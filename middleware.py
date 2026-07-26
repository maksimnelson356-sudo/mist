import contextlib
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery

logger = logging.getLogger("MIST.middleware")


class CallbackAnswerMiddleware(BaseMiddleware):
    """Auto-answer every callback query before the handler runs."""

    async def __call__(
        self,
        handler: Callable[[CallbackQuery, dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        with contextlib.suppress(Exception):
            await event.answer()
        return await handler(event, data)
