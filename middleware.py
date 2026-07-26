import logging
from typing import Any, Awaitable, Callable

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
        try:
            await event.answer()
        except Exception:
            pass
        return await handler(event, data)
