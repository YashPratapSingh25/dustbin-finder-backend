from math import ceil
from typing import Annotated, List

from fastapi import APIRouter, Depends, Form, Query

from core.dependencies import get_dustbin_repo, get_dustbin_service, get_images_bytes, get_pagination, get_s3_service
from repository.dustbin_repo import DustbinRepository
from schemas.base_schema import ApiResponseSchema, PaginatedResponseSchema, Pagination, PaginationMetaData
from schemas.dustbin_schemas import CreateDustbinRequest, DustbinNearbyResponse, DustbinResponse, FillLevelStatus
from service.dustbin_service import DustbinService
from service.s3 import S3Service
from utils.annotated_types import PageNumberQuery, PageSizeQuery

dustbin_router = APIRouter(prefix="/dustbin", tags=["dustbins"])

@dustbin_router.post('/', response_model=ApiResponseSchema[DustbinResponse])
async def create_dustbin(
    name: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    address: str = Form(...),
    fill_level: FillLevelStatus | None = Form(default=None),
    images_bytes : list[bytes] = Depends(get_images_bytes),
    dustbin_service : DustbinService = Depends(get_dustbin_service)
):
    schema = CreateDustbinRequest(
        name=name,
        latitude=latitude,
        address=address,
        longitude=longitude,
        fill_level=fill_level
    )
    result = await dustbin_service.create_dustbin(
        schema,
        images_bytes=images_bytes,
    )

    return ApiResponseSchema(
        message = "Dustbin added successfully",
        result = result
    )

@dustbin_router.get("/nearby", response_model=PaginatedResponseSchema[DustbinNearbyResponse])
async def get_nearby_dustbins(
    latitude : float = Query(...),
    longitude : float = Query(...),
    radius_in_m : float = Query(default=500),
    pagination : Pagination = Depends(get_pagination),
    dustbin_service : DustbinService = Depends(get_dustbin_service)
):
    paginated_result = await dustbin_service.get_nearby_dustbins(
        latitude=latitude,
        longitude=longitude,
        pagination=pagination,
        radius_in_m=radius_in_m
    )

    total_pages = ceil(paginated_result.total_items / pagination.page_size)

    return PaginatedResponseSchema(
        message="Nearby dustbins fetched successfully",
        metadata=PaginationMetaData(
            page_number = pagination.page_number,
            page_size = pagination.page_size,
            has_next = pagination.page_number < total_pages,
            has_previous = pagination.page_number > 1,
            total_pages = total_pages,
            total_items = paginated_result.total_items
        ),
        result=paginated_result.result
    )