"""
Запускаемый сервер Telegram бота

"""
from typing import Callable

from aiogram import Bot, Dispatcher, executor, types

import messages as msgs
from middlewares import AccessMiddleware
from settings import LOG, ACCESS_IDS, TELEGRAM_API_TOKEN, DEBUG_MODE


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


# @log_errors
@dp.message_handler(commands=('start', 'help'))
async def send_welcome(message: types.Message):
    """Send "welcome" and info about bot usage to user"""
    if message.get_command(pure=True) == 'start':
        LOG.info('New user: ' + message.from_user.get_mention())
    await message.answer(msgs.welcome)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
