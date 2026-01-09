from fastapi import FastAPI
from app.core.database import engine, Base
from app.core.config import settings
from app.api.v1 import api_router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for PayPing merchant management and authentication",
    version=settings.PROJECT_VERSION
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "message": "Welcome to PayPing API",
        "docs": "/docs",
        "version": settings.PROJECT_VERSION
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}

