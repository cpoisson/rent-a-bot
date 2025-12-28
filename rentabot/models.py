"""
rentabot.models
~~~~~~~~~~~~~~~

This module contains rent-a-bot in-memory resource model.
"""

import asyncio

from pydantic import BaseModel, Field


class Resource(BaseModel):
    """Resource class."""

    id: int
    name: str
    description: str = ""
    lock_token: str = Field(default="", alias="lock-token")
    lock_details: str = Field(default="Resource is available", alias="lock-details")
    endpoint: str = ""
    tags: str = ""


# In-memory storage (replaces database)
resources_by_id: dict[int, Resource] = {}
resource_lock = asyncio.Lock()
next_resource_id = 1
