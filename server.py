"""
Запускаемый сервер Telegram бота

"""
from typing import Callable

from aiogram import Bot, Dispatcher, executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery

import messages as msgs
from middlewares import AccessMiddleware
from settings import LOG, ACCESS_IDS, TELEGRAM_API_TOKEN, DEBUG_MODE

from database.db_manager import db_manager

from datetime import datetime

import json

import asyncio

# FIXME: wrong decoration of async funcs, use asyncref?
def log_errors(func: Callable) -> Callable:
    def decorator(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            LOG.error(e, exc_info=DEBUG_MODE)
    return decorator


bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(AccessMiddleware(ACCESS_IDS))

db = db_manager()



stop_sending = asyncio.Event()
lock = asyncio.Lock()
interval = 15

async def get_interval():
    await lock.acquire()
    try:
        return interval
    finally:
        lock.release()

async def set_interval(new_interval):
    await lock.acquire()
    try:
        interval = new_interval
    finally:
        lock.release()

async def repeat(func, *args, **kwargs):
    """Run func every interval seconds.

    If func has not finished before *interval*, will run again
    immediately when the previous iteration finished.

    *args and **kwargs are passed as the arguments to func.
    """
    while not stop_sending.is_set():
        await asyncio.gather(
            func(*args, **kwargs),
            asyncio.sleep(await get_interval()),
        )


@log_errors
@dp.message_handler(commands=('help'))
async def send_welcome(message: Message):
    await message.answer(msgs.welcome)

@log_errors
@dp.message_handler(commands=('start'))
async def send_start(message: Message):
    if message.get_command(pure=True) == 'start':
        LOG.info('User: ' + message.from_user.get_mention())

    user = message.from_user
    now = datetime.now()
    db.try_add_user(user, now)

    started = db.try_start_session(user.id, now)

    reply = 'Стартуем'
    if started == False:
        reply = 'Уже стартовали'

    await message.answer(reply)

    if started == True:
        stop_sending.clear()
        await repeat(periodic, user.id)


@dp.message_handler(commands=('stop'))
async def send_stop(message: Message):
    user = message.from_user
    now = datetime.now()

    stopped = db.try_stop_session(user.id, now)

    reply = 'Остановились'
    if stopped == False:
        reply = 'Нечего останавливать'

    await message.answer(reply)

    if stopped == True:
        stop_sending.set()

@log_errors
@dp.message_handler(commands=('list'))
async def send_list(message: Message):
    """Send "welcome" and info about bot usage to user"""
    msg = db.list_categories()
    await message.answer(msg)

@log_errors
@dp.message_handler(commands=('int'))
async def send_set_interval(message: Message):
    """Send "welcome" and info about bot usage to user"""
    new_interval = await get_interval() + 5
    await set_interval(new_interval)
    await message.answer("Интервал установлен в " + str(new_interval) + " секунд")

@log_errors
@dp.message_handler(commands=('commands'))
async def send_set_interval(message: Message):

    start_btn = InlineKeyboardButton('Старт', callback_data="cmd_start")
    stop_btn = InlineKeyboardButton('Стоп', callback_data="cmd_stop")
    report_btn = InlineKeyboardButton('Отчет', callback_data="cmd_report")
    interval_btn = InlineKeyboardButton('Сменить интервал', callback_data="cmd_interval")

    buttons = InlineKeyboardMarkup() \
        .row(start_btn, stop_btn) \
        .row(report_btn, interval_btn)

    await message.answer("Полезные команды:", reply_markup=buttons)

async def periodic(*args):
    date_now = datetime.now()
    date = str(date_now.strftime("%Y-%m-%d %H:%M:%S"))
    data = {'name':'','date':date}

    data['name'] = 'Работа'
    work_btn = InlineKeyboardButton('Работа', callback_data=json.dumps(data, ensure_ascii=False))

    data['name'] = 'TimeKiller'
    time_killer_btn = InlineKeyboardButton('TimeKiller', callback_data=json.dumps(data, ensure_ascii=False))

    data['name'] = 'Еда'
    food_btn = InlineKeyboardButton('Еда', callback_data=json.dumps(data, ensure_ascii=False))

    data['name'] = 'Гулять'
    walk_btn = InlineKeyboardButton('Гулять', callback_data=json.dumps(data, ensure_ascii=False))

    data['name'] = 'Тренировка'
    workout_btn = InlineKeyboardButton('Тренировка', callback_data=json.dumps(data, ensure_ascii=False))

    data['name'] = 'Сон'
    sleep_btn = InlineKeyboardButton('Сон', callback_data=json.dumps(data, ensure_ascii=False))

    buttons = InlineKeyboardMarkup()\
        .row(work_btn, time_killer_btn, food_btn)\
        .row(walk_btn, workout_btn, sleep_btn)

    db.start_event(args[0], date)

    await bot.send_message(args[0], f'{date_now.strftime("%m-%d %H:%M:%S")}. Что делал последние: {await get_interval()} секунд', reply_markup=buttons)

@dp.callback_query_handler(lambda c: 'name' in c.data and 'date' in c.data)
async def process_callback_button1(callback_query: CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    data = json.loads(callback_query.data)
    stopped = db.try_stop_event(callback_query.from_user.id, data['name'], data['date'])

    reply = data['date'] + ' - Заполнено. ' + data['name']
    if not stopped:
        reply = 'Промежуток уже был заполнен'

    await bot.send_message(callback_query.from_user.id, reply)

@dp.callback_query_handler(lambda c: c.data.startswith('cmd'))
async def process_callback_button1(callback_query: CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    if callback_query.data == 'cmd_start':
        await send_start(callback_query.message)
    if callback_query.data == 'cmd_stop':
        await send_start(callback_query.message)
    else:
        await bot.send_message(callback_query.from_user.id, "Не реализовано")

if __name__ == '__main__':
    db.migrate()
    executor.start_polling(dp, skip_updates=True)

