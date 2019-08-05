def return_settings():
    return {
        'token_group': 'cea381b07db415480a69826b703c920170d3b8534410b611790987b44af3ceb8d2ae85dd8dd879344cd08',
        'token_app': '2dce6b932dce6b932dce6b93072daf276422dce2dce6b937746107ab8e34133e156cdb9',
        'group_id': -162118980, #id группы
        'scenario_file': 'scenario_view.json',
        'messages_per_request': 100,  # Количество сообщений, которые программа запрашивает за раз
        'time_wait_remind': 1800, #Время в секундах через которое нужно спросить пользователя хочет ли он задавать вопросы еще
        'time_wait_clear_cache': 96000, #Время до удаления пользователя из кеша
        'post_link_template': 'vk.com/wall%(wall_id)s_%(post_id)s',  # Шаблон для ссылки
        'memory_sleep_time': 1 # Время прохождения итерации в потоке кеш памяти

    }
