from aiogram import types


DEFAULT_INTERVAL_SECONDS = 60 * 15
MAX_ROW_BUTTONS = 3

CHOOSE_INTERVAL_TEXT = 'Выбери интервал'
INTERVAL_BUTTONS = (
    types.InlineKeyboardButton('15 минут', callback_data=str(60 * 15)),
    types.InlineKeyboardButton('20 минут', callback_data=str(60 * 20)),
    types.InlineKeyboardButton('30 минут', callback_data=str(60 * 30)),
)
DEBUG_BUTTONS = (
    types.InlineKeyboardButton('5 секунд (тест)', callback_data=str(5)),
    types.InlineKeyboardButton('10 секунд (тест)', callback_data=str(10)),
    types.InlineKeyboardButton('30 секунд (тест)', callback_data=str(30)),
)

CHOOSE_STATS_TEXT = 'Статистика за какой период?'
STATS_BUTTONS = (
    # types.InlineKeyboardButton('За последнюю сессию', callback_data='session'),
    types.InlineKeyboardButton('За день', callback_data='1'),
    types.InlineKeyboardButton('За неделю', callback_data='7'),
    types.InlineKeyboardButton('За месяц', callback_data='31'),
    # types.InlineKeyboardButton('За текущий месяц', callback_data='7'),
    # types.InlineKeyboardButton('За текущую неделю', callback_data='31'),
)
