"""
Запускаемый сервер Telegram бота

"""
from typing import Callable

from aiogram import Bot, Dispatcher, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, \
    InlineKeyboardMarkup, Message, CallbackQuery, ContentTypes

import messages as msgs
from middlewares import AccessMiddleware
from settings import LOG, ACCESS_IDS, TELEGRAM_API_TOKEN, DEBUG_MODE

from database.db_manager import DBManager

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

db = DBManager()



stop_sending = asyncio.Event()
lock = asyncio.Lock()
interval = 15

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
        (fetched, step) = await get_interval(user_id)

        if fetched:
            await asyncio.gather(
                func(*args, **kwargs),
                asyncio.sleep(step),
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
    await start_routine(message)


async def start_routine(message: Message):
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
    await stop_routine(message)


async def stop_routine(message: Message):
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
@dp.message_handler(commands=('buttons'))
async def send_list(message: Message):

    btn_start = KeyboardButton('Старт')
    btn_stop = KeyboardButton('Стоп')
    btn_change_step = KeyboardButton('Сменить интервал')
    btn_report = KeyboardButton('Отчет')

    navigation_kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    navigation_kb.row(btn_start, btn_stop).row(btn_change_step, btn_report)

    await message.reply("Отображаем кнопки", reply_markup=navigation_kb)



@log_errors
@dp.message_handler(commands=('step'))
async def send_set_step(message: Message):
    await set_step_routine(message)


async def set_step_routine(message: Message):
    btn_10_minutes = InlineKeyboardButton('15 минут', callback_data='step_15')
    btn_20_minutes = InlineKeyboardButton('20 минут', callback_data='step_20')
    btn_30_minutes = InlineKeyboardButton('30 минут', callback_data='step_30')

    btn_5_second = InlineKeyboardButton('5 секунд (тест)', callback_data='step_5_s')
    btn_10_seconds = InlineKeyboardButton('10 секунд (тест)', callback_data='step_10_s')
    btn_30_seconds = InlineKeyboardButton('30 секунд (тест)', callback_data='step_30_s')

    buttons = InlineKeyboardMarkup() \
        .row(btn_10_minutes, btn_20_minutes, btn_30_minutes) \
        .row(btn_5_second, btn_10_seconds, btn_30_seconds)

    await bot.send_message(message.from_user.id,
                           'Выбери интервал',
                           reply_markup=buttons)


@dp.message_handler(content_types=ContentTypes.ANY)
async def all_other_messages(message: Message):
    if message.text == 'Старт':
        await start_routine(message)
    elif message.text == 'Стоп':
        await stop_routine(message)
    elif message.text == 'Сменить интервал':
        await set_step_routine(message)
    elif message.text == 'Отчет':
        await message.answer('Отчета пока нет')


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

    user_id = args[0]
    db.start_event(user_id, date)

    (fetched, step) = await get_interval(user_id)
    if fetched:
        await bot.send_message(user_id, f'{date_now.strftime("%m-%d %H:%M:%S")}. Что делал последние: {step} секунд', reply_markup=buttons)
    else:
        await bot.send_message(user_id, 'Ошибка получения интервала')

@dp.callback_query_handler(lambda c: 'name' in c.data and 'date' in c.data)
async def process_callback_button1(callback_query: CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    data = json.loads(callback_query.data)
    stopped = db.try_stop_event(callback_query.from_user.id, data['name'], data['date'])

    reply = data['date'] + ' - Заполнено. ' + data['name']
    if not stopped:
        reply = 'Промежуток уже был заполнен'

    await bot.send_message(callback_query.from_user.id, reply)


@dp.callback_query_handler(lambda c: 'step' in c.data)
async def process_callback_button1(callback_query: CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    cmd = callback_query.data
    error_msg = 'Нет активной сессии, в которой можно сменить интервал'
    reply = 'Интервал установлен в '

    if cmd == 'step_15':
        result = db.try_set_step(callback_query.from_user.id, 15 * 60)
        if result == True:
            reply += '15 минут'
        else:
            reply = error_msg
    elif cmd == 'step_20':
        result = db.try_set_step(callback_query.from_user.id, 20 * 60)
        if result == True:
            reply += '20 минут'
        else:
            reply = error_msg
    elif cmd == 'step_30':
        result = db.try_set_step(callback_query.from_user.id, 30 * 60)
        if result == True:
            reply += '30 минут'
        else:
            reply = error_msg
    elif cmd == 'step_5_s':
        result = db.try_set_step(callback_query.from_user.id, 5)
        if result == True:
            reply += '5 секунд'
        else:
            reply = error_msg
    elif cmd == 'step_10_s':
        result = db.try_set_step(callback_query.from_user.id, 10)
        if result == True:
            reply += '10 секунд'
        else:
            reply = error_msg
    elif cmd == 'step_30_s':
        result = db.try_set_step(callback_query.from_user.id, 30)
        if result == True:
            reply += '30 секунд'
        else:
            reply = error_msg
    await bot.send_message(callback_query.from_user.id, reply)

if __name__ == '__main__':
    db.migrate()
    executor.start_polling(dp, skip_updates=True)

