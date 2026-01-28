"""
rentabot.models
~~~~~~~~~~~~~~~

This module contains rent-a-bot in-memory resource model.
"""

import asyncio
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Resource(BaseModel):
    """Resource class."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    description: str = ""
    lock_token: str = Field(default="", alias="lock-token")
    lock_details: str = Field(default="Resource is available", alias="lock-details")
    endpoint: str = ""
    tags: str = ""
    lock_acquired_at: datetime | None = Field(default=None, alias="lock-acquired-at")
    lock_expires_at: datetime | None = Field(default=None, alias="lock-expires-at")
    max_lock_duration: int = Field(default=86400, alias="max-lock-duration")  # 24 hours default


class Reservation(BaseModel):
    """Represents a resource reservation in the queue."""

    model_config = ConfigDict(populate_by_name=True)

    reservation_id: str  # "res_" + UUID
    tags: list[str]  # Required tags for resources
    quantity: int = Field(gt=0)  # Number of resources needed
    ttl: int = Field(default=3600, gt=0)  # Lock TTL when claimed (seconds)

    status: str  # "pending" | "fulfilled" | "claimed" | "expired" | "cancelled"

    # Timestamps
    created_at: datetime  # When reservation was created
    expires_at: datetime  # When reservation expires if not fulfilled
    fulfilled_at: datetime | None = None  # When resources were allocated
    claim_expires_at: datetime | None = None  # 60s after fulfilled_at
    claimed_at: datetime | None = None  # When client claimed

    # Fulfillment data (set when status = fulfilled)
    resource_ids: list[int] = []  # IDs of allocated resources
    lock_tokens: list[str] = []  # Lock tokens for allocated resources

    # Queue position (computed dynamically)
    position_in_queue: int | None = None


# In-memory storage (replaces database)
resources_by_id: dict[int, Resource] = {}
resource_lock = asyncio.Lock()
next_resource_id = 1

reservations_by_id: dict[str, Reservation] = {}
reservation_lock = asyncio.Lock()
