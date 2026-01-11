from fastapi import APIRouter
from app.api.v1 import auth, merchants, customers, invoices

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(merchants.router, prefix="/merchants", tags=["merchants"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["invoices"])

