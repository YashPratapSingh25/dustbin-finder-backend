from dataclasses import dataclass


@dataclass
class BoundingBox:
    min_lat : float
    max_lat : float
    min_lng : float
    max_lng : float
