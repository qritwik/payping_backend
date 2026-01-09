from fastapi import APIRouter
from app.api.v1 import auth, merchants

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(merchants.router, prefix="/merchants", tags=["merchants"])

