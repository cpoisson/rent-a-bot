"""
rentabot.controllers
~~~~~~~~~~~~~~~~~~~~

This module contains rent-a-bot functions related to in-memory resource manipulation.
"""

from uuid import uuid4

import yaml

from rentabot.exceptions import (
    InvalidLockToken,
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


async def lock_resource(resource_id: int) -> tuple[str, Resource]:
    """Lock a specific resource by ID.

    Args:
        resource_id: The ID of the resource to lock.

    Returns:
        tuple: (lock_token, updated_resource)

    Raises:
        ResourceNotFound: If resource doesn't exist.
        ResourceAlreadyLocked: If resource is already locked.
    """
    async with resource_lock:
        resource = get_resource_from_id(resource_id)

        if resource.lock_token:
            logger.warning(f"Resource already locked. Id: {resource_id}")
            raise ResourceAlreadyLocked(
                message="Cannot lock the requested resource, resource is already locked",
                payload={"resource_id": resource_id},
            )

        updated_resource = resource.model_copy(
            update={"lock_token": str(uuid4()), "lock_details": "Resource locked"}
        )

        resources_by_id[updated_resource.id] = updated_resource
        logger.info(f"Resource locked. Id: {updated_resource.id}")

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
                "resource": resource.model_dump(by_alias=True),
                "invalid-lock-token": lock_token,
            },
        )

    updated_resource = resource.model_copy(
        update={"lock_token": "", "lock_details": "Resource available"}
    )

    resources_by_id[updated_resource.id] = updated_resource

    logger.info(f"Resource unlocked. Id : {resource_id}")


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
