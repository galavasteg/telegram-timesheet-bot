from typing import Dict

_base_cmds = {
    'help': 'вывести это сообщение',
    'list': 'список текущих категорий',
    'buttons': 'вывести кнопки управления ботом',
    # TODO: DELETE or not DELETE category
    # 'add': ('добавить категорию. Ввести название новой категории,'
    #         ' например: "Проект X". При следующем ответе боту'
    #         ' будет доступна кнопка "ПРОЕКТ X"'),
    # 'turn_off': ('исключить категорию из списка текущих.'
    #              ' Выбрать исключаемую категорию. Нельзя исключать'
    #              ' категории по умолчанию'),
    # 'list_all': 'список всех категорий. Список категорий, включая вычеркнутые',
    # 'turn_on': 'включить категорию в список текущих. Выбрать исключенную категорию',
}
# _stat_cmds = {
#     'day': 'за текущий день',
#     'week': 'за текущую неделю',
#     'month': 'за текущий месяц',
# }


def _represent_commands(cmd_description_map: Dict[str, str]) -> str:
    cmds_description = '\n'.join(
        f'/{name} - {descr}' for name, descr in cmd_description_map.items())
    return cmds_description

_base_cmds_s = _represent_commands(_base_cmds)
# _category_cmds_s = '\n'.join(f'/{name} - {descr}' for name, descr
#                              in _category_cmds.items())
# _stat_cmds_s = '\n'.join(f'/{name} - {descr}' for name, descr
#                          in _stat_cmds.items())


WELCOME = (
    f'Бот для учёта времени.\n\n'
    
    f'Чтобы начать нажмите: /start'
    
    'ПРОЧИЕ КОМАНДЫ\n'
    f'{_base_cmds_s}\n\n'
)
