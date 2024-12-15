from math import acos, cos, radians, sin
from typing import Tuple
import random

DRIVER_FIRST_NAMES = ["Jose", "Juan", "Manuel", "Pedro"]
DRIVER_LAST_NAMES = ["Garcia", "Hernandez", "Lopez", "Perez"]


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


def generate_driver_data() -> Tuple[str, str, str]:
    first_name = random.choice(DRIVER_FIRST_NAMES)
    last_name = random.choice(DRIVER_LAST_NAMES)
    phone_country_code = "+58"
    phone_prefix = f"4{random.choice(['12', '14', '16', '24', '26'])}"
    phone_number = f"{phone_prefix}{random.randint(1000000, 9999999)}"
    return first_name, last_name, phone_country_code, phone_number
