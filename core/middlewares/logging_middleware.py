import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware

from core.app_logger import HttpLogger
from core.context_vars import ContextVars

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        ContextVars.request_id.set(str(uuid.uuid4()))        
        ContextVars.method.set(request.method)
        ContextVars.path.set(request.url.path)
        

        HttpLogger.info("INCOMING HTTP REQUEST")

        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time

        if 200 <= response.status_code < 400:
            HttpLogger.info(
                f"HTTP request completed in {duration:.2f}s"
            )

        elif 400 <= response.status_code < 500:
            HttpLogger.info(
                f"HTTP request completed with client error ({response.status_code}) in {duration:.2f}s"
            )

        else:
            HttpLogger.error(
                f"HTTP request completed with server error ({response.status_code}) in {duration:.2f}s"
            )

        return response
