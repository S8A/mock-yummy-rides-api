from enum import Enum, IntEnum
from typing import List
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, ConfigDict

from db import TripServiceType, init_db
from dependencies import api_key_header, get_language_header
from utils import calculate_distance_between_coordinates

router = APIRouter(
    prefix="/api/v1",
    dependencies=[Depends(api_key_header), Depends(get_language_header)],
    tags=["endpoints"]
)


class YummyResponse(BaseModel):
    code: str
    response: dict
    status: int


class CreateQuotationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    destination_latitude: float = Field(
        ..., alias="destinationLatitude", ge=-90, le=90
    )
    destination_longitude: float = Field(
        ..., alias="destinationLongitude", ge=-180, le=180
    )
    pickup_latitude: float = Field(..., alias="pickupLatitude", ge=-90, le=90)
    pickup_longitude: float = Field(..., alias="pickupLongitude", ge=-180, le=180)
    weight: float | None = Field(None, ge=0)


class TripService(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    typename: str
    estimated_fare: float = Field(..., ge=0)
    service_type_id: str = Field(..., alias="serviceTypeId")


class CreateQuotationResponseData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    eta: int
    message: str
    success: bool
    distance: float
    quotation_id: str = Field(..., alias="quotationId")
    trip_services: List[TripService]


class CreateQuotationResponse(YummyResponse):
    response: CreateQuotationResponseData


class Currency(Enum):
    BS = "BS"
    USD = "USD"


class TripProduct(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    image: str | None = None
    price: float | None = Field(None, ge=0)
    quantity: int = Field(..., gt=0)
    currency_code: Currency | None = Field(None, alias="currencyCode")


class StoreDetail(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    store_fav_icon: str | None = Field(None, alias="storeFavIcon")
    store_alias_name: str = Field(..., alias="storeAliasName")
    store_image: str | None = Field(None, alias="storeImage")
    store_full_name: str = Field(..., alias="storeFullName")
    store_order_id: str | None = Field(None, alias="storeOrderId")
    store_phone: str | None = Field(None, alias="storePhone")
    store_country_phone_code: str | None = Field(None, alias="storeCountryPhoneCode")


class PaymentMode(IntEnum):
    CASH = 1
    POS = 4
    DEFAULT = 7


class CreateTripRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    payer_id: str = Field(..., alias="payerId")
    payment_mode: PaymentMode = Field(..., alias="paymentMode")
    quotation_id: str = Field(..., alias="quotationId")
    store_detail: StoreDetail | None = Field(None, alias="storeDetail")
    trip_products: List[TripProduct] | None = Field(None, alias="tripProducts")
    service_type_id: str = Field(..., alias="serviceTypeId")
    source_address: str = Field(..., alias="sourceAddress")
    destination_address: str = Field(..., alias="destinationAddress")
    partner_order_id: str | None = Field(None, alias="partnerOrderId")
    user_first_name: str | None = Field(None)
    user_last_name: str | None = Field(None)
    user_country_phone_code: str | None = Field(None)
    user_phone_number: str | None = Field(None)
    receiver_first_name: str
    receiver_last_name: str
    receiver_country_phone_code: str
    receiver_phone_number: str
    receiver_picture: str | None = Field(None, alias="receiverPicture")
    trip_source: str | None = Field(None, alias="tripSource")
    total_order_price: float | None = Field(None, alias="totalOrderPrice", ge=0)
    cash_collected: float | None = Field(None, alias="cashCollected", ge=0)
    tip_amount: float | None = Field(None, alias="tipAmount", ge=0)


class CreateTripResponseData(BaseModel):
    message: str
    success: bool
    trip_id: str
    trip_unique_id: int


class CreateTripResponse(YummyResponse):
    response: CreateTripResponseData


class TripStatusCode(IntEnum):
    CANCELLED = 0
    ACCEPTED = 1
    DRIVER_ON_THE_WAY = 2
    DRIVER_ARRIVED_TO_PICKUP = 4
    DRIVER_ON_THE_WAY_TO_DESTINATION = 6
    DRIVER_ARRIVED_TO_DESTINATION = 8
    TRIP_COMPLETED = 9


class TripStatusText(Enum):
    CANCELLED = "Cancelado"
    ACCEPTED = "Aceptado"
    DRIVER_ON_THE_WAY = "En camino"
    DRIVER_ARRIVED_TO_PICKUP = "Primera parada"
    DRIVER_ON_THE_WAY_TO_DESTINATION = "En camino a destino"
    DRIVER_ARRIVED_TO_DESTINATION = "Llegó a destino"
    TRIP_COMPLETED = "Completado"


class TripStatusData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id")
    unique_id: int
    status_code: TripStatusCode = Field(..., alias="statusCode")
    status_text: TripStatusText = Field(..., alias="statusText")


class GetStatusTripResponseData(BaseModel):
    message: str
    success: bool
    trip: TripStatusData


class GetStatusTripResponse(YummyResponse):
    response: GetStatusTripResponseData


class CancelTripRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    trip_id: str = Field(..., alias="tripId")
    cancel_reason: str | None = Field(None, alias="cancelReason")


class CancelTripResponseData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    message: str
    success: bool
    payment_method: int = Field(..., alias="paymentMethod")
    payment_status: int = Field(..., alias="paymentStatus")


class CancelTripResponse(YummyResponse):
    response: CancelTripResponseData


class ForceTripCompleteRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    trip_id: str = Field(..., alias="tripId")
    force_b2b: bool = Field(..., alias="forceB2B")


class ForceTripCompleteResponseData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    message: str
    success: bool
    payment_status: int = Field(..., alias="paymentStatus")


class ForceTripCompleteResponse(YummyResponse):
    code: str | None = None
    response: ForceTripCompleteResponseData


class ErrorResponseData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    path: str
    type: str
    stack: str
    method: str
    message: str
    req_body: dict = Field(..., alias="reqBody")
    success: bool
    timestamp: str
    error_description: list[str]


class ErrorResponse(YummyResponse):
    error_code: str
    status: int
    response: ErrorResponseData


@router.post("/quotation/api-corporate", response_model_exclude_unset=True)
async def create_quotation(request: CreateQuotationRequest) -> CreateQuotationResponse:
    # Initialize database connection
    await init_db()

    # Calculate distance between coordinates
    distance = calculate_distance_between_coordinates(
        (request.pickup_latitude, request.pickup_longitude),
        (request.destination_latitude, request.destination_longitude)
    )

    # Get and filter service types based on weight
    service_types = await TripServiceType.get_or_create_standard_types()

    # If weight is specified, filter service types
    if request.weight is not None:
        service_types = service_types.find(
            TripServiceType.max_weight >= request.weight
        )

    # Convert to list and create TripService objects
    trip_services = [
        TripService(
            name=st.name,
            typename=st.typename,
            estimated_fare=st.estimate_fare(distance),
            service_type_id=str(st.id)
        )
        for st in await service_types.to_list()
    ]

    return CreateQuotationResponse(
        code="36",
        status=201,
        response=CreateQuotationResponseData(
            eta=828,
            message="Cotizacion realizada correctamente",
            success=True,
            distance=distance,
            quotation_id=str(uuid.uuid4()).replace("-", ""),
            trip_services=trip_services
        ),
    )


@router.post("/trip/api-corporate", response_model_exclude_unset=True)
async def create_trip(request: CreateTripRequest) -> CreateTripResponse:
    trip_id = str(uuid.uuid4()).replace("-", "")
    return CreateTripResponse(
        code="9",
        status=201,
        response=CreateTripResponseData(
            message="Viaje creado correctamente",
            success=True,
            trip_id=trip_id,
            trip_unique_id=29714
        ),
    )


@router.get("/trip/api-status-by-corporate/{id}", response_model_exclude_unset=True)
async def get_trip_status(id: str) -> GetStatusTripResponse:
    return GetStatusTripResponse(
        code="10",
        status=200,
        response=GetStatusTripResponseData(
            message="Status del viaje obtenido con éxito",
            success=True,
            trip=TripStatusData(
                id=id,
                unique_id=656,
                status_code=TripStatusCode.DRIVER_ON_THE_WAY,
                status_text=TripStatusText.DRIVER_ON_THE_WAY,
            )
        ),
    )


@router.post("/trip/external-cancel-trip", response_model_exclude_unset=True)
async def cancel_trip_by_external(request: CancelTripRequest) -> CancelTripResponse:
    return CancelTripResponse(
        code="11",
        status=200,
        response=CancelTripResponseData(
            payment_method=1,
            payment_status=1,
            message="Tu viaje ha sido cancelado exitosamente",
            success=True
        ),
    )


@router.post("/payment-trip/pay-payment-b2b", response_model_exclude_unset=True)
async def force_trip_complete_by_external(
    request: ForceTripCompleteRequest
) -> ForceTripCompleteResponse:
    return ForceTripCompleteResponse(
        status=200,
        response=ForceTripCompleteResponseData(
            payment_status=1,
            message="Tu viaje ha sido completado correctamente",
            success=True
        ),
    )
