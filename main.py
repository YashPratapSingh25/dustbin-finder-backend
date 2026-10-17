from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from core.app_logger import HttpLogger, setup_logging
from core.exceptions import AppException
from core.middlewares.logging_middleware import LoggingMiddleware
from router import router

setup_logging()

@asynccontextmanager
async def lifespan(app : FastAPI):

    yield

app = FastAPI(
    lifespan=lifespan
)

app.include_router(router)

@app.exception_handler(exc_class_or_status_code=AppException)
async def app_exception_handler(request : Request, exc : AppException):
    if exc.status_code == 403:
        HttpLogger.warning("Unauthorized Access")
    elif exc.status_code == 429:
        HttpLogger.warning("Rate Limit Exceeded")
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder({
            "message": exc.message,
            "result": exc.result
        })
    )

@app.exception_handler(exc_class_or_status_code=500)
async def server_exception_handler(
    request: Request,
    exc : Exception
):
    HttpLogger.exception(f"Server Exception : {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "message": "Something went wrong. Please try again later."
        }
    )


app.add_middleware(LoggingMiddleware)