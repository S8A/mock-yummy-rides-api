from math import acos, cos, radians, sin
from typing import Tuple
import random

DRIVER_FIRST_NAMES = ["Jose", "Juan", "Manuel", "Pedro"]
DRIVER_LAST_NAMES = ["Garcia", "Hernandez", "Lopez", "Perez"]


def generate_driver_data() -> Tuple[str, str, str]:
    first_name = random.choice(DRIVER_FIRST_NAMES)
    last_name = random.choice(DRIVER_LAST_NAMES)
    phone_country_code = "+58"
    phone_prefix = f"4{random.choice(['12', '14', '16', '24', '26'])}"
    phone_number = f"{phone_prefix}{random.randint(1000000, 9999999)}"
    return first_name, last_name, phone_country_code, phone_number
