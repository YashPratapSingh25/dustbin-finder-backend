from fastapi import APIRouter
from router.dustbin_router import dustbin_router

router = APIRouter()

router.include_router(dustbin_router)