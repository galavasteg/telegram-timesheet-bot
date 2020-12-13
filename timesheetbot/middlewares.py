"""Аутентификация — пропускаем сообщения только от определенных Telegram аккаунтов.

Любой пользователь имеет доступ, если белый список не задан.
"""
from typing import Iterable

from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware


class AccessMiddleware(BaseMiddleware):
    def __init__(self, user_id_white_list: Iterable[int]):
        super().__init__()

        # Everyone have access if `access_ids` is empty
        self._access_ids = set(map(int, user_id_white_list))

    async def on_process_message(self, message: types.Message, _) -> None:
        access_denied = self.access_ids and int(message.from_user.id) not in self.access_ids
        if access_denied:
            await message.answer("Access Denied")
            raise CancelHandler()
