import json
import re
from math import cos, radians

from utils.models import BoundingBox


def extract_json(text: str):
    text = text.strip()

    # Remove opening fence
    text = re.sub(r"^```(?:json)?\s*", "", text)

    # Remove closing fence
    text = re.sub(r"\s*```$", "", text)

    return json.loads(text)


def get_bounding_box(
    latitude: float,
    longitude: float,
    radius_km: float,
):
    # 1° latitude is approximately 111.32 km.
    # Longitude distance varies based on the current latitude.
    lat_delta = radius_km / 111.32
    lng_delta = radius_km / (
        111.32 * cos(radians(latitude))
    )

    return BoundingBox(
        latitude - lat_delta, # Minimun Latitude
        latitude + lat_delta, # Maximum Latitude
        longitude - lng_delta, # Minimum Longitude
        longitude + lng_delta, # Maximum Longitude
    )