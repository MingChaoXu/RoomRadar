from fastapi import APIRouter

from hotel_spider.api.routes import health, hotels, rates, system

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(hotels.router, prefix="/hotels", tags=["hotels"])
api_router.include_router(rates.router, prefix="/rates", tags=["rates"])
