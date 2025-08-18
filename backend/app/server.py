from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers.auth_routers import router as auth_router
from app.api.routers.order_routers import router as order_router
from app.api.routers.ws_router import router as ws_router
from app.api.routers.price_routers import router as price_router
from app.api.services.startup_service import restore_matching_engine_from_database


async def set_engine():
    restore_matching_engine_from_database()

app = FastAPI(
    title="Realtime Trading Platform",
    description="A high-performance trading platform with real-time order matching",
    version="1.0.0",
    on_startup=[set_engine]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def health_check():
    return {"message": "server up and running"}


# Include routers
app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

app.include_router(
    order_router,
    prefix="/api/v1/orders",
    tags=["Orders & Trading"]
)

app.include_router(
    ws_router,
    prefix="/api/v1/ws",
    tags=["websocket"]
)

app.include_router(
    price_router,
    prefix="/api/v1/prices",
    tags=["Price"]
)
