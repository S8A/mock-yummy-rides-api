from fastapi import FastAPI

from endpoints import router as endpoints_router

app = FastAPI(
    title="Yummy Rides - Corporate Integrations API",
    version="1.0.0"
)

app.include_router(endpoints_router)
