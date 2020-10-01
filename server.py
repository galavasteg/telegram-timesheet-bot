"""
Запускаемый сервер Telegram бота

"""
import json
import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, executor
from aiogram import types

import settings
import messages as msgs
from database.db_manager import DBManager
from middlewares import AccessMiddleware


LOG = settings.LOG

db = DBManager()

bot = Bot(token=settings.TELEGRAM_API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(AccessMiddleware(settings.ACCESS_IDS))

stop_sending = asyncio.Event()
lock = asyncio.Lock()

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

async def get_interval(user_id):
    await lock.acquire()
    try:
        return db.try_get_step(user_id)
    finally:
        lock.release()


async def set_interval(user_id, new_step):
    await lock.acquire()
    try:
        db.try_set_step(user_id, new_step)
    finally:
        lock.release()


async def repeat(func, *args, **kwargs):
    """Run func every interval seconds.

    If func has not finished before *interval*, will run again
    immediately when the previous iteration finished.

    *args and **kwargs are passed as the arguments to func.
    """
    while not stop_sending.is_set():
        user_id = args[0]
        fetched, step = await get_interval(user_id)

        if fetched:
            await asyncio.gather(
                func(*args, **kwargs),
                asyncio.sleep(step),
        )


@dp.message_handler(commands=('help',))
async def send_welcome(message: types.Message):
    await message.answer(msgs.welcome)


@dp.message_handler(commands=('start',))
async def send_start(message: types.Message):
    msg = 'Opened session. User: ' + message.from_user.get_mention()
    LOG.info(msg)
    await start_routine(message)


async def start_routine(message: types.Message):
    user = message.from_user
    now = datetime.now()
    db.try_register_user(user)

    started = db.try_start_session(user.id, now)

    reply = 'Стартуем' if started is False else 'Уже стартовали'
    await message.answer(reply)

    if started is True:
        stop_sending.clear()
        await repeat(periodic, user.id)


@dp.message_handler(commands=('stop',))
async def send_stop(message: types.Message):
    await stop_routine(message)
    msg = 'Closed session. User: ' + message.from_user.get_mention()
    LOG.info(msg)


async def stop_routine(message: types.Message):
    user = message.from_user
    now = datetime.now()

    stopped = db.try_stop_session(user.id, now)
    reply = 'Остановились' if stopped else 'Нечего останавливать'

    await message.answer(reply)

    if stopped:
        stop_sending.set()


@dp.message_handler(commands=('list',))
async def send_list(message: types.Message):
    msg = db.list_categories()
    await message.answer(msg)


@dp.message_handler(commands=('buttons',))
async def send_list(message: types.Message):
    btn_start = types.KeyboardButton('Старт')
    btn_stop = types.KeyboardButton('Стоп')
    btn_change_step = types.KeyboardButton('Сменить интервал')
    btn_statistic = types.KeyboardButton('Отчет')

    navigation_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    navigation_kb.row(btn_start, btn_stop).row(btn_change_step, btn_statistic)

    await message.reply("Отображаем кнопки", reply_markup=navigation_kb)


@dp.message_handler(commands=('step',))
async def send_set_step(message: types.Message):
    await set_step_routine(message)


async def set_step_routine(message: types.Message):
    buttons = types.InlineKeyboardMarkup().row(*INTERVAL_BUTTONS)
    if settings.DEBUG_MODE:
        buttons.row(*DEBUG_BUTTONS)

    await bot.send_message(message.from_user.id,
                           CHOOSE_INTERVAL_TEXT,
                           reply_markup=buttons)


BTNNAME_HANDLER_MAP = {
    'Старт': start_routine,
    'Стоп': stop_routine,
    'Сменить интервал': set_step_routine,
    # TODO: implement reports
    # 'Статистика >>': start_routine,
}


@dp.message_handler(content_types=types.ContentTypes.ANY)
async def reply_admin_btns(message: types.Message):
    btn_name = message.text

    if btn_name not in BTNNAME_HANDLER_MAP:
        await message.answer(f'`{btn_name}` не реализован')
    else:

        handler = BTNNAME_HANDLER_MAP[btn_name]
        await handler(message)


async def periodic(*args):
    date_now = datetime.now()
    date = str(date_now.strftime("%Y-%m-%d %H:%M:%S"))
    data = {'name': '', 'date': date}

    data['name'] = 'Работа'
    work_btn = types.InlineKeyboardButton('Работа', callback_data=json.dumps(data, ensure_ascii=False))

    data['name'] = 'TimeKiller'
    time_killer_btn = types.InlineKeyboardButton('TimeKiller', callback_data=json.dumps(data, ensure_ascii=False))

    data['name'] = 'Еда'
    food_btn = types.InlineKeyboardButton('Еда', callback_data=json.dumps(data, ensure_ascii=False))

    data['name'] = 'Гулять'
    walk_btn = types.InlineKeyboardButton('Гулять', callback_data=json.dumps(data, ensure_ascii=False))

    data['name'] = 'Тренировка'
    workout_btn = types.InlineKeyboardButton('Тренировка', callback_data=json.dumps(data, ensure_ascii=False))

    data['name'] = 'Сон'
    sleep_btn = types.InlineKeyboardButton('Сон', callback_data=json.dumps(data, ensure_ascii=False))

    buttons = types.InlineKeyboardMarkup()\
        .row(work_btn, time_killer_btn, food_btn)\
        .row(walk_btn, workout_btn, sleep_btn)

    user_id = args[0]
    db.start_event(user_id, date)

    (fetched, step) = await get_interval(user_id)
    if fetched:
        await bot.send_message(user_id, f'{date_now.strftime("%m-%d %H:%M:%S")}. Что делал последние: {step} секунд', reply_markup=buttons)
    else:
        await bot.send_message(user_id, 'Ошибка получения интервала')


@dp.callback_query_handler(lambda c: 'name' in c.data and 'date' in c.data)
async def process_callback_button1(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    data = json.loads(callback_query.data)
    user_id = callback_query.from_user.id

    stopped = db.try_stop_event(user_id, data['name'], data['date'])
    if stopped:
        reply = f'{data["date"]} - Заполнено. {data["name"]}'
    else:
        reply = 'Промежуток уже был заполнен'

    await bot.send_message(user_id, reply)


@dp.callback_query_handler(lambda c: c.message.text == CHOOSE_INTERVAL_TEXT)
async def process_callback_button1(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    interval_seconds = int(callback_query.data)
    # TODO: seconds to minutes (via datetime?)
    interval_representation = f'{interval_seconds} секунд'

    is_set = db.try_set_step(callback_query.from_user.id, interval_seconds)

    if is_set:
        reply = 'Интервал изменен: {}'.format(interval_representation)
    else:
        reply = 'Интервал тот же: {}'.format(interval_representation)
    await bot.send_message(callback_query.from_user.id, reply)


if __name__ == '__main__':
    db.migrate()
    executor.start_polling(dp, skip_updates=True)
