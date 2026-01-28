"""
rentabot.main
~~~~~~~~~~~~~

This module contains rent-a-bot FastAPI application.
"""

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict, Field

from rentabot import __version__
from rentabot.controllers import (
    auto_expire_locks,
    auto_fulfill_reservations,
    cancel_reservation,
    claim_reservation,
    create_reservation,
    extend_resource_lock,
    get_all_resources,
    get_reservation,
    get_resource_from_id,
    get_resources_from_tags,
    list_reservations,
    lock_resource,
    populate_database_from_file,
    unlock_resource,
)
from rentabot.exceptions import (
    ReservationException,
    ResourceAlreadyLocked,
    ResourceException,
    ResourceNotFound,
)
from rentabot.logger import get_logger

logger = get_logger(__name__)


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        descriptor = os.environ["RENTABOT_RESOURCE_DESCRIPTOR"]
        populate_database_from_file(descriptor)
        logger.info(f"Loaded resources from {descriptor}")
    except KeyError:
        logger.info(
            "No RENTABOT_RESOURCE_DESCRIPTOR environment variable set, starting with empty resources"
        )

    # Start background tasks
    expire_task = asyncio.create_task(auto_expire_locks())
    logger.info("Started auto-expire locks background task")

    fulfill_task = asyncio.create_task(auto_fulfill_reservations())
    logger.info("Started auto-fulfill reservations background task")

    yield

    # Shutdown - cancel background tasks
    expire_task.cancel()
    fulfill_task.cancel()
    try:
        await expire_task
    except asyncio.CancelledError:
        logger.info("Auto-expire locks task cancelled")
    try:
        await fulfill_task
    except asyncio.CancelledError:
        logger.info("Auto-fulfill reservations task cancelled")


# Create FastAPI app
app = FastAPI(
    title="Rent-A-Bot",
    description="Your automation resource provider",
    version=__version__,
    lifespan=lifespan,
)

# Legacy/API path constants
LEGACY_API_PREFIX = "/rentabot/api/v1.0"
NEW_API_PREFIX = "/api/v1"


# Middleware: Deprecation warning and optional redirect for legacy API paths
@app.middleware("http")
async def legacy_api_migration_middleware(request: Request, call_next):
    path = request.url.path
    if path.startswith(LEGACY_API_PREFIX):
        # Compose new path preserving the suffix and query
        suffix = path[len(LEGACY_API_PREFIX) :]
        new_path = f"{NEW_API_PREFIX}{suffix}"
        query = request.url.query

        # Log deprecation warning
        logger.warning(f"Using deprecated API path '{path}'. Please migrate to '{new_path}'.")

        # Optional redirect controlled via environment variable
        redirect_enabled = os.getenv("RENTABOT_LEGACY_REDIRECT", "0").lower() in {
            "1",
            "true",
            "yes",
        }
        if redirect_enabled:
            target = new_path if not query else f"{new_path}?{query}"
            return RedirectResponse(url=target, status_code=307)

        # Proceed and attach deprecation headers
        response = await call_next(request)
        try:
            response.headers["Deprecation"] = "true"
            response.headers["Link"] = f"<{new_path}>; rel=alternate"
            # Optional 'Sunset' header could be added when date is determined
        except Exception:
            pass
        return response

    # Non-legacy paths: proceed as usual
    return await call_next(request)


# Setup templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))


# Response models
class ResourceResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    lock_token: Optional[str] = None
    lock_details: str
    endpoint: Optional[str] = None
    tags: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "coffee-machine",
                "description": "Kitchen coffee machine",
                "lock_token": "",
                "lock_details": "Resource is available",
                "endpoint": "tcp://192.168.1.50",
                "tags": "coffee kitchen food",
            }
        }
    )


class ResourcesListResponse(BaseModel):
    resources: list[dict]


class LockResponse(BaseModel):
    message: str
    lock_token: str = Field(alias="lock-token")
    resource: dict
    locked_at: Optional[datetime] = Field(None, alias="locked-at")
    expires_at: Optional[datetime] = Field(None, alias="expires-at")

    model_config = ConfigDict(populate_by_name=True)


class UnlockResponse(BaseModel):
    message: str


class LockRequest(BaseModel):
    ttl: Optional[int] = 3600  # Default 1 hour


class ExtendRequest(BaseModel):
    lock_token: str = Field(alias="lock-token")
    additional_ttl: int = Field(alias="additional-ttl")

    model_config = ConfigDict(populate_by_name=True)


class ExtendResponse(BaseModel):
    message: str
    new_expires_at: datetime = Field(alias="new-expires-at")
    total_lock_duration: int = Field(alias="total-lock-duration")

    model_config = ConfigDict(populate_by_name=True)


# Reservation models
class CreateReservationRequest(BaseModel):
    tags: list[str]
    quantity: int = Field(gt=0)
    max_wait_time: Optional[int] = Field(default=3600, gt=0)
    ttl: Optional[int] = Field(default=3600, gt=0)


class ReservationResponse(BaseModel):
    reservation_id: str
    status: str
    tags: list[str]
    quantity: int
    position_in_queue: Optional[int] = None
    created_at: datetime
    expires_at: datetime
    fulfilled_at: Optional[datetime] = None
    claim_expires_at: Optional[datetime] = None
    claimed_at: Optional[datetime] = None
    resource_ids: list[int] = []
    lock_tokens: list[str] = []


class ReservationsListResponse(BaseModel):
    reservations: list[ReservationResponse]


# - [ Web View ] --------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Display all resources in HTML format."""
    resources = get_all_resources()
    return templates.TemplateResponse(
        request=request, name="display_resources.html", context={"resources": resources}
    )


# - [ Health & Status ] -------------------------------------------------------


@app.get("/health")
async def health():
    """
    Health check endpoint for monitoring.

    Returns 200 OK if the service is running.
    Useful for basic uptime monitoring and load balancer health checks.
    """
    return {"status": "ok"}


@app.get("/readiness")
async def readiness():
    """
    Readiness check endpoint for Kubernetes.

    Returns 200 OK if the service is ready to accept traffic.
    Kubernetes uses this to determine if the pod should receive requests.
    """
    return {"status": "ready"}


# - [ API ] ------------------------------------------------------------------

# - [ GET : Access to resources information ]


@app.get("/rentabot/api/v1.0/resources", response_model=ResourcesListResponse)
@app.get("/api/v1/resources", response_model=ResourcesListResponse)
async def get_resources():
    """Get all resources."""
    resources = [
        resource.model_dump(by_alias=True, mode="json") for resource in get_all_resources()
    ]
    return {"resources": resources}


@app.get("/rentabot/api/v1.0/resources/{resource_id}")
@app.get("/api/v1/resources/{resource_id}")
async def get_resource(resource_id: int):
    """Get a specific resource by ID."""
    resource = get_resource_from_id(resource_id)
    return {"resource": resource.model_dump(by_alias=True, mode="json")}


# - [ POST : Acquire and release resource lock ] ------------------------------


@app.post("/rentabot/api/v1.0/resources/{resource_id}/lock")
@app.post("/api/v1/resources/{resource_id}/lock")
async def lock_by_id(resource_id: int, request: Optional[LockRequest] = None):
    """Lock a resource by ID with optional TTL."""
    ttl = request.ttl if request and request.ttl is not None else 3600
    lock_token, resource = await lock_resource(resource_id, ttl=ttl)
    return {
        "message": "Resource locked",
        "lock-token": lock_token,
        "resource": resource.model_dump(by_alias=True, mode="json"),
        "locked-at": resource.lock_acquired_at,
        "expires-at": resource.lock_expires_at,
    }


@app.post("/rentabot/api/v1.0/resources/{resource_id}/unlock")
@app.post("/api/v1/resources/{resource_id}/unlock")
async def unlock_by_id(
    resource_id: int, lock_token: Optional[str] = Query(None, alias="lock-token")
):
    """Unlock a resource by ID."""
    await unlock_resource(resource_id, lock_token)
    return {"message": "Resource unlocked"}


@app.post("/rentabot/api/v1.0/resources/{resource_id}/extend")
@app.post("/api/v1/resources/{resource_id}/extend")
async def extend_lock(
    resource_id: int,
    lock_token: str = Query(alias="lock-token"),
    additional_ttl: int = Query(alias="additional-ttl"),
):
    """Extend the lock duration for a locked resource."""
    resource = await extend_resource_lock(resource_id, lock_token, additional_ttl)

    # Calculate total lock duration
    if resource.lock_acquired_at and resource.lock_expires_at:
        total_duration = int((resource.lock_expires_at - resource.lock_acquired_at).total_seconds())
    else:
        total_duration = additional_ttl

    return {
        "message": "Lock extended",
        "new-expires-at": resource.lock_expires_at,
        "total-lock-duration": total_duration,
    }


@app.post("/rentabot/api/v1.0/resources/lock")
@app.post("/api/v1/resources/lock")
async def lock_by_criterias(
    request: Optional[LockRequest] = None,
    id: Optional[int] = Query(None),
    name: Optional[str] = Query(None),
    tag: Optional[list[str]] = Query(None),
):
    """Lock a resource by criteria (id, name, or tags) with optional TTL."""
    resource_id = None

    if id:
        resource_id = id
    elif name:
        resource = next((r for r in get_all_resources() if r.name == name), None)
        if resource is None:
            raise ResourceNotFound(message="Resource not found", payload={"resource_name": name})
        resource_id = resource.id
    elif tag:
        resources = get_resources_from_tags(tag)
        available = next((r for r in resources if not r.lock_token), None)
        if available is None:
            raise ResourceAlreadyLocked(
                message="No available resource found matching the tag(s)",
                payload={"tags": tag},
            )
        resource_id = available.id
    else:
        raise ResourceException(message="Bad Request")

    ttl = request.ttl if request and request.ttl is not None else 3600
    lock_token, resource = await lock_resource(resource_id, ttl=ttl)
    return {
        "message": "Resource locked",
        "lock-token": lock_token,
        "resource": resource.model_dump(by_alias=True, mode="json"),
        "locked-at": resource.lock_acquired_at,
        "expires-at": resource.lock_expires_at,
    }


# - [ API : Error Handlers ] ----------------------------------------


@app.exception_handler(ResourceException)
async def resource_exception_handler(request: Request, exc: ResourceException):
    """
    Consolidated exception handler for all ResourceException subclasses.

    Handles: ResourceNotFound, ResourceAlreadyLocked, ResourceAlreadyUnlocked, InvalidLockToken, InvalidTTL
    """
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


@app.exception_handler(ReservationException)
async def reservation_exception_handler(request: Request, exc: ReservationException):
    """
    Consolidated exception handler for all ReservationException subclasses.

    Handles: ReservationNotFound, ReservationNotFulfilled, ReservationClaimExpired,
             InsufficientResources, ReservationCannotBeCancelled
    """
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


# - [ API : Reservations ] --------------------------------------------------


@app.post("/api/v1/reservations", response_model=ReservationResponse, status_code=201)
async def create_new_reservation(req: CreateReservationRequest):
    """Create a new resource reservation."""
    reservation = await create_reservation(
        tags=req.tags,
        quantity=req.quantity,
        max_wait_time=req.max_wait_time or 3600,
        ttl=req.ttl or 3600,
    )
    return reservation.model_dump()


@app.get("/api/v1/reservations/{reservation_id}", response_model=ReservationResponse)
async def get_reservation_status(reservation_id: str):
    """Get reservation status by ID."""
    reservation = await get_reservation(reservation_id)
    return reservation.model_dump()


@app.post("/api/v1/reservations/{reservation_id}/claim", response_model=ReservationResponse)
async def claim_reservation_endpoint(reservation_id: str):
    """Claim a fulfilled reservation."""
    reservation = await claim_reservation(reservation_id)
    return reservation.model_dump()


@app.delete("/api/v1/reservations/{reservation_id}", status_code=204)
async def cancel_reservation_endpoint(reservation_id: str):
    """Cancel a pending reservation."""
    await cancel_reservation(reservation_id)
    return None


@app.get("/api/v1/reservations", response_model=ReservationsListResponse)
async def list_all_reservations():
    """List all active reservations."""
    reservations = await list_reservations()
    return {"reservations": [r.model_dump() for r in reservations]}
