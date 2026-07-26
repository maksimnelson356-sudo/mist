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
        logger.info(f"[MW] callback answer: data={event.data} user={event.from_user.id}")
        try:
            await event.answer()
        except Exception as e:
            logger.warning(f"[MW] answer failed: {e}")
        result = await handler(event, data)
        logger.info(f"[MW] handler done: data={event.data}")
        return result
