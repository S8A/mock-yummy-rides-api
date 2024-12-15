from enum import Enum
import logging
import random

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import httpx
from beanie import PydanticObjectId

from config import settings
from db import Contact, Trip, init_db
from dependencies import api_key_header
from endpoints import TripStatusCode

LOGGER = logging.getLogger("uvicorn.error")


router = APIRouter(
    prefix="/webhook",
    dependencies=[Depends(api_key_header)],
    tags=["webhook"],
)

test_router = APIRouter(
    prefix="/webhook-test",
    tags=["webhook-test"],
)


class WebhookType(Enum):
    TRIP_UPDATE = "trip_update"
    TRIP_CANCEL = "trip_cancel"
    TRIP_CANCEL_BY_ADMIN = "trip_cancel_by_admin"
    TRIP_REASSIGN = "trip_reassign"
    TRIP_REASSIGN_BY_ADMIN = "trip_reassign_by_admin"


class Location(BaseModel):
    latitude: float
    longitude: float


class Person(BaseModel):
    first_name: str
    last_name: str
    phone: str

    @classmethod
    def from_contact(cls, contact: Contact) -> "Person":
        phone = ""
        if contact.phone_country_code and contact.phone_number:
            phone = f"{contact.phone_country_code}{contact.phone_number}"

        return cls(
            first_name=contact.first_name,
            last_name=contact.last_name,
            phone=phone,
        )


class Driver(Person):
    id: str
    unique_id: int
    location: tuple[float, float] | None = None

    @classmethod
    def from_contact(cls, id: str, unique_id: int, contact: Contact) -> "Driver":
        return cls(
            id=id,
            unique_id=unique_id,
            **Person.from_contact(contact).model_dump(),
        )


class TripData(BaseModel):
    id: str
    unique_id: int
    order_id: str | None = None
    code: TripStatusCode | None = None
    sender: Person
    receiver: Person | None = None
    driver: Driver | None = None
    message: str | None = None
    quotation_id: str | None = None
    reassignment_by_admin: bool | None = None


class WebhookPayload(BaseModel):
    type: WebhookType
    data: TripData


class WebhookCallResponse(BaseModel):
    success: bool
    message: str


async def send_webhook(payload: WebhookPayload) -> httpx.Response:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                settings.WEBHOOK_URL,
                data=payload.model_dump_json(exclude_unset=True),
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            LOGGER.error(
                "send_webhook :: Failed to send webhook: %s", str(e), exc_info=True
            )
            raise HTTPException(
                status_code=500, detail=f"Failed to send webhook: {str(e)}"
            )
        LOGGER.info(
            "send_webhook :: Webhook sent successfully: %s", response.status_code
        )
        return response


@router.post("/trip/{trip_id}/status", response_model_exclude_unset=True)
async def update_trip_status(
    trip_id: str,
    status_code: TripStatusCode,
) -> WebhookCallResponse:
    """Send trip status update webhook"""
    # Initialize database connection
    await init_db()

    # Try to get the trip
    trip = await Trip.get(PydanticObjectId(trip_id))
    if not trip:
        raise HTTPException(
            status_code=404,
            detail=f"Trip {trip_id} not found"
        )

    # Update trip status
    trip.status = status_code
    await trip.save()

    # Generate deterministic unique_id using the trip's ID
    random.seed(str(trip.id))
    unique_id = random.randint(10000, 99999)

    # Convert Contact objects to Person objects
    sender = Person.from_contact(trip.sender)

    receiver = None
    if trip.receiver:
        receiver = Person.from_contact(trip.receiver)

    driver = None
    if trip.driver:
        driver = Driver.from_contact(str(trip.id), unique_id, trip.driver)

    # Create TripData from actual trip
    trip_data = TripData(
        id=str(trip.id),
        unique_id=unique_id,
        code=trip.status,
        order_id=trip.order_id,
        sender=sender,
        receiver=receiver,
        driver=driver,
    )

    # Build and send payload to webhook
    payload = WebhookPayload(
        type=WebhookType.TRIP_UPDATE,
        data=trip_data,
    )
    await send_webhook(payload)

    return WebhookCallResponse(
        success=True,
        message="Webhook sent successfully"
    )


@router.post("/trip/{trip_id}/cancel")
async def cancel_trip(
    trip_id: str,
    by_admin: bool = False
) -> WebhookCallResponse:
    """Send trip cancellation webhook"""
    mock_trip_data = TripData(
        id=trip_id,
        unique_id=123,
        sender=Person(
            first_name="John",
            last_name="Doe",
            phone="+584141234567",
        ),
    )
    webhook_type = WebhookType.TRIP_CANCEL
    if by_admin:
        webhook_type = WebhookType.TRIP_CANCEL_BY_ADMIN
    payload = WebhookPayload(
        type=webhook_type,
        data=mock_trip_data
    )
    await send_webhook(payload)
    return WebhookCallResponse(
        success=True,
        message="Webhook sent successfully"
    )


@router.post("/trip/{trip_id}/reassign")
async def reassign_trip(
    trip_id: str,
    by_admin: bool = False
) -> WebhookCallResponse:
    """Send trip reassignment webhook"""
    mock_trip_data = TripData(
        id=trip_id,
        unique_id=123,
        sender=Person(
            first_name="John",
            last_name="Doe",
            phone="+584141234567",
        ),
        message="Se está reasignando su viaje",
    )
    webhook_type = WebhookType.TRIP_REASSIGN
    if by_admin:
        webhook_type = WebhookType.TRIP_REASSIGN_BY_ADMIN
    payload = WebhookPayload(
        type=webhook_type,
        data=mock_trip_data
    )
    await send_webhook(payload)
    return WebhookCallResponse(
        success=True,
        message="Webhook sent successfully"
    )


@test_router.post("/")
async def test_webhook(payload: WebhookPayload) -> WebhookCallResponse:
    LOGGER.info(
        "test_webhook :: payload = %s",
        payload.model_dump_json(exclude_unset=True),
    )
    return WebhookCallResponse(
        success=True,
        message="Webhook test successful"
    )
