# -*- coding: utf-8 -*-
"""
rentabot.models
~~~~~~~~~~~~~~~

This module contains rent-a-bot in-memory resource model.
"""

from pydantic import BaseModel
from typing import Optional
import threading


class Resource(BaseModel):
    """Resource class."""

    id: int
    name: str
    description: Optional[str] = None
    lock_token: Optional[str] = None
    lock_details: str = "Resource is available"
    endpoint: Optional[str] = None
    tags: Optional[str] = None

    @property
    def dict(self):
        """Compatibility property for existing code."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "lock-token": self.lock_token,
            "lock-details": self.lock_details,
            "endpoint": self.endpoint,
            "tags": self.tags,
        }


# In-memory storage (replaces database)
resources_by_id: dict[int, Resource] = {}
resources_by_name: dict[str, Resource] = {}
resource_lock = threading.Lock()
next_resource_id = 1
