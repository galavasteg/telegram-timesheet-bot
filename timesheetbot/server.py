"""Telegram bot server."""
import functools
import itertools
import json
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from logging import getLogger
from typing import Dict, Union, Tuple, Iterable, List

from aiogram import Bot, Dispatcher
from aiogram import types
from aiogram.types import InputFile
from dateutil.relativedelta import relativedelta
import more_itertools

import settings
from settings import TELEGRAM_API_TOKEN, ACCESS_IDS_FILE, DEBUG_MODE, SITE_URL
from timesheetbot.services.report import generate_report
from . import utils, messages as msgs
from .db_manager import DBManager, DoesNotExist
from .middlewares import AccessMiddleware


log = getLogger(__name__)

const = settings.constants

db = DBManager()

assert TELEGRAM_API_TOKEN, 'TELEGRAM_API_TOKEN not provided.'
bot = Bot(token=TELEGRAM_API_TOKEN, proxy=None if DEBUG_MODE else 'http://proxy.server:3128')
if not DEBUG_MODE:
    asyncio.get_event_loop().run_until_complete(
        bot.set_webhook(f'{SITE_URL}/{TELEGRAM_API_TOKEN}', max_connections=1)
    )
dp = Dispatcher(bot)

assert ACCESS_IDS_FILE.exists(), f'No such file: {ACCESS_IDS_FILE=}'
with ACCESS_IDS_FILE.open(encoding='utf-8') as f:
    ACCESS_IDS = set(json.load(f))
dp.middleware.setup(AccessMiddleware(ACCESS_IDS))

stop_sending_events = defaultdict(lambda: [])
user_start_interval_waiters = defaultdict(lambda: [])
locks = {}


class FoundUnfilledActivity(BaseException): ...
class WrongStatPeriod(BaseException): ...


async def get_interval(u: types.User):
    async with locks[u.id]:
        interval_seconds = db.get_interval_seconds(u)
    return interval_seconds


async def set_interval(u: types.User, interval_seconds):
    if u.id in locks:
        async with locks[u.id]:
            rows_num = db.set_interval_seconds(u, interval_seconds)
    else:
        db.register_user_if_not_exists(u)
        rows_num = db.set_interval_seconds(u, interval_seconds)

    return rows_num


@dp.message_handler(commands=('help',))
async def send_welcome(message: types.Message):
    await message.answer(msgs.WELCOME)


async def send_events_coro(user, session_id):
    while True:
        interval_seconds = await get_interval(user)
        await asyncio.sleep(interval_seconds)
        await send_choose_categories(user, session_id, interval_seconds)


def get_ts_btns() -> types.ReplyKeyboardMarkup:
    btn_start = types.KeyboardButton('Старт')
    btn_stop = types.KeyboardButton('Стоп')
    btn_change_step = types.KeyboardButton('Изменить интервал')
    btn_statistic = types.KeyboardButton('Статистика >>')

    navigation_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    navigation_kb.row(btn_start, btn_stop).row(btn_change_step, btn_statistic)
    return navigation_kb


@dp.message_handler(commands=('start',))
@dp.message_handler(lambda msg: msg.text.lower() in ('start', 'старт'))
async def start_session(message: types.Message):
    user = message.from_user

    db.register_user_if_not_exists(user)

    await check_activities_filled(user)

    session_id, is_new_session = db.get_new_or_existing_session_id(user)

    if not is_new_session:
        await message.answer(msgs.CLOSE_SESSION_PLS)
        return

    await message.answer('У вас есть {wait_for_sec:d} секунд, чтобы выбрать интервал на эту сессию.'.format(
        wait_for_sec=const.WAIT_INTERVAL_FROM_USER_BEFORE_START
    ))
    await change_interval_cmd(message)

    sleep = asyncio.create_task(asyncio.sleep(const.WAIT_INTERVAL_FROM_USER_BEFORE_START))
    user_start_interval_waiters[user.id].append(sleep)
    try:
        await sleep
    except asyncio.CancelledError as exc:
        pass

    locks[user.id] = asyncio.Lock()
    interval_seconds = await get_interval(user)
    # TODO: seconds to minutes (via datetime?)
    first_bot_msg_time = datetime.now() + timedelta(0, interval_seconds)
    reply = msgs.FIRST_BOT_MSG.format(
        time=first_bot_msg_time.strftime("%H:%M:%S"))

    navigation_kb = get_ts_btns()
    await message.answer(reply, reply_markup=navigation_kb)

    log.info('Opened session. User: ' + user.get_mention())

    task = asyncio.create_task(send_events_coro(user, session_id))
    stop_sending_events[user.id].append(task)
    await task


async def check_activities_filled(u):
    try:
        activities = db.get_user_unfilled_activities(u)
    except DoesNotExist:
        return True
    else:
        log.error(str(activities))
        raise FoundUnfilledActivity



@dp.message_handler(commands=('stop',))
@dp.message_handler(lambda msg: msg.text.lower() in ('stop', 'стоп'))
async def stop_session(message: types.Message):
    user = message.from_user

    stopped = db.try_stop_session(user)
    reply = 'Остановились' if stopped else 'Нечего останавливать'

    await message.answer(reply)

    if stopped and user.id in stop_sending_events:
        [task.cancel() for task in stop_sending_events[user.id]]
        msg = 'Closed session. User: ' + message.from_user.get_mention()
        log.info(msg)


@dp.message_handler(commands=('list',))
async def list_categories_cmd(message: types.Message):
    user = message.from_user
    categories = db.list_categories(user)
    msg = 'Категории:\n\n{}'.format(
            '\n'.join(name for _, name in categories))
    await message.answer(msg)


@dp.message_handler(commands=('buttons',))
async def control_buttons_cmd(message: types.Message):
    await bot.send_message(message.from_user.id, "Отображаем кнопки", reply_markup=get_ts_btns())


@dp.message_handler(lambda msg: msg.text.lower() in ('change interval', 'изменить интервал'))
async def change_interval_cmd(message: types.Message):
    buttons = types.InlineKeyboardMarkup().row(*const.INTERVAL_BUTTONS)
    if settings.DEBUG_MODE:
        buttons.row(*const.DEBUG_BUTTONS)

    await bot.send_message(message.from_user.id, const.CHOOSE_INTERVAL_TEXT, reply_markup=buttons)


@dp.callback_query_handler(lambda c: c.message.text == const.CHOOSE_INTERVAL_TEXT)
async def set_replied_interval(callback_query: types.CallbackQuery):
    user = callback_query.from_user
    interval_seconds = int(callback_query.data)

    _ = await set_interval(user, interval_seconds)
    [task.cancel() for task in user_start_interval_waiters[user.id]]

    await bot.answer_callback_query(
        callback_query_id=callback_query.id,
        show_alert=False,
        text=f'Установлен интервал: {timedelta(seconds=interval_seconds)}',
    )


@dp.message_handler(lambda msg: msg.text.lower() in ('statistic >>', 'статистика >>'))
async def stats_cmd(message: types.Message):
    await bot.send_message(
        message.from_user.id,
        const.CHOOSE_STATS_TEXT,
        reply_markup=const.STATS_BUTTONS,
    )


def increment_activities_duration(acc: datetime, activity: tuple) -> datetime:
    start, finish = map(utils.parse_datetime, activity[-3:-1])
    duration = finish - start
    acc += duration
    return acc


def calc_category_stats(category: str, activities: itertools._grouper
                        ) -> Dict[str, Union[timedelta, str, int]]:
    time_ = functools.reduce(increment_activities_duration,
                             tuple(activities), timedelta())
    stat_repr = dict(category=category, time=time_)
    return stat_repr


def represent_stats(category_stats: Tuple[Dict[str, Union[timedelta, str, float, int]]]) -> str:
    category_stat_template = '{category:<15} {time} ({percent:.2f}%)'
    stats_repr = '\n'.join(category_stat_template.format(**stats)
                           for stats in category_stats)
    return stats_repr


def calc_stats(activities: List[tuple]
               ) -> Tuple[Dict[str, Union[str, int, float, timedelta]], ...]:
    category_filter = lambda activity: activity[-1]
    groups_gen = itertools.groupby(sorted(activities, key=category_filter),
                                   key=category_filter)
    category_stats = tuple(itertools.starmap(calc_category_stats, groups_gen))

    all_activities_time = sum((stats.get('time', timedelta())
                               for stats in category_stats), timedelta())
    for stats in category_stats:
        percent = stats.get('time', timedelta()) / all_activities_time * 100
        stats.update(percent=percent)

    return category_stats


def get_stats(u: types.User, period: Union[Dict[str, int], str]) -> Tuple[str, Tuple[datetime, datetime], List[tuple]]:
    t1 = datetime.now()
    t1 -= timedelta(microseconds=t1.microsecond)
    msg_title = 'За {stat_period} ваша статистика следующая:'

    if isinstance(period, dict):
        if 'months' in period:
            t0 = t1 - relativedelta(**period)
        else:
            t0 = t1 - timedelta(**period)
        sessions = db.filter_user_sessions_by_start(u, t0)
        stat_period = f'{utils.parse_datetime(str(t0))} - {utils.parse_datetime(str(t1))}'
    elif period == 'session':
        sessions = (db.get_last_started_session(u),)
        t0 = sessions[0][-2]
        stat_period = f'последнюю сессию'
    else:
        raise WrongStatPeriod()

    session_ids = tuple(session[0] for session in sessions)
    activities = db.get_timesheet_frame_by_sessions(session_ids)

    # TODO: other representations
    stats = calc_stats(activities)
    stats_repr = represent_stats(stats)
    stats_repr = f'{msg_title}\n`{stats_repr}`'
    stats_repr = stats_repr.format(stat_period=stat_period)

    return stats_repr, (t0, t1), activities


@dp.callback_query_handler(lambda c: c.message.text == const.CHOOSE_STATS_TEXT)
async def get_requested_stats(callback_query: types.CallbackQuery):
    request_message = callback_query.message

    await bot.answer_callback_query(callback_query.id)
    user = callback_query.from_user
    try:
        stats_period = json.loads(callback_query.data)
    except ValueError:
        stats_period = callback_query.data

    send_file_task = []
    try:
        stats, (t0, t1), activities = get_stats(user, stats_period)
    except DoesNotExist:
        text = 'За данный период ничего не найдено!'
    else:
        text = stats
        report = generate_report((t0, t1), activities)
        filename = f'ts-stats-{t0:%Y%m%dT%H%M%S}-{t1:%Y%m%dT%H%M%S}.xlsx'
        report_file = InputFile(report, filename=filename)
        send_file_task = [bot.send_document(request_message.chat.id, report_file)]

    async def edit_request_msg():
        await request_message.edit_reply_markup()
        await request_message.edit_text(text, parse_mode="Markdown")

    await asyncio.gather(edit_request_msg(), *send_file_task)


def split_buttons_on_rows(btns: Iterable[types.InlineKeyboardButton]
                          ) -> types.InlineKeyboardMarkup:
    btns_by_rows = more_itertools.chunked(btns, const.MAX_ROW_BUTTONS)
    buttons = types.InlineKeyboardMarkup()
    for btns in btns_by_rows:
        buttons.row(*btns)
    return buttons


def get_choose_categories_msg_payload(activity: tuple, categories: Tuple[tuple]) -> Dict[str, Union[str, dict]]:
    activity_id, _, _, _, start, finish = activity
    start = utils.parse_datetime(start)
    finish = utils.parse_datetime(finish)

    category_btns = []
    for category_id, _, name in categories:
        data = json.dumps({'act_id': activity_id, 'cat_id': category_id}, ensure_ascii=False)
        category_btns.append(types.InlineKeyboardButton(name, callback_data=data))

    buttons = split_buttons_on_rows(category_btns)

    msg_payload = {
        'msg': 'Что делал в этот период: {event_interval}'.format(
            event_interval=f'{start.strftime("%H:%M:%S")} - {finish.strftime("%H:%M:%S")}',
        ),
        'payload': {'reply_markup': buttons},
    }
    return msg_payload


async def send_choose_categories(u: types.User, session_id: int, interval_seconds: int):
    if not db.has_active_session(u):
        return

    activity_id = db.start_activity(session_id, interval_seconds)
    activity = db.get_unstopped_activity(activity_id)
    categories = db.list_categories(u)

    msg_payload = get_choose_categories_msg_payload(activity, categories)
    await bot.send_message(u.id, msg_payload['msg'], **msg_payload['payload'])


@dp.callback_query_handler(lambda c: 'act_id' in c.data)
async def finish_activity(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    data = json.loads(callback_query.data)
    request_message = callback_query.message

    try:
        activity_id, category_id = data['act_id'], data['cat_id']
        db.stop_activity(activity_id, category_id)
    except DoesNotExist:
        reply = '\n'.join((request_message.text, 'Промежуток уже был заполнен'))
    except RuntimeError:
        reply = '\n'.join((request_message.text, 'Ошибка на сервере! Как сказал инженер Чернобыльской АЭС: "...Упс"'))
    else:
        _, _, category_name = db.get_category(category_id)
        reply = '\n'.join((request_message.text, f'Заполнено: `{category_name}`'))

    await request_message.edit_reply_markup()
    await request_message.edit_text(reply, parse_mode="Markdown")


if __name__ == '__main__':
    from aiogram.utils import executor

    db.migrate()
    executor.start_polling(dp, skip_updates=True)
