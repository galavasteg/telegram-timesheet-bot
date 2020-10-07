"""
Запускаемый сервер Telegram бота

"""
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Union, Tuple

from aiogram import Bot, Dispatcher, executor
from aiogram import types
import more_itertools

import settings
import messages as msgs
import settings.constancies as const
from database.db_manager import DBManager, DoesNotExist
from middlewares import AccessMiddleware


LOG = settings.LOG

db = DBManager()

bot = Bot(token=settings.TELEGRAM_API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(AccessMiddleware(settings.ACCESS_IDS))

# TODO: event for different user
stop_sending_events = {} #asyncio.Event()
locks = {} #asyncio.Lock()


async def get_interval(u: types.User):
    await locks[u.id].acquire()
    try:
        interval_seconds = db.get_interval_seconds(u)
        return interval_seconds
    finally:
        locks[u.id].release()


async def set_interval(u: types.User, interval_seconds):
    await locks[u.id].acquire()
    try:
        return db.set_interval_seconds(u, interval_seconds)
    finally:
        locks[u.id].release()


# TODO: message actualize
@dp.message_handler(commands=('help',))
async def send_welcome(message: types.Message):
    await message.answer("Hello")#msgs.welcome)


@dp.message_handler(commands=('start',))
async def start_session(message: types.Message):
    user = message.from_user
    db.register_user_if_not_exists(user)

    session_id, is_new_session = db.get_new_or_existing_session_id(user)

    if not is_new_session:
        # TODO: all message tmpls to constants
        await message.answer('Обнаружена незавершенная сессия.'
                             ' Закройте ее ("Стоп") и начните новую ("Старт")')
        return

    stop_sending_events[user.id] = asyncio.Event()
    locks[user.id] = asyncio.Lock()

    stop_sending_events[user.id].clear()
    interval_seconds = await get_interval(user)
    # TODO: seconds to minutes (via datetime?)
    first_bot_msg_time = datetime.now() + timedelta(0, interval_seconds)
    reply = f'Бот пришлет первое сообщение в {first_bot_msg_time.strftime("%H:%M")}.'
    await message.answer(reply)

    LOG.info('Opened session. User: ' + user.get_mention())
    while not stop_sending_events[user.id].is_set():
        interval_seconds = await get_interval(user)
        await asyncio.sleep(interval_seconds)
        await send_choose_categories(user, session_id, interval_seconds)


@dp.message_handler(commands=('stop',))
async def stop_session(message: types.Message):
    user = message.from_user

    stopped = db.try_stop_session(user)
    reply = 'Остановились' if stopped else 'Нечего останавливать'

    await message.answer(reply)

    if stopped:
        stop_sending_events[user.id].set()
        msg = 'Closed session. User: ' + message.from_user.get_mention()
        LOG.info(msg)


@dp.message_handler(commands=('list',))
async def list_categories_cmd(message: types.Message):
    user = message.from_user
    categories = db.list_categories(user)
    msg = 'Категории:\n\n{}'.format(
            '\n'.join(name for _, name in categories))
    await message.answer(msg)


@dp.message_handler(commands=('buttons',))
async def control_buttons_cmd(message: types.Message):
    user = message.from_user

    btn_start = types.KeyboardButton('Старт')
    btn_stop = types.KeyboardButton('Стоп')
    btn_change_step = types.KeyboardButton('Изменить интервал')
    btn_statistic = types.KeyboardButton('Статистика>>')

    navigation_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    navigation_kb.row(btn_start, btn_stop).row(btn_change_step, btn_statistic)

    await bot.send_message(user.id, "Отображаем кнопки", reply_markup=navigation_kb)


@dp.message_handler(commands=('step',))
async def change_interval_cmd(message: types.Message):
    buttons = types.InlineKeyboardMarkup().row(*const.INTERVAL_BUTTONS)
    if settings.DEBUG_MODE:
        buttons.row(*const.DEBUG_BUTTONS)

    await bot.send_message(message.from_user.id,
                           const.CHOOSE_INTERVAL_TEXT,
                           reply_markup=buttons)


@dp.callback_query_handler(lambda c: c.message.text == const.CHOOSE_INTERVAL_TEXT)
async def set_replied_interval(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user = callback_query.from_user
    interval_seconds = int(callback_query.data)

    _ = await set_interval(user, interval_seconds)

    # TODO: seconds to minutes (via datetime?)
    interval_representation = f'{interval_seconds} секунд'
    reply = 'Установлен интервал: {}'.format(interval_representation)
    await bot.send_message(user.id, reply)


BTNNAME_HANDLER_MAP = {
    'Старт': start_session,
    'Стоп': stop_session,
    'Изменить интервал': change_interval_cmd,
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


def get_choose_categories_msg_payload(activity: tuple, categories: Tuple[tuple]
                                      ) -> Dict[str, Union[str, dict]]:
    activity_id, _, _, _, start, finish = activity
    start = datetime.strptime(start.rsplit(".", 1)[0], "%Y-%d-%m %H:%M:%S")
    finish = datetime.strptime(finish.rsplit(".", 1)[0], "%Y-%d-%m %H:%M:%S")

    category_btns = []
    for category_id, name in categories:
        data = json.dumps({'act_id': activity_id, 'cat_id': category_id},
                          ensure_ascii=False)
        category_btns.append(types.InlineKeyboardButton(name, callback_data=data))

    btns_by_rows = more_itertools.chunked(category_btns, const.MAX_ROW_BUTTONS)
    buttons = types.InlineKeyboardMarkup()
    for btns in btns_by_rows:
        buttons.row(*btns)

    msg_payload = {
        'msg': 'Что делал в этот период: {event_interval}'.format(
            event_interval=f'{start.strftime("%H:%M:%S")} - {finish.strftime("%H:%M:%S")}',
        ),
        'payload': {'reply_markup': buttons},
    }
    return msg_payload


async def send_choose_categories(u: types.User, session_id: int, interval_seconds: int):
    activity_id = db.start_activity(session_id, interval_seconds)
    activity = db.get_unstopped_activity(activity_id)
    categories = db.list_categories(u)

    msg_payload = get_choose_categories_msg_payload(activity, categories)
    await bot.send_message(u.id, msg_payload['msg'], **msg_payload['payload'])


@dp.callback_query_handler(lambda c: 'act_id' in c.data)
async def finish_activity(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    data = json.loads(callback_query.data)
    user = callback_query.from_user

    try:
        activity_id, category_id = data['act_id'], data['cat_id']
        db.stop_activity(activity_id, category_id)
    except DoesNotExist:
        reply = 'Промежуток уже был заполнен'
    except RuntimeError:
        reply = 'Ошибка на сервере! Как сказал инженер Чернобыльской АЭС: "...Упс"'
    else:
        _, category_name = db.get_category(category_id)
        reply = f'Заполнено: "{category_name}"'

    await bot.send_message(user.id, reply)


if __name__ == '__main__':
    db.migrate()
    executor.start_polling(dp, skip_updates=True)
