"""API v1 routes package."""
from fastapi import APIRouter

from app.api.v1 import auth, users

# Create v1 API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])

__all__ = ["api_router"]
