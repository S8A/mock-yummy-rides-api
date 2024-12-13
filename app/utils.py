from math import acos, cos, radians, sin
from typing import Tuple


def calculate_distance_between_coordinates(
    coordinate1: Tuple[float, float],
    coordinate2: Tuple[float, float]
) -> float:
    """
    Calculate the distance in kilometers between two coordinates using the
    great circle distance formula.
    """
    # Earth's radius in kilometers
    EARTH_RADIUS = 6371.0

    # Convert coordinates to radians
    lat1, lon1 = map(radians, coordinate1)
    lat2, lon2 = map(radians, coordinate2)

    try:
        # Calculate distance using spherical law of cosines
        distance = acos(
            sin(lat1) * sin(lat2) +
            cos(lat1) * cos(lat2) * cos(lon2 - lon1)
        ) * EARTH_RADIUS

        return round(distance, 2)
    except ValueError:
        # Handle case where coordinates are too close and acos gets a value > 1
        return 0.0
