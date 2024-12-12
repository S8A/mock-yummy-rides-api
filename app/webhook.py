from enum import Enum

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pydantic_settings import BaseSettings
import httpx

from endpoints import TripStatusCode

router = APIRouter(
    prefix="/webhook",
    tags=["webhook"],
)


class Settings(BaseSettings):
    webhook_url: str


settings = Settings()


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


class Driver(Person):
    id: str
    unique_id: int
    location: tuple[float, float] | None = None


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


async def send_webhook(payload: WebhookPayload):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                settings.webhook_url, json=payload.model_dump_json()
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            print(e)
            raise HTTPException(
                status_code=500, detail=f"Failed to send webhook: {str(e)}"
            )


@router.post("/trip/{trip_id}/status")
async def update_trip_status(
    trip_id: str,
    status_code: TripStatusCode,
    trip_data: TripData
) -> WebhookCallResponse:
    """Send trip status update webhook"""
    payload = WebhookPayload(
        type=WebhookType.TRIP_UPDATE,
        data=trip_data
    )
    await send_webhook(payload)
    return WebhookCallResponse(
        success=True,
        message="Webhook sent successfully"
    )


@router.post("/trip/{trip_id}/cancel")
async def cancel_trip(
    trip_id: str,
    trip_data: TripData,
    by_admin: bool = False
) -> WebhookCallResponse:
    """Send trip cancellation webhook"""
    webhook_type = WebhookType.TRIP_CANCEL
    if by_admin:
        webhook_type = WebhookType.TRIP_CANCEL_BY_ADMIN
    payload = WebhookPayload(
        type=webhook_type,
        data=trip_data
    )
    await send_webhook(payload)
    return WebhookCallResponse(
        success=True,
        message="Webhook sent successfully"
    )


@router.post("/trip/{trip_id}/reassign")
async def reassign_trip(
    trip_id: str,
    trip_data: TripData,
    by_admin: bool = False
) -> WebhookCallResponse:
    """Send trip reassignment webhook"""
    webhook_type = WebhookType.TRIP_REASSIGN
    if by_admin:
        webhook_type = WebhookType.TRIP_REASSIGN_BY_ADMIN
    payload = WebhookPayload(
        type=webhook_type,
        data=trip_data
    )
    await send_webhook(payload)
    return WebhookCallResponse(
        success=True,
        message="Webhook sent successfully"
    )


@router.post("/test")
async def test_webhook(payload: WebhookPayload) -> WebhookCallResponse:
    print(payload)
    return WebhookCallResponse(
        success=True,
        message="Webhook test successful"
    )
