from datetime import datetime, timezone
from enum import Enum
from typing import List
import random

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from beanie import PydanticObjectId
from bson.errors import InvalidId

from db import (
    Contact,
    Currency,
    PaymentMode,
    Quotation,
    Trip,
    TripProduct,
    TripService,
    TripServiceType,
    TripStatusCode,
    TripStatusText,
    init_db,
)
from dependencies import api_key_header, get_language_header
from utils import calculate_distance_between_coordinates, generate_driver_data

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


class TripServiceData(BaseModel):
    name: str
    typename: str
    estimated_fare: float = Field(..., ge=0)
    service_type_id: str


class CreateQuotationResponseData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    eta: int
    message: str
    success: bool
    distance: float
    quotation_id: str = Field(..., alias="quotationId")
    trip_services: List[TripServiceData]


class CreateQuotationResponse(YummyResponse):
    response: CreateQuotationResponseData


class TripProductData(BaseModel):
    name: str
    image: str | None = None
    price: float | None = Field(None, ge=0)
    quantity: int = Field(..., gt=0)
    currency_code: Currency | None = None


class StoreDetail(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    store_fav_icon: str | None = Field(None, alias="storeFavIcon")
    store_alias_name: str = Field(..., alias="storeAliasName")
    store_image: str | None = Field(None, alias="storeImage")
    store_full_name: str = Field(..., alias="storeFullName")
    store_order_id: str | None = Field(None, alias="storeOrderId")
    store_phone: str | None = Field(None, alias="storePhone")
    store_country_phone_code: str | None = Field(None, alias="storeCountryPhoneCode")


class CreateTripRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    payer_id: str = Field(..., alias="payerId")
    payment_mode: PaymentMode = Field(..., alias="paymentMode")
    quotation_id: str = Field(..., alias="quotationId")
    store_detail: StoreDetail | None = Field(None, alias="storeDetail")
    trip_products: List[TripProductData] | None = Field(None, alias="tripProducts")
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
    code: str | None = None
    error_code: str
    status: int
    response: ErrorResponseData


class YummyHTTPException(HTTPException):
    """Custom exception for Yummy-style error responses"""

    def __init__(
        self,
        status_code: int,
        name: str,
        path: str,
        method: str,
        message: str,
        req_body: dict | None = None,
        error_description: list[str] | None = None,
    ):
        super().__init__(status_code=status_code)
        self.name = name
        self.path = path
        self.method = method
        self.message = message
        self.req_body = req_body or {}
        self.error_description = error_description or [message]


async def yummy_exception_handler(
    request: Request,
    exc: YummyHTTPException
) -> JSONResponse:
    """Handle YummyHTTPException by returning a formatted error response"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=str(exc.status_code),
            status=exc.status_code,
            response=ErrorResponseData(
                name=exc.name,
                path=exc.path,
                type="error",
                stack="",
                method=exc.method,
                message=exc.message,
                req_body=exc.req_body,
                success=False,
                timestamp=datetime.now(timezone.utc).isoformat(),
                error_description=exc.error_description,
            ),
        ).model_dump(exclude_unset=True),
    )


@router.post("/quotation/api-corporate", response_model_exclude_unset=True)
async def create_quotation(request: CreateQuotationRequest) -> CreateQuotationResponse:
    # Initialize database connection
    await init_db()

    # Calculate distance between coordinates
    distance = calculate_distance_between_coordinates(
        (request.pickup_latitude, request.pickup_longitude),
        (request.destination_latitude, request.destination_longitude)
    )

    # Calculate the ETA in seconds based on the distance and assuming 60 km/h
    # 60 km/h = 1 km/min = 1/60 km/s
    # eta = distance / (1/60)
    eta = int(distance * 60)

    # Get and filter service types based on weight
    service_types = await TripServiceType.get_or_create_standard_types()

    # If weight is specified, filter service types
    if request.weight is not None:
        service_types = service_types.find(
            TripServiceType.max_weight >= request.weight
        )

    # Create TripService documents
    trip_services = [
        TripService(
            name=st.name,
            typename=st.typename,
            estimated_fare=st.estimate_fare(distance),
            service_type_id=str(st.id)
        )
        for st in await service_types.to_list()
    ]

    # Create and save the Quotation document
    quotation = Quotation(
        eta=eta,
        distance=distance,
        trip_services=trip_services,
    )
    await quotation.insert()

    # Convert TripService documents to response models
    trip_services_data = [
        TripServiceData(
            name=ts.name,
            typename=ts.typename,
            estimated_fare=ts.estimated_fare,
            service_type_id=str(ts.service_type_id)
        )
        for ts in trip_services
    ]

    return CreateQuotationResponse(
        code="36",
        status=201,
        response=CreateQuotationResponseData(
            eta=eta,
            message="Cotizacion realizada correctamente",
            success=True,
            distance=distance,
            quotation_id=str(quotation.id),
            trip_services=trip_services_data,
        ),
    )


@router.post("/trip/api-corporate", response_model_exclude_unset=True)
async def create_trip(request: CreateTripRequest) -> CreateTripResponse:
    # Initialize database connection
    await init_db()

    # Try to get quotation
    quotation = None
    try:
        quotation_id = PydanticObjectId(request.quotation_id)
    except (ValueError, InvalidId):
        pass
    else:
        quotation = await Quotation.get(quotation_id)

    if not quotation:
        raise YummyHTTPException(
            status_code=404,
            name="NotFoundError",
            path="/api/v1/trip/api-corporate",
            method="POST",
            message="Quotation not found",
            req_body=request.model_dump(by_alias=True),
        )

    # Check if quotation is already in use by an active trip
    existing_trip = await Trip.find_one(
        Trip.quotation_id == str(quotation.id),
        Trip.status != TripStatusCode.CANCELLED,
    )

    if existing_trip:
        raise YummyHTTPException(
            status_code=400,
            name="ValidationError",
            path="/api/v1/trip/api-corporate",
            method="POST",
            message="Quotation already used to create a trip",
            req_body=request.model_dump(by_alias=True),
        )

    # Try to get service type
    service_type = None
    try:
        service_type_id = PydanticObjectId(request.service_type_id)
    except (ValueError, InvalidId):
        pass
    else:
        service_type = await TripServiceType.get(service_type_id)

    if not service_type:
        raise YummyHTTPException(
            status_code=404,
            name="NotFoundError",
            path="/api/v1/trip/api-corporate",
            method="POST",
            message="Service type not found",
            req_body=request.model_dump(by_alias=True),
        )

    # Validate service type exists in quotation
    if not any(
        ts.service_type_id == str(service_type.id) for ts in quotation.trip_services
    ):
        raise YummyHTTPException(
            status_code=400,
            name="ValidationError",
            path="/api/v1/trip/api-corporate",
            method="POST",
            message="Service type not available for this quotation",
            req_body=request.model_dump(by_alias=True),
        )

    # Validate cash_collected is only set for cash payments
    cash_collected = request.cash_collected
    if request.payment_mode != PaymentMode.CASH:
        cash_collected = None

    # Create sender Contact from store details or user details
    sender = Contact(
        first_name=request.user_first_name or "",
        last_name=request.user_last_name or "",
        phone_country_code=request.user_country_phone_code,
        phone_number=request.user_phone_number,
    )

    if request.store_detail:
        sender.is_store = True
        sender.store_full_name = request.store_detail.store_full_name
        sender.store_alias = request.store_detail.store_alias_name
        sender.store_image = request.store_detail.store_image
        sender.store_favicon = request.store_detail.store_fav_icon

    # Create receiver Contact
    receiver = Contact(
        first_name=request.receiver_first_name,
        last_name=request.receiver_last_name,
        phone_country_code=request.receiver_country_phone_code,
        phone_number=request.receiver_phone_number,
    )

    # Create driver Contact with random name
    (
        driver_first_name,
        driver_last_name,
        driver_phone_country_code,
        driver_phone_number
    ) = generate_driver_data()
    driver = Contact(
        first_name=driver_first_name,
        last_name=driver_last_name,
        phone_country_code=driver_phone_country_code,
        phone_number=driver_phone_number,
    )

    # Create trip products if provided
    trip_products = None
    if request.trip_products:
        trip_products = [
            TripProduct(
                name=product.name,
                image=product.image,
                price=product.price,
                quantity=product.quantity,
                currency_code=product.currency_code,
            )
            for product in request.trip_products
        ]

    # Create and save the Trip
    trip = Trip(
        status=TripStatusCode.ACCEPTED,
        payer_id=request.payer_id,
        payment_mode=request.payment_mode,
        quotation_id=str(quotation.id),
        service_type_id=str(service_type.id),
        order_id=request.partner_order_id,
        source_address=request.source_address,
        destination_address=request.destination_address,
        sender=sender,
        receiver=receiver,
        driver=driver,
        trip_source=request.trip_source,
        trip_products=trip_products,
        total_order_price=request.total_order_price,
        cash_collected=cash_collected,
        tip_amount=request.tip_amount,
    )
    await trip.insert()

    # Generate a deterministic unique_id using the trip's ID as seed
    random.seed(str(trip.id))
    unique_id = random.randint(10000, 99999)

    return CreateTripResponse(
        code="9",
        status=201,
        response=CreateTripResponseData(
            message="Viaje creado correctamente",
            success=True,
            trip_id=str(trip.id),
            trip_unique_id=unique_id
        ),
    )


@router.get("/trip/api-status-by-corporate/{id}", response_model_exclude_unset=True)
async def get_trip_status(id: str) -> GetStatusTripResponse:
    # Initialize database connection
    await init_db()

    # Try to get the trip
    trip = None
    try:
        trip_id = PydanticObjectId(id)
    except (ValueError, InvalidId):
        pass
    else:
        trip = await Trip.get(trip_id)

    if not trip:
        raise YummyHTTPException(
            status_code=404,
            name="NotFoundError",
            path=f"/api/v1/trip/api-status-by-corporate/{id}",
            method="GET",
            message="Trip not found",
        )

    # Generate deterministic unique_id using the trip's ID
    random.seed(str(trip.id))
    unique_id = random.randint(10000, 99999)

    return GetStatusTripResponse(
        code="10",
        status=200,
        response=GetStatusTripResponseData(
            message="Status del viaje obtenido con éxito",
            success=True,
            trip=TripStatusData(
                id=str(trip.id),
                unique_id=unique_id,
                status_code=trip.status,
                status_text=trip.get_status_text().value
            )
        ),
    )


@router.post("/trip/external-cancel-trip", response_model_exclude_unset=True)
async def cancel_trip_by_external(request: CancelTripRequest) -> CancelTripResponse:
    # Initialize database connection
    await init_db()

    # Try to get the trip
    trip = None
    try:
        trip_id = PydanticObjectId(request.trip_id)
    except (ValueError, InvalidId):
        pass
    else:
        trip = await Trip.get(trip_id)

    if not trip:
        raise YummyHTTPException(
            status_code=404,
            name="NotFoundError",
            path="/api/v1/trip/external-cancel-trip",
            method="POST",
            message="Trip not found",
            req_body=request.model_dump(by_alias=True),
        )

    # Check if trip can be cancelled
    if trip.status in [
        TripStatusCode.CANCELLED,
        TripStatusCode.TRIP_COMPLETED,
        TripStatusCode.DRIVER_ARRIVED_TO_DESTINATION,
    ]:
        raise YummyHTTPException(
            status_code=400,
            name="ValidationError",
            path="/api/v1/trip/external-cancel-trip",
            method="POST",
            message="Trip cannot be cancelled in its current state",
            req_body=request.model_dump(by_alias=True),
        )

    # Update trip status to cancelled
    trip.status = TripStatusCode.CANCELLED
    await trip.save()

    return CancelTripResponse(
        code="11",
        status=200,
        response=CancelTripResponseData(
            payment_method=trip.payment_mode,
            payment_status=1,
            message="Tu viaje ha sido cancelado exitosamente",
            success=True
        ),
    )


@router.post("/payment-trip/pay-payment-b2b", response_model_exclude_unset=True)
async def force_trip_complete_by_external(
    request: ForceTripCompleteRequest
) -> ForceTripCompleteResponse:
    # Initialize database connection
    await init_db()

    # Try to get the trip
    trip = None
    try:
        trip_id = PydanticObjectId(request.trip_id)
    except (ValueError, InvalidId):
        pass
    else:
        trip = await Trip.get(trip_id)

    if not trip:
        raise YummyHTTPException(
            status_code=404,
            name="NotFoundError",
            path="/api/v1/payment-trip/pay-payment-b2b",
            method="POST",
            message="Trip not found",
            req_body=request.model_dump(by_alias=True),
        )

    # Update trip status to completed
    trip.status = TripStatusCode.TRIP_COMPLETED
    await trip.save()

    return ForceTripCompleteResponse(
        status=200,
        response=ForceTripCompleteResponseData(
            payment_status=1,
            message="Tu viaje ha sido completado correctamente",
            success=True
        ),
    )
