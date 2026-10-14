from datetime import datetime
from uuid import UUID
from enum import StrEnum

from pydantic import BaseModel
from schemas.base_schema import BaseRequestSchema, BaseResponseSchema

class FillLevelStatus(StrEnum):
    EMPTY = "Empty"
    STARTING_TO_FILL = "Starting to fill"
    HALF_FILLED = "Half filled"
    ALMOST_FULL = "Almost full"
    FULL = "Full"
    OVERFLOWING = "Overflowing"

class CreateDustbinRequest(BaseRequestSchema):
    name : str
    latitude : float
    longitude : float
    address : str
    accepted_waste_types : list[str] | None
    fill_level : FillLevelStatus

class DustbinResponse(CreateDustbinRequest):
    id : UUID
    photos_keys : list[str]
    photo_urls : list[str]
    confidence_score : float
    report_count : int
    last_verified_at : datetime | None
    created_at : datetime
    updated_at : datetime

class DustbinNearbyResponse(DustbinResponse):
    distance_in_m : float

class NearbyDustbinConflict(BaseModel):
    id : UUID
    name : str
    latitude : float
    longitude : float
    address : str
    photo_urls : list[str]
    distance_in_m : float