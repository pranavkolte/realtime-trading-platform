from fastapi import FastAPI
from app.api.routers.auth_routers import router as auth_router
from app.api.routers.order_routers import router as order_router

app = FastAPI(
    title="Realtime Trading Platform",
    description="A high-performance trading platform with real-time order matching",
    version="1.0.0"
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