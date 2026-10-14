from typing import Literal

from pydantic import BaseModel, Field
from schemas.base_schema import BaseRequestSchema

class RoutingRequest(BaseRequestSchema):
    locations: list[list[float, float]]
    sources: list[int]
    destinations: list[int]
    metrics: list[Literal["distance", "duration"]] = Field(default=["distance", "duration"])
    units: Literal["m", "km", "mi"] = Field(default="m")