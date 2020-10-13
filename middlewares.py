"""
Аутентификация — пропускаем сообщения только
от определенных Telegram аккаунтов

"""
from typing import Iterable

from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware


class AccessMiddleware(BaseMiddleware):
    def __init__(self, access_ids: Iterable[int]):
        self.access_ids = set(map(int, access_ids))
        super().__init__()

    async def on_process_message(self, message: types.Message, _) -> None:
        if self.access_ids and int(message.from_user.id) not in self.access_ids:
            await message.answer("Access Denied")
            raise CancelHandler()
