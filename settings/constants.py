from aiogram import types

DEFAULT_CATEGORIES = 'Работа', 'TimeKiller', 'Еда', 'Прогулка', 'Тренировка', 'Сон',

WAIT_INTERVAL_FROM_USER_BEFORE_START = 10

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
    types.InlineKeyboardButton('За 24 часа', callback_data='{"days": 1}'),
    types.InlineKeyboardButton('За 7 суток', callback_data='{"weeks": 1}'),
    types.InlineKeyboardButton('За 1 месяц', callback_data='{"months": 1}'),
).row(
    types.InlineKeyboardButton('За последнюю сессию', callback_data='session'),
#     TODO:
#     types.InlineKeyboardButton('За текущий день', callback_data='???'),
# ).row(
#     types.InlineKeyboardButton('За текущий месяц', callback_data='???'),
#     types.InlineKeyboardButton('За текущую неделю', callback_data='???'),
)
