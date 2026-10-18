import asyncio
import uuid
from core.app_logger import HttpLogger, log_task
from core.exceptions import ConflictException
from model.dustbin import Dustbin
from repository.dustbin_repo import DustbinRepository
from schemas.base_schema import PaginatedServiceResponse, Pagination
from schemas.dustbin_schemas import (
    CreateDustbinRequest,
    DustbinNearbyResponse,
    DustbinResponse,
    NearbyDustbinConflict,
)
from service.routing_service import RoutingService
from service.s3 import S3Service
from utils.services import round_to_multiple


class DustbinService:
    def __init__(
        self,
        s3_service: S3Service,
        routing_service: RoutingService,
        dustbin_repo: DustbinRepository,
    ):
        self.s3_service = s3_service
        self.dustbin_repo = dustbin_repo
        self.routing_service = routing_service

    async def _get_photos_url(self, dustbin: Dustbin) -> list[str]:
        presigned_urls = []
        for key in dustbin.photos_keys:
            url = await self.s3_service.get_presigned_url(key)
            presigned_urls.append(url)

        return presigned_urls

    async def create_dustbin(
        self,
        create_dustbin_schema: CreateDustbinRequest,
        images_bytes: list[bytes],
    ) -> DustbinResponse:

        # Check if dustbin already exists within the range of 50m
        with log_task("NEARBY_DUSTBIN_CHECK"):
            db_result = await self.dustbin_repo.get_nearby_dustbins(
                create_dustbin_schema.latitude,
                create_dustbin_schema.longitude,
                0.05,
            )

        if len(db_result) != 0:
            dustbin, distance_km = db_result[0]
            distance_in_m = round(distance_km * 1000, 2)

            raise ConflictException(
                result=NearbyDustbinConflict(
                    id=dustbin.id,
                    latitude=dustbin.latitude,
                    longitude=dustbin.longitude,
                    address=dustbin.address,
                    name=dustbin.name,
                    distance_in_m=distance_in_m,
                    photo_urls=await self._get_photos_url(dustbin),
                ),
                message=f"Dustbin {dustbin.name} already exists within {round(distance_km * 1000)}m",
            )

        photos_keys = []
        presigned_urls = []

        with log_task("S3_IMAGE_UPLOAD"):
            for i in range(len(images_bytes)):
                # Creating S3 name as <name>_<random_uuid>.jpeg and assigning in list to store in DB
                obj_name = f"dustbin_images/{create_dustbin_schema.name.replace(" ", "")}_{uuid.uuid4()}"
                photos_keys.append(obj_name)
                # Uploading and fetching the presigned url to return in API
                url = await self.s3_service.upload_file(
                    images_bytes[i], photos_keys[i]
                )
                presigned_urls.append(url)

        with log_task("ADD_DUSTBIN_QUERY"):
            new_dustbin = await self.dustbin_repo.add_dustbin(
                create_dustbin_schema, photos_keys
            )

        return DustbinResponse(
            id=new_dustbin.id,
            name=create_dustbin_schema.name,
            latitude=create_dustbin_schema.latitude,
            longitude=create_dustbin_schema.longitude,
            address=create_dustbin_schema.address,
            photos_keys=photos_keys,
            photo_urls=presigned_urls,
            fill_level=create_dustbin_schema.fill_level,
            confidence_score=new_dustbin.confidence_score,
            report_count=new_dustbin.report_count,
            last_verified_at=new_dustbin.last_verified_at,
            created_at=new_dustbin.created_at,
            updated_at=new_dustbin.updated_at,
        )

    async def get_nearby_dustbins(
        self,
        latitude: float,
        longitude: float,
        radius_in_m: float,
        pagination: Pagination,
    ) -> PaginatedServiceResponse:
        radius_km = radius_in_m / 1000

        with log_task("TOTAL_DUSTBINS_QUERY"):
            total_count = await self.dustbin_repo.get_nearby_centers_count(
                latitude, longitude, radius_km
            )

        # Rows (list) containing the Dustbin data and distance in km
        with log_task("NEARBY_DUSTBINS_QUERY"):
            db_result = await self.dustbin_repo.get_nearby_dustbins(
                latitude,
                longitude,
                radius_km,
                pagination.limit,
                pagination.offset,
            )

        nearby_dustbins : list[DustbinNearbyResponse] = []

        for dustbin, distance_in_km in db_result:
            nearby_dustbin = DustbinNearbyResponse(
                id=dustbin.id,
                name=dustbin.name,
                latitude=dustbin.latitude,
                longitude=dustbin.longitude,
                address=dustbin.address,
                fill_level=dustbin.fill_level,
                photos_keys=dustbin.photos_keys,
                photo_urls=await self._get_photos_url(dustbin),
                confidence_score=dustbin.confidence_score,
                report_count=dustbin.report_count,
                last_verified_at=dustbin.last_verified_at,
                created_at=dustbin.created_at,
                updated_at=dustbin.updated_at,
                distance_in_m=round(distance_in_km * 1000, 2),
            )

            nearby_dustbins.append(nearby_dustbin)

        if len(nearby_dustbins) == 0:
            return PaginatedServiceResponse(result=[], total_items=0)

        # Fetching the real time route distance between the user and dustbin coordinates
        try:
            with log_task("ROUTING_API_CALL"):
                routing_result = await self.routing_service.get_distance_duration(
                    user_lat=latitude,
                    user_long=longitude,
                    dustbin_locations=[
                        # [Longitude, Latitude]
                        [dustbin.longitude, dustbin.latitude]
                        for dustbin in nearby_dustbins
                    ],
                )
        except Exception as e:
            HttpLogger.error(f"OPEN ROUTE SERVICE NOT WORKING: [{type(e).__name__}]: {repr(e)}")
            return PaginatedServiceResponse(
                result=nearby_dustbins, total_items=total_count
            )

        # If routing service is unavailable, return the route distance calculated by Haversine
        if not routing_result:
            return PaginatedServiceResponse(
                result=nearby_dustbins, total_items=total_count
            )

        durations, distances = routing_result

        for i in range(len(distances)):
            # Round to nearest 50 (100, 150, 200, 250....)
            nearby_dustbins[i].distance_in_m = round_to_multiple(distances[i], 50)

        sorted_dustbins = sorted(
            nearby_dustbins, key=lambda dustbin: dustbin.distance_in_m
        )

        filtered_dustbins = [dustbin for dustbin in sorted_dustbins if dustbin.distance_in_m < radius_in_m]

        return PaginatedServiceResponse(result=filtered_dustbins, total_items=total_count)
