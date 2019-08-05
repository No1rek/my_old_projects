import time


class CachedMem:
    def __init__(self, inmemory_time, timedelta=0):
        self.list = []
        self.inmemory_time = int(inmemory_time)
        self.timedelta = timedelta

    #Основной поток
    def run(self, execute_step, vars):
        settings = vars['settings']
        while True:
            # Проверка на напоминание
            usrs_to_remind = self.remove_obsolete_users(rm=False, inmemory_time=settings['time_wait_remind'])
            # Напоминалку можно лучше расписать
            for usr in usrs_to_remind:
                if usr['obsolete'] == 1:
                    self.list[self.search_by_id(usr['id'])]['step'] = 'allfortoday'
                    self.list[self.search_by_id(usr['id'])]['obsolete'] = 0
                    vars['vk'].group.method(
                        'messages.send',
                        {'user_id': usr['id'],
                         'message': vars['SC'].find_step_by_name('allfortoday')['ask']}
                    )
                    execute_step(vars['vk'], vars['SC'], None, vars['SC'].find_step_by_name('allfortoday'), usr,
                                 settings)

            self.remove_obsolete_users()
            time.sleep(settings['memory_sleep_time'])

    #Для поиска бзера в списке
    def search_by_id(self, ident):
        increment = 0
        for user in self.list:
            if user['id'] == str(ident):
                return increment
            increment += 1
        else:
            return False

    def append_user(self, ident, step='greetings'):
        curr_time = time.time()
        self.list.append(
            {'id': str(ident), 'time': int(curr_time), 'step': str(step), 'names': [], 'obsolete': 0}
        )

    def clear_request(self, ident):
        index = self.search_by_id(ident)
        self.list[index]['names'] = ""

    def remove_user(self, ident):
        del self.list[self.search_by_id(ident)]

    # Удаление устаревших пользователей из памяти
    def remove_obsolete_users(self, rm=True, inmemory_time=False):
        if not inmemory_time:
            inmemory_time = self.inmemory_time
        curr_time = time.time() - self.timedelta
        increment = 0
        for user in self.list:
            if user['time'] < curr_time - inmemory_time:
                increment += 1
            else:
                break
        ret = list(self.list[:increment])
        if rm == True:
            self.list = list(self.list[increment:])
        return ret
