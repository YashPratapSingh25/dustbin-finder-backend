from typing import Literal

import httpx
from core.app_logger import HttpLogger
from core.config import settings
from schemas.routing_schema import RoutingRequest
from utils.services import extract_json


class RoutingService:
    OPEN_ROUTING_SERVICE_MATRIX_URL = "https://api.heigit.org/openrouteservice/v2/matrix"

    async def get_distance_duration(
        self,
        user_lat : float,
        user_long : float,
        dustbin_locations : list[list[float, float]],
        profile : Literal["driving-car", "foot-walking", "cycling-road"] = settings.DEFAULT_ORS_PROFILE
    ) -> tuple[list[float], list[float]] | None:
        user_location = (user_long, user_lat)

        request = RoutingRequest(
            locations=[user_location, *dustbin_locations],
            sources=[0],
            destinations=list(range(1, len(dustbin_locations) + 1)),
        )

        headers = {
            'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
            'Authorization': settings.OPEN_ROUTE_SERVICE_API_KEY,
            'Content-Type': 'application/json; charset=utf-8'
        }

        
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                url=f"{self.OPEN_ROUTING_SERVICE_MATRIX_URL}/{profile}",
                data=request.model_dump_json(),
                headers=headers
            )

            if (response.status_code != 200):
                HttpLogger.error(response.text)
                return None

            response_json = extract_json(response.text)

            durations : float = response_json["durations"][0]
            distances : float = response_json["distances"][0]

            return durations, distances