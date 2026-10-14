from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from core.exceptions import AppException
from router import router

@asynccontextmanager
async def lifespan(app : FastAPI):

    yield

app = FastAPI(
    lifespan=lifespan
)

app.include_router(router)

@app.exception_handler(exc_class_or_status_code=AppException)
async def app_exception_handler(request : Request, exc : AppException):
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
    return JSONResponse(
        status_code=500,
        content={
            "message": "Something went wrong. Please try again later."
        }
    )
