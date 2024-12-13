from typing import Annotated, List
from math import sqrt

from beanie import Document, Indexed, init_beanie
from beanie.operators import In
from beanie.odm.queries.find import FindMany
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import Field

from config import settings


async def init_db():
    """Initialize database connection and models"""
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client[settings.MONGODB_DB_NAME],
        document_models=[TripServiceType]
    )


class TripServiceType(Document):
    name: Annotated[str, Indexed(unique=True)]
    typename: str
    max_weight: float = Field(ge=0)

    @classmethod
    async def get_or_create_standard_types(cls) -> FindMany["TripServiceType"]:
        """Get or create the standard Yummy Rides service types."""
        standard_types = [
            {
                "name": "Estandar M",
                "typename": "Mandaditos",
                "max_weight": 5.0,
            },
            {
                "name": "XL",
                "typename": "Mandaditos XL",
                "max_weight": 30.0,
            },
            {
                "name": "XXL",
                "typename": "Mandaditos XXL",
                "max_weight": 180.0,
            },
        ]

        # Get all existing service types in one query
        standard_types_names = [t["name"] for t in standard_types]
        existing_types = await cls.find(In(cls.name, standard_types_names)).to_list()
        existing_names = [st.name for st in existing_types]

        # Create missing types in a single batch
        to_create = []
        for type_data in standard_types:
            if type_data["name"] not in existing_names:
                service_type = cls(**type_data)
                to_create.append(service_type)

        if to_create:
            await cls.insert_many(to_create)

        # Get all service types again to ensure we have all
        service_types = cls.find(
            In(cls.name, standard_types_names)
        ).sort(+cls.max_weight)

        return service_types

    def estimate_fare(self, distance: float) -> float:
        """Estimate fare based on distance (km) and service type's max weight."""
        return round(distance * sqrt(self.max_weight) * 0.10, 2)
