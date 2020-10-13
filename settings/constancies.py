from aiogram import types


DEFAULT_INTERVAL_SECONDS = 60 * 15
MAX_ROW_BUTTONS = 3

START_SESSION_BEFOREHAND = 'Сперва стартуй сессию'
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
STATS_BUTTONS = types.InlineKeyboardMarkup().row(
    types.InlineKeyboardButton('За день', callback_data='{"days": 1}'),
    types.InlineKeyboardButton('За неделю', callback_data='{"weeks": 1}'),
    types.InlineKeyboardButton('За месяц', callback_data='{"months": 1}'),
).row(
    types.InlineKeyboardButton('За последнюю сессию', callback_data='session'),
#     TODO:
#     types.InlineKeyboardButton('За текущий день', callback_data='???'),
# ).row(
#     types.InlineKeyboardButton('За текущий месяц', callback_data='???'),
#     types.InlineKeyboardButton('За текущую неделю', callback_data='???'),
)
