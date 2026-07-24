import uuid
import contextvars

_request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")


def get_request_id() -> str:
    rid = _request_id_var.get()
    if not rid:
        rid = str(uuid.uuid4())[:12]
        _request_id_var.set(rid)
    return rid


def new_request_id() -> str:
    rid = str(uuid.uuid4())[:12]
    _request_id_var.set(rid)
    return rid
