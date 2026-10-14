from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from utils.models import BoundingBox
from utils.services import get_bounding_box
from model.dustbin import Dustbin
from schemas.dustbin_schemas import CreateDustbinRequest, DustbinNearbyResponse


class DustbinRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def add_dustbin(
        self, create_schema: CreateDustbinRequest, object_names: list[str]
    ) -> Dustbin:
        new_dustbin = Dustbin(
            name=create_schema.name,
            latitude=create_schema.latitude,
            longitude=create_schema.longitude,
            address=create_schema.address,
            photos_keys=object_names,
            accepted_waste_types=create_schema.accepted_waste_types,
            fill_level=create_schema.fill_level,
        )

        self.db_session.add(new_dustbin)
        await self.db_session.flush()
        return new_dustbin

    def _get_distance_km(self, user_lat: float, user_lng: float):
        # SQL function to find difference in user and dustbin lat lng in radian
        lat_diff = func.radians(Dustbin.latitude - user_lat)
        lng_diff = func.radians(Dustbin.longitude - user_lng)

        # SQL function to find user and dustbin lat in radian to use it with sin and cos
        user_lat_rad = func.radians(user_lat)
        dustbin_lat_rad = func.radians(Dustbin.latitude)

        # SQL function to find haversine Constant
        a = func.pow(func.sin(lat_diff / 2), 2) + func.cos(user_lat_rad) * func.cos(
            dustbin_lat_rad
        ) * func.pow(func.sin(lng_diff / 2), 2)

        # SQL function to find actual distance
        distance_km = 2 * 6371 * func.asin(func.sqrt(a))
        return distance_km

    async def get_nearby_dustbins(
        self,
        user_lat: float,
        user_lng: float,
        radius_km: float,
        limit: int | None = None,
        offset: int | None = None,
    ):
        bounding_box = get_bounding_box(
            user_lat,
            user_lng,
            radius_km,
        )
        
        distance_km = self._get_distance_km(user_lat, user_lng)

        stmt = (
            select(Dustbin, distance_km)
            .where(
                Dustbin.latitude.between(bounding_box.min_lat, bounding_box.max_lat),
                Dustbin.longitude.between(bounding_box.min_lng, bounding_box.max_lng),
                distance_km <= radius_km,
            )
            .order_by(distance_km)
        )

        if limit:
            stmt = stmt.limit(limit)

        if offset:
            stmt = stmt.offset(offset)

        result = await self.db_session.execute(stmt)

        rows = result.all()

        return rows

    async def get_nearby_centers_count(self, user_lat, user_lng, radius_km : float) -> int:
        bounding_box = get_bounding_box(
            user_lat,
            user_lng,
            radius_km,
        )

        distance_km = self._get_distance_km(user_lat, user_lng)

        stmt = (
            select(func.count())
            .select_from(Dustbin)
            .where(
                Dustbin.latitude.between(bounding_box.min_lat, bounding_box.max_lat),
                Dustbin.longitude.between(bounding_box.min_lng, bounding_box.max_lng),
                distance_km <= radius_km,
            )
        )

        result = await self.db_session.execute(stmt)

        return result.scalar_one()