from fastapi import FastAPI
from app.api.routers.auth_routers import router as auth_router

app = FastAPI()

@app.get("/")
async def health_check():
    return {"message": "server up and running"}

app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["api-auth"]
)