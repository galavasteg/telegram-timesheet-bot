base_cmds = {
    'help': 'вывести это сообщение',
}
category_cmds = {
    # TODO: DELETE or not DELETE category
    'list': 'список текущих категорий',
    'add': ('добавить категорию. Ввести название новой категории,'
            ' например: "Проект X". При следующем ответе боту'
            ' будет доступна кнопка "ПРОЕКТ X"'),
    'turn_off': ('исключить категорию из списка текущих.'
                 ' Выбрать исключаемую категорию. Нельзя исключать'
                 ' категории по умолчанию'),
    'list_all': 'список всех категорий. Список категорий, включая вычеркнутые',
    'turn_on': 'включить категорию в список текущих. Выбрать исключенную категорию',
}
stat_cmds = {
    'day': 'за текущий день',
    'week': 'за текущую неделю',
    'month': 'за текущий месяц',
}

# TODO: actualize descr
description = ('Бот для учёта времени.\n\n'

               'Отвечайте на сообщения бота в течение 5 минут.'
               ' Если оставить бота без ответа, то за указанный период'
               ' будет установлена предыдущая активность.')
base_cmds_s = '\n'.join(f'/{name} - {descr}' for name, descr
                        in base_cmds.items())
category_cmds_s = '\n'.join(f'/{name} - {descr}' for name, descr
                            in category_cmds.items())
stat_cmds_s = '\n'.join(f'/{name} - {descr}' for name, descr
                        in stat_cmds.items())


class MSGS:
    welcome = (
        f'{description}\n\n'
        
        'КОМАНДЫ\n'
        f'{base_cmds_s}\n\n'
        
        f'{category_cmds_s}\n\n'
        
        f'Статистика:\n'
        f'{stat_cmds_s}'
    )


# Ugly? Guido recommends this himself ...
# http://mail.python.org/pipermail/python-ideas/2012-May/014969.html
import sys  # noqa

messages = MSGS()
messages.__name__ = __name__
sys.modules[__name__] = messages
