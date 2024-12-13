from fastapi import FastAPI

from endpoints import router as endpoints_router
from webhook import router as webhook_router
from webhook import test_router as webhook_test_router

app = FastAPI(
    title="Yummy Rides - Corporate Integrations API",
    version="1.0.0"
)

app.include_router(endpoints_router)
app.include_router(webhook_router)
app.include_router(webhook_test_router)
