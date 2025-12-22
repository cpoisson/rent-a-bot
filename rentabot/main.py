"""
rentabot.main
~~~~~~~~~~~~~

This module contains rent-a-bot FastAPI application.
"""

import os
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict

from rentabot import __version__
from rentabot.controllers import (
    get_all_ressources,
    get_resource_from_id,
    lock_resource,
    populate_database_from_file,
    unlock_resource,
)
from rentabot.exceptions import (
    InvalidLockToken,
    ResourceAlreadyLocked,
    ResourceAlreadyUnlocked,
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

    yield
    # Shutdown (if needed)


# Create FastAPI app
app = FastAPI(
    title="Rent-A-Bot",
    description="Your automation resource provider",
    version=__version__,
    lifespan=lifespan,
)

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
                "lock_token": None,
                "lock_details": "Resource is available",
                "endpoint": "tcp://192.168.1.50",
                "tags": "coffee kitchen food",
            }
        }
    )


class ResourcesListResponse(BaseModel):
    resources: List[dict]


class LockResponse(BaseModel):
    message: str
    lock_token: str = Query(alias="lock-token")
    resource: dict

    model_config = ConfigDict(populate_by_name=True)


class UnlockResponse(BaseModel):
    message: str


# - [ Web View ] --------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Display all resources in HTML format."""
    resources = get_all_ressources()
    return templates.TemplateResponse(
        request=request, name="display_resources.html", context={"resources": resources}
    )


# - [ API ] ------------------------------------------------------------------

# - [ GET : Access to resources information ]


@app.get("/rentabot/api/v1.0/resources", response_model=ResourcesListResponse)
async def get_resources():
    """Get all resources."""
    resources = [resource.dict for resource in get_all_ressources()]
    return {"resources": resources}


@app.get("/rentabot/api/v1.0/resources/{resource_id}")
async def get_resource(resource_id: int):
    """Get a specific resource by ID."""
    resource = get_resource_from_id(resource_id)
    return {"resource": resource.dict}


# - [ POST : Acquire and release resource lock ]


@app.post("/rentabot/api/v1.0/resources/{resource_id}/lock")
async def lock_by_id(resource_id: int):
    """Lock a resource by ID."""
    lock_token, resource = lock_resource(rid=resource_id)
    return {"message": "Resource locked", "lock-token": lock_token, "resource": resource.dict}


@app.post("/rentabot/api/v1.0/resources/{resource_id}/unlock")
async def unlock_by_id(
    resource_id: int, lock_token: Optional[str] = Query(None, alias="lock-token")
):
    """Unlock a resource by ID."""
    unlock_resource(resource_id, lock_token)
    return {"message": "Resource unlocked"}


@app.post("/rentabot/api/v1.0/resources/lock")
async def lock_by_criterias(
    id: Optional[int] = Query(None),
    name: Optional[str] = Query(None),
    tag: Optional[List[str]] = Query(None),
):
    """Lock a resource by criteria (id, name, or tags)."""
    lock_token, resource = lock_resource(rid=id, name=name, tags=tag)
    return {"message": "Resource locked", "lock-token": lock_token, "resource": resource.dict}


# - [ API : Error Handlers ] ----------------------------------------


@app.exception_handler(ResourceException)
async def resource_exception_handler(request: Request, exc: ResourceException):
    return JSONResponse(status_code=exc.status_code, content=exc.dict)


@app.exception_handler(ResourceNotFound)
async def resource_not_found_handler(request: Request, exc: ResourceNotFound):
    return JSONResponse(status_code=exc.status_code, content=exc.dict)


@app.exception_handler(ResourceAlreadyLocked)
async def resource_already_locked_handler(request: Request, exc: ResourceAlreadyLocked):
    return JSONResponse(status_code=exc.status_code, content=exc.dict)


@app.exception_handler(ResourceAlreadyUnlocked)
async def resource_already_unlocked_handler(request: Request, exc: ResourceAlreadyUnlocked):
    return JSONResponse(status_code=exc.status_code, content=exc.dict)


@app.exception_handler(InvalidLockToken)
async def invalid_lock_token_handler(request: Request, exc: InvalidLockToken):
    return JSONResponse(status_code=exc.status_code, content=exc.dict)
