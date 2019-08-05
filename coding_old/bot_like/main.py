from threading import Thread

import vk_api
from vk_api import *
from vk_api.longpoll import VkLongPoll, VkEventType

from data_processing import CachedMem
from scenario_funcs import *
from settings import return_settings



class session():
    def init_group_session(self, token):
        self.group = vk_api.VkApi(token=token)

    def init_app_session(self, token):
        self.app = vk_api.VkApi(token=token)

# Функция для отправки сообщения
def write_msg(vk, user_id, s):
    if len(s) > 0:
        vk.group.method('messages.send', {'user_id': user_id, 'message': s})


def execute_step(vk, SC, msg, step, user, settings):
    if len(step['function']) > 0:
        user = SC.functions[step['function']](locals())

    else:
        if len(step['text_before']) > 0:
            write_msg(vk, user['id'], step['text_before'])

        user['step'] = step['next']
        user['time'] = msg['date']

        if len(step['text_after']) > 0:
            write_msg(vk, user['id'], step['text_after'])
        return user

def main():
    # Импортируем настройки из файла settings
    settings = return_settings()
    # Инициализация vk Api для группы и для приложения
    vk = session()
    vk.init_app_session(token=settings['token_app'])
    vk.init_group_session(token=settings['token_group'])
    longpoll = VkLongPoll(vk.group)

    # Инициализируем кэш-память, БД, сценарий
    CM = CachedMem(settings['time_wait_clear_cache'])
    SC = Scenario(settings['scenario_file'])
    Thread(target=CM.run, args=[execute_step, locals()]).start()

    # Подключаем лонгполл
    for event in longpoll.listen():
        # Получаем непрочитанные сообщения
        if event.type == VkEventType.MESSAGE_NEW and event.to_me and (event.flags == 17 or event.flags == 1):

            msg = {'body': event.text, 'user_id': event.user_id, 'date': time.time()}
            user_id = event.user_id
            user_id_local = CM.search_by_id(user_id)

            # Проверить есть ли уже у пользователя диалог с ботом
            if not (user_id_local is False):
                stepname = CM.list[user_id_local]['step']
                ret = execute_step(vk, SC, msg, SC.find_step_by_name(stepname), CM.list[user_id_local], settings)
                if not ret is None:
                    CM.list[user_id_local] = ret
            else:
                CM.append_user(user_id)
                user_id_local = CM.search_by_id(user_id)
                execute_step(vk, SC, msg, SC.find_step_by_name('greetings'), CM.list[user_id_local], settings)


if __name__ == '__main__':
    main()
