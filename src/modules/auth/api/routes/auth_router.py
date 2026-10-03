from fastapi import APIRouter

from src.modules.auth.api.routes import register_user_router

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Auth"],
)

router.include_router(register_user_router.router)
