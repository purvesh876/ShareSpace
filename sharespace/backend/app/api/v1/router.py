from fastapi import APIRouter
from app.api.v1.endpoints import auth, bookings, compliance, evidence, health, organizations, resources

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(
    resources.router,
    prefix="/organizations/{organization_id}/resources",
    tags=["resources"],
)
api_router.include_router(
    bookings.router,
    prefix="/organizations/{organization_id}/bookings",
    tags=["bookings"],
)
api_router.include_router(
    compliance.router,
    prefix="/organizations/{organization_id}",
    tags=["compliance"],
)
api_router.include_router(
    evidence.router,
    prefix="/organizations/{organization_id}",
    tags=["evidence"],
)

