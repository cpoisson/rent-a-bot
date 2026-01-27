"""
rentabot.controllers
~~~~~~~~~~~~~~~~~~~~

This module contains rent-a-bot functions related to in-memory resource manipulation.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import yaml

from rentabot.exceptions import (
    InvalidLockToken,
    InvalidTTL,
    ResourceAlreadyLocked,
    ResourceAlreadyUnlocked,
    ResourceDescriptorIsEmpty,
    ResourceNotFound,
)
from rentabot.logger import get_logger
from rentabot.models import (
    Resource,
    resource_lock,
    resources_by_id,
)

logger = get_logger(__name__)


def get_all_resources() -> list[Resource]:
    """Returns a list of resources."""
    return list(resources_by_id.values())


def get_resource_from_id(resource_id: int) -> Resource:
    """Returns a Resource object given it's id.

    Args:
        resource_id: the index of the resource.

    Returns:
        A Resource object.
    """
    resource = resources_by_id.get(resource_id)

    if resource is None:
        logger.warning(f"Resource not found. Id : {resource_id}")
        raise ResourceNotFound(message="Resource not found", payload={"resource_id": resource_id})
    return resource


def get_resources_from_tags(resource_tags: list[str]) -> list[Resource]:
    """Returns a Resource object list given their tags.

    Args:
        resource_tags: the tags of the resource we are looking for.

    Returns:
        A Resource object.
    """
    all_resources = get_all_resources()
    resources = []

    for resource in all_resources:
        if not resource.tags:
            continue
        # Parse comma-separated tags and strip whitespace
        parsed_tags = [tag.strip() for tag in resource.tags.split(",") if tag.strip()]
        if set(parsed_tags).intersection(set(resource_tags)) == set(resource_tags):
            resources.append(resource)

    if not resources:
        logger.warning(f"Resources not found. Tag(s) : {resource_tags}")
        raise ResourceNotFound(
            message="No resource found matching the tag(s)", payload={"tags": resource_tags}
        )
    return resources


async def lock_resource(resource_id: int, ttl: int = 3600) -> tuple[str, Resource]:
    """Lock a specific resource by ID.

    Args:
        resource_id: The ID of the resource to lock.
        ttl: Time-to-live in seconds (default: 3600 = 1 hour).

    Returns:
        tuple: (lock_token, updated_resource)

    Raises:
        ResourceNotFound: If resource doesn't exist.
        ResourceAlreadyLocked: If resource is already locked.
        InvalidTTL: If TTL exceeds max_lock_duration.
    """
    async with resource_lock:
        resource = get_resource_from_id(resource_id)

        if resource.lock_token:
            logger.warning(f"Resource already locked. Id: {resource_id}")
            raise ResourceAlreadyLocked(
                message="Cannot lock the requested resource, resource is already locked",
                payload={"resource_id": resource_id},
            )

        # Validate TTL against max_lock_duration
        if ttl > resource.max_lock_duration:
            raise InvalidTTL(
                message=f"Requested TTL ({ttl}s) exceeds maximum allowed duration ({resource.max_lock_duration}s)",
                payload={
                    "resource_id": resource_id,
                    "requested_ttl": ttl,
                    "max_lock_duration": resource.max_lock_duration,
                },
            )

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl)

        updated_resource = resource.model_copy(
            update={
                "lock_token": str(uuid4()),
                "lock_details": "Resource locked",
                "lock_acquired_at": now,
                "lock_expires_at": expires_at,
            }
        )

        resources_by_id[updated_resource.id] = updated_resource
        logger.info(
            f"Resource locked. Id: {updated_resource.id}, TTL: {ttl}s, Expires: {expires_at.isoformat()}"
        )

        return updated_resource.lock_token, updated_resource


async def unlock_resource(resource_id: int, lock_token: str | None) -> None:
    """Unlock resource. Raise an exception if the token is invalid or if the resource is already unlocked.

    Args:
        resource_id (int): The id of the resource to unlock.
        lock_token (str): The lock token to authorize the unlock.

    Returns:
        None
    """
    resource = get_resource_from_id(resource_id)

    if not resource.lock_token:
        logger.warning(f"Resource already unlocked. Id : {resource_id}")
        raise ResourceAlreadyUnlocked(
            message="Resource is already unlocked", payload={"resource_id": resource_id}
        )
    if lock_token != resource.lock_token:
        msg = f"Incorrect lock token. Id : {resource_id}, lock-token : {lock_token}, resource lock-token : {resource.lock_token}"
        logger.warning(msg)
        raise InvalidLockToken(
            message="Cannot unlock resource, the lock token is not valid.",
            payload={
                "resource": resource.model_dump(by_alias=True, mode="json"),
                "invalid-lock-token": lock_token,
            },
        )

    updated_resource = resource.model_copy(
        update={
            "lock_token": "",
            "lock_details": "Resource available",
            "lock_acquired_at": None,
            "lock_expires_at": None,
        }
    )

    resources_by_id[updated_resource.id] = updated_resource

    logger.info(f"Resource unlocked. Id : {resource_id}")


async def extend_resource_lock(resource_id: int, lock_token: str, additional_ttl: int) -> Resource:
    """Extend the lock duration for a locked resource.

    Args:
        resource_id: The ID of the resource to extend.
        lock_token: The lock token to authorize the extension.
        additional_ttl: Additional time in seconds to add to the lock.

    Returns:
        Updated resource with new expiration time.

    Raises:
        ResourceNotFound: If resource doesn't exist.
        ResourceAlreadyUnlocked: If resource is not locked.
        InvalidLockToken: If lock token is invalid.
        InvalidTTL: If extension would exceed max_lock_duration.
    """
    async with resource_lock:
        resource = get_resource_from_id(resource_id)

        # Check if resource is locked
        if not resource.lock_token:
            logger.warning(f"Cannot extend unlocked resource. Id: {resource_id}")
            raise ResourceAlreadyUnlocked(
                message="Cannot extend lock on unlocked resource",
                payload={"resource_id": resource_id},
            )

        # Validate lock token
        if lock_token != resource.lock_token:
            logger.warning(
                f"Invalid lock token for extension. Id: {resource_id}, Token: {lock_token}"
            )
            raise InvalidLockToken(
                message="Cannot extend lock, the lock token is not valid.",
                payload={
                    "resource": resource.model_dump(by_alias=True, mode="json"),
                    "invalid-lock-token": lock_token,
                },
            )

        # Calculate total lock duration that will result
        now = datetime.now(timezone.utc)
        new_expires_at = now + timedelta(seconds=additional_ttl)

        # Calculate what the total duration would be
        if resource.lock_acquired_at is not None:
            total_duration = int((new_expires_at - resource.lock_acquired_at).total_seconds())
        else:
            # Shouldn't happen, but handle gracefully
            total_duration = additional_ttl

        # Validate against max_lock_duration
        if total_duration > resource.max_lock_duration:
            logger.warning(
                f"Extension would exceed max duration. Id: {resource_id}, "
                f"Total: {total_duration}s, Max: {resource.max_lock_duration}s"
            )
            raise InvalidTTL(
                message=f"Total lock duration ({total_duration}s) would exceed maximum allowed ({resource.max_lock_duration}s)",
                payload={
                    "resource_id": resource_id,
                    "total_duration": total_duration,
                    "max_lock_duration": resource.max_lock_duration,
                    "additional_ttl": additional_ttl,
                },
            )

        # Update resource with new expiration
        updated_resource = resource.model_copy(update={"lock_expires_at": new_expires_at})

        resources_by_id[updated_resource.id] = updated_resource
        logger.info(
            f"Lock extended. Id: {updated_resource.id}, "
            f"Additional TTL: {additional_ttl}s, New expiration: {new_expires_at.isoformat()}"
        )

        return updated_resource


async def auto_expire_locks() -> None:
    """Background task to automatically expire locks that have exceeded their TTL.

    Runs periodically to check all locked resources and unlock those that have expired.
    """
    while True:
        try:
            await asyncio.sleep(10)  # Check every 10 seconds

            now = datetime.now(timezone.utc)
            expired_resources = []

            # Find expired locks
            for resource in resources_by_id.values():
                if (
                    resource.lock_token
                    and resource.lock_expires_at is not None
                    and resource.lock_expires_at <= now
                ):
                    expired_resources.append(resource)

            # Unlock expired resources
            for resource in expired_resources:
                async with resource_lock:
                    # Re-check in case it was unlocked/extended during iteration
                    current = resources_by_id.get(resource.id)
                    if (
                        current
                        and current.lock_token
                        and current.lock_expires_at is not None
                        and current.lock_expires_at <= now
                    ):
                        updated = current.model_copy(
                            update={
                                "lock_token": "",
                                "lock_details": f"Auto-expired at {now.isoformat()}",
                                "lock_acquired_at": None,
                                "lock_expires_at": None,
                            }
                        )
                        resources_by_id[updated.id] = updated
                        logger.info(
                            f"Lock auto-expired. Id: {updated.id}, "
                            f"Expired at: {current.lock_expires_at.isoformat()}"
                        )

        except Exception as e:
            logger.error(f"Error in auto_expire_locks task: {e}", exc_info=True)


def populate_database_from_file(resource_descriptor: str) -> list[str]:
    """Populate the in-memory storage using the resources described in a yaml file.

    Args:
      resource_descriptor (str): the resource descriptor.

    Returns:
        (list) resources name added

    """
    logger.info(f"Populating resources from descriptor : {resource_descriptor}")

    with open(resource_descriptor) as f:
        resources = yaml.load(f, Loader=yaml.SafeLoader)

    if resources is None:
        raise ResourceDescriptorIsEmpty(resource_descriptor)

    import rentabot.models
    from rentabot.models import resources_by_id

    resources_by_id.clear()
    rentabot.models.next_resource_id = 1

    for resource_name in list(resources):
        logger.debug(f"Add resource : {resource_name}")

        description = resources[resource_name].get("description", "")
        endpoint = resources[resource_name].get("endpoint", "")
        tags = resources[resource_name].get("tags", "")

        resource = Resource(
            id=rentabot.models.next_resource_id,
            name=resource_name,
            description=description,
            endpoint=endpoint,
            tags=tags,
        )

        resources_by_id[resource.id] = resource
        rentabot.models.next_resource_id += 1

    return list(resources)
