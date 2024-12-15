from enum import Enum, IntEnum
from typing import Annotated, List
from math import sqrt

from beanie import Document, Indexed, init_beanie
from beanie.operators import In
from beanie.odm.queries.find import FindMany
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import Field

from config import settings


class Currency(str, Enum):
    BS = "BS"
    USD = "USD"


class PaymentMode(IntEnum):
    CASH = 1
    POS = 4
    DEFAULT = 7


class TripStatusCode(IntEnum):
    CANCELLED = 0
    ACCEPTED = 1
    DRIVER_ON_THE_WAY = 2
    DRIVER_ARRIVED_TO_PICKUP = 4
    DRIVER_ON_THE_WAY_TO_DESTINATION = 6
    DRIVER_ARRIVED_TO_DESTINATION = 8
    TRIP_COMPLETED = 9


class TripStatusText(str, Enum):
    CANCELLED = "Cancelado"
    ACCEPTED = "Aceptado"
    DRIVER_ON_THE_WAY = "En camino"
    DRIVER_ARRIVED_TO_PICKUP = "Primera parada"
    DRIVER_ON_THE_WAY_TO_DESTINATION = "En camino a destino"
    DRIVER_ARRIVED_TO_DESTINATION = "Llegó a destino"
    TRIP_COMPLETED = "Completado"


async def init_db():
    """Initialize database connection and models"""
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client[settings.MONGODB_DB_NAME],
        document_models=[
            Contact,
            Quotation,
            Trip,
            TripProduct,
            TripService,
            TripServiceType,
        ],
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


class TripService(Document):
    name: str
    typename: str
    estimated_fare: float = Field(ge=0)
    service_type_id: str


class Quotation(Document):
    eta: int = Field(ge=0)
    distance: float = Field(ge=0)
    trip_services: List[TripService]


class Contact(Document):
    first_name: str
    last_name: str
    phone_country_code: str | None = None
    phone_number: str | None = None
    is_store: bool = False
    store_full_name: str | None = None
    store_alias: str | None = None
    store_image: str | None = None
    store_favicon: str | None = None


class TripProduct(Document):
    name: str
    image: str | None = None
    price: float | None = Field(None, ge=0)
    quantity: int = Field(..., gt=0)
    currency_code: Currency | None = None


class Trip(Document):
    status: TripStatusCode
    payer_id: str
    payment_mode: PaymentMode
    quotation_id: str
    service_type_id: str
    order_id: str | None = None
    source_address: str
    destination_address: str
    sender: Contact
    receiver: Contact
    driver: Contact | None = None
    trip_source: str | None = None
    trip_products: List[TripProduct] | None = None
    total_order_price: float | None = Field(None, ge=0)
    cash_collected: float | None = Field(None, ge=0)
    tip_amount: float | None = Field(None, ge=0)

    def get_status_text(self) -> TripStatusText:
        """Get the text representation of the trip's status."""
        return TripStatusText[TripStatusCode(self.status).name]
