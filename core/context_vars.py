from contextvars import ContextVar
import uuid

class ContextVars():
    request_id : ContextVar[str] = ContextVar("request_id", default="-")
    method : ContextVar[str] = ContextVar("method", default="-")
    path : ContextVar[str] = ContextVar("path", default="-")
    user_id : ContextVar[str] = ContextVar("user_id", default="Unauthenticated")