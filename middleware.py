from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery


class CallbackAnswerMiddleware(BaseMiddleware):
    """Auto-answer every callback query before the handler runs.

    This prevents the loading spinner from getting stuck when a handler
    raises an exception before calling callback.answer() (e.g. edit_text
    fails with MessageNotModified). callback.answer() is idempotent in
    aiogram 3 — handlers can still call it again for show_alert messages.
    """

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
