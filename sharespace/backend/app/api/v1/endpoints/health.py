from fastapi import APIRouter, Response, status
from app.schemas.health import HealthResponse, ReadinessResponse
from app.services.health_service import HealthService

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check API service health",
    description="Returns basic operational health status of the FastAPI backend application.",
)
def get_health() -> HealthResponse:
    return HealthService.get_health()


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Check database and external dependency readiness",
    description="Validates connection to the configured PostgreSQL instance. Returns 503 if unavailable.",
    responses={
        200: {"description": "Database is reachable and ready."},
        503: {"description": "Database is not configured or cannot be reached."},
    },
)
async def get_readiness(response: Response) -> ReadinessResponse:
    readiness_data, is_ready = await HealthService.get_readiness()
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return readiness_data
