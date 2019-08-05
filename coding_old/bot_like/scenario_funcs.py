import datetime
import json
import re
import time


class Scenario:
    def __init__(self, scenario_file):
        with open(scenario_file, 'r', encoding='utf-8') as scenario:
            self.steps = json.loads(scenario.read())['steps']
            self.functions = self.FUNC_STEP_RELATION_TABLE()

    #Служит для связи логики и вьюхи
    def find_step_by_name(self, name):
        for step in self.steps:
            if step['name'] == name:
                return step
        else:
            return False

    def FUNC_STEP_RELATION_TABLE(self):
        return {
            "start": start,
            "get_name": get_name,
            "get_date": get_date,
            "all_for_today": all_for_today
        }


def use_regexp(exp, text):
    pattern = re.sub(r"\\\\\\\\", '\\\\', exp)
    matches = re.findall(pattern, text)
    return matches

# Проверка ключевого слова, чтобы избежать повтора
def template_f(kw, nextstep=True):
    matches = use_regexp(kw['step']['regexp'], kw['msg']['body'])
    if len(matches) > 0:
        if nextstep:
            kw['user']['step'] = kw['step']['next']
            kw['user']['time'] = kw['msg']['date']
        return kw['user']
    else:
        kw['vk'].group.method(
            'messages.send',
            {'user_id': kw['user']['id'],
             'message': kw['step']['error']}
        )
        return None

# Переход на след шаг, чтобы избежать повтореня хода
def wrapper(f):
    def decorated(kw):
        user = kw['user']
        step = kw['step']
        msg = kw['msg']
        if len(step['text_before']) > 0:
            kw['vk'].group.method('messages.send',
                                  {'user_id': user['id'], 'message': step['text_before']}
                                  )
        try:
            ret = f(kw)
        except:
            ret = None

        if ret is not None:
            user = ret
            user['time'] = msg['date']
            user['step'] = step['next']

            if len(step['text_after']) > 0:
                kw['vk'].group.method('messages.send',
                                      {'user_id': user['id'], 'message': step['text_after']}
                                      )
        else:
            try:
                user['time'] = msg['date']
            except:
                user['time'] = time.time()
        return user

    return decorated


@wrapper
def start(kw):
    return template_f(kw)

# Получает, сохраняет имя для поиска
@wrapper
def get_name(kw):
    user = template_f(kw, nextstep=False)
    if user is None:
        return None

    user['names'] = use_regexp(r'\w+', kw['msg']['body'])
    user['names'] = list([el for el in user['names']][:2])

    if len(user['names']) == 0:
        user['step'] = kw['step']['name']
        kw['vk'].group.method(
            'messages.send',
            {'user_id': kw['user']['id'],
             'message': kw['step']['error']}  # Тут можно сделать другую ошибку
        )
    else:
        user['step'] = kw['step']['next']
    return user

# Свой врапер для фукции поиска лайков
def get_date(kw):
    try:
        ret = get_date_contents(kw)
    except:
        kw['vk'].group.method(
            'messages.send',
            {'user_id': kw['user']['id'],
             'message': kw['step']['error']}
        )
        ret = None

    if not (ret is None):
        ret['obsolete'] = 1
        return ret
    else:
        kw['user']['obsolete'] = 1
        return kw['user']

# Поиск лайков
# Ищем дату в сообщении, перебираем стену, сверяем име, фамилию
def get_date_contents(kw):
    user = kw['user']
    kw['user']['time'] = kw['msg']['date']
    ret = template_f(kw, nextstep=False)
    if ret is None:
        return user
    settings = kw['settings']
    vk = kw['vk']

    if len(kw['step']['text_before']) > 0:
        kw['vk'].group.method('messages.send',
                              {'user_id': user['id'], 'message': kw['step']['text_before']}
                              )

    dates = re.findall(r'\d+.\d+.\d+', kw['msg']['body'])

    convert_date = lambda x: time.mktime(
        datetime.datetime.strptime(x, '%d.%m.%y').timetuple()
    )
    date1 = convert_date(dates[0])
    if len(dates) > 1:
        date2 = convert_date(dates[1]) + 86400
    else:
        # Прибавляем один день
        date2 = date1 + 86400

    friend = {'first_name': user['names'][0], 'last_name': "", 'likes': []}
    if len(user['names']) > 1:
        friend['last_name'] = user['names'][1]

    posts = vk.app.method('wall.get', {'owner_id': settings['group_id'], 'filter': 'owner'})['items']

    # Здесь можно оптимизировать поиск: искать не перебором, а, алгоритмом быстрого поиска
    for post in posts:
        if post['date'] > date1 and post['date'] < date2:
            likes = vk.app.method('likes.getList', {'type': 'post',
                                                    'owner_id': settings['group_id'],
                                                    'item_id': post['id'],
                                                    'extended': 1})['items']
            for like in likes:
                like['first_name'] = like['first_name'].lower()
                like['last_name'] = like['last_name'].lower()
                if (like['first_name'] == friend['first_name'].lower() or like['last_name'] == friend[
                    'first_name'].lower()) \
                        and (like['last_name'] == friend['last_name'].lower() or friend['last_name'] == ""):
                    link = settings['post_link_template'] \
                           % {'wall_id': str(settings['group_id']),
                              'post_id': str(post['id'])}
                    friend['likes'].append(link)
                    break

    if len(friend['likes']) == 0:
        kw['vk'].group.method(
            'messages.send',
            {'user_id': kw['user']['id'],
             'message': kw['step']['search_error']})  # Тут можно сделать другую ошибку
        user['step'] = "getname"

    else:
        vk.group.method('messages.send', {'user_id': user['id'], 'message': print_links(friend)})

        user['step'] = kw['step']['next']
        user['names'] = []
        user['time'] = kw['msg']['date']

    user['obsolete'] = 1

    if len(kw['step']['text_after']) > 0:
        kw['vk'].group.method('messages.send',
                              {'user_id': user['id'], 'message': kw['step']['text_after']}
                              )
    return user


# Функция вывода списка ссылок
def print_links(friend):
    msg = ""
    msg = msg + " ".join([friend['first_name'], friend['last_name']]) + ':\n'
    for link in friend['likes']:
        msg = msg + '    ' + link + '\n'
    return msg.encode('utf-8')

# Сверяет ответ да или нет на вопрос все ли на сегодня
@wrapper
def all_for_today(kw):
    user = kw['user']
    matches = use_regexp(kw['step']['regexp'],
                         kw['msg']['body'])
    if len(matches) < 1:
        kw['vk'].group.method(
            'messages.send',
            {'user_id': kw['user']['id'],
             'message': kw['step']['error']}
        )
    elif matches[0] == 'да':
        kw['vk'].group.method(
            'messages.send',
            {'user_id': kw['user']['id'],
             'message': kw['step']['yes']}
        )
        user['obsolete'] = 0
        return user
    elif matches[0] == 'нет':
        kw['vk'].group.method(
            'messages.send',
            {'user_id': kw['user']['id'],
             'message': kw['step']['no']}
        )
        user['obsolete'] = 0
        user['time'] = 0  # Это удалит юзера на следующем цикле как устаревшую сессию
        return user
