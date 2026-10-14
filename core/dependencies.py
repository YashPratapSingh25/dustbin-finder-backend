from io import BytesIO
import aioboto3
from fastapi import Depends, File, Query, UploadFile
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from core.config import settings
from core.exceptions import (
    BadRequestException,
    ContentNotSupportedException,
    ContentTooLargeException,
)
from core.db.db_config import async_session_maker
from repository.dustbin_repo import DustbinRepository
from schemas.base_schema import Pagination
from service.dustbin_service import DustbinService
from service.routing_service import RoutingService
from service.s3 import S3Service
from botocore.config import Config


async def get_db_session():
    async with async_session_maker() as session:
        async with session.begin():
            yield session


ALLOWED_FORMATS = settings.ALLOWED_IMAGE_FORMATS.split(",")

MAX_SIZE = settings.MAX_IMAGE_SIZE * 1024 * 1024


async def _get_image_bytes(file: UploadFile) -> bytes:
    image_bytes = await file.read()

    try:
        with Image.open(BytesIO(image_bytes)) as img:
            img.verify()

            if img.format not in ALLOWED_FORMATS:
                raise ContentNotSupportedException(
                    f"Only image supported formats are {settings.ALLOWED_IMAGE_FORMATS}"
                )
    except ContentNotSupportedException:
        raise  # Rethrow as this exception is already handled
    except Exception:
        raise ContentNotSupportedException(
            "Image Integrity Verification Failed"
        )  # img.verify failed

    if len(image_bytes) > MAX_SIZE:
        raise ContentTooLargeException(
            f"Image should be less than {settings.MAX_IMAGE_SIZE} MB"
        )

    return image_bytes


async def get_images_bytes(images: list[UploadFile] = File(...)) -> list[bytes]:
    if not 0 < len(images) < 5:
        raise BadRequestException(message="Upload images in the range of 1 to 5")

    bytes_list = []

    for image in images:
        byte = await _get_image_bytes(image)
        bytes_list.append(byte)

    return bytes_list

def get_pagination(
    page_number: int = Query(ge=1, default=1), page_size: int = Query(ge=1, default=5)
) -> Pagination:
    limit = page_size
    offset = (page_number - 1) * page_size

    return Pagination(limit=limit, offset=offset, page_number=page_number, page_size=page_size)

def get_routing_service():
    return RoutingService()

async def get_s3_service():
    session = aioboto3.Session()

    async with session.client(
        "s3",
        region_name=settings.S3_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "virtual"},
        ),
    ) as s3_client:
        yield S3Service(s3_client)


def get_dustbin_repo(db_session: AsyncSession = Depends(get_db_session)):
    return DustbinRepository(db_session)


def get_dustbin_service(
    s3_service: S3Service = Depends(get_s3_service),
    dustbin_repo: DustbinRepository = Depends(get_dustbin_repo),
    routing_service : RoutingService = Depends(get_routing_service)
):
    return DustbinService(s3_service, routing_service, dustbin_repo)