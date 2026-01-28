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
    InsufficientResources,
    InvalidLockToken,
    InvalidReservationTags,
    InvalidTTL,
    ReservationCannotBeCancelled,
    ReservationClaimExpired,
    ReservationNotFound,
    ReservationNotFulfilled,
    ResourceAlreadyLocked,
    ResourceAlreadyUnlocked,
    ResourceDescriptorIsEmpty,
    ResourceNotFound,
)
from rentabot.logger import get_logger
from rentabot.models import (
    Reservation,
    Resource,
    reservation_lock,
    reservations_by_id,
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
                    "ttl": ttl,
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

            # Find expired locks - take snapshot while holding lock to avoid race condition
            async with resource_lock:
                resources_snapshot = list(resources_by_id.values())

            for resource in resources_snapshot:
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


# - [ Reservation Functions ] ------------------------------------------------


async def unlock_resource_by_token(lock_token: str) -> None:
    """Unlock a resource by its lock token (helper for cleanup).

    Args:
        lock_token: The lock token to identify the resource.

    Raises:
        ResourceNotFound: If no resource with this token exists.
    """
    async with resource_lock:
        # Find resource with this token
        resource = None
        for res in resources_by_id.values():
            if res.lock_token == lock_token:
                resource = res
                break

        if resource is None:
            logger.warning(f"No resource found with token: {lock_token}")
            raise ResourceNotFound(
                message="No resource found with this token", payload={"lock_token": lock_token}
            )

        # Unlock it
        updated_resource = resource.model_copy(
            update={
                "lock_token": "",
                "lock_details": "Resource available",
                "lock_acquired_at": None,
                "lock_expires_at": None,
            }
        )
        resources_by_id[updated_resource.id] = updated_resource
        logger.info(f"Resource unlocked by token. Id: {resource.id}")


async def lock_resources_by_tags(tags: list[str], quantity: int, ttl: int = 3600) -> list[Resource]:
    """Lock multiple resources matching tags atomically.

    Args:
        tags: List of required tags.
        quantity: Number of resources to lock.
        ttl: Time-to-live for locks in seconds.

    Returns:
        List of locked Resource objects.

    Raises:
        InsufficientResources: If not enough unlocked resources match the tags.
        InvalidTTL: If TTL exceeds max_lock_duration for any resource.
    """
    async with resource_lock:
        # Find available resources matching all tags
        all_resources = get_all_resources()
        available = []

        for resource in all_resources:
            if not resource.tags:
                continue

            # Skip locked resources
            if resource.lock_token:
                continue

            # Check if resource has all required tags
            parsed_tags = [tag.strip() for tag in resource.tags.split(",") if tag.strip()]
            if set(parsed_tags).intersection(set(tags)) == set(tags):
                available.append(resource)

        # Check if we have enough resources
        if len(available) < quantity:
            raise InsufficientResources(
                message=f"Not enough resources available. Need {quantity}, found {len(available)}",
                payload={"tags": tags, "quantity": quantity, "available": len(available)},
            )

        # Take the first N available resources
        to_lock = available[:quantity]

        # Validate TTL for all resources first
        for resource in to_lock:
            if ttl > resource.max_lock_duration:
                raise InvalidTTL(
                    message=f"Requested TTL ({ttl}s) exceeds maximum allowed duration for resource {resource.id} ({resource.max_lock_duration}s)",
                    payload={
                        "resource_id": resource.id,
                        "ttl": ttl,
                        "max_lock_duration": resource.max_lock_duration,
                    },
                )

        # Lock all resources
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl)
        locked_resources = []

        for resource in to_lock:
            updated = resource.model_copy(
                update={
                    "lock_token": str(uuid4()),
                    "lock_details": "Resource locked (reservation)",
                    "lock_acquired_at": now,
                    "lock_expires_at": expires_at,
                }
            )
            resources_by_id[updated.id] = updated
            locked_resources.append(updated)
            logger.info(f"Resource locked for reservation. Id: {updated.id}, TTL: {ttl}s")

        return locked_resources


async def create_reservation(
    tags: list[str], quantity: int, max_wait_time: int = 3600, ttl: int = 3600
) -> Reservation:
    """Create a new reservation.

    Args:
        tags: Required tags for resources.
        quantity: Number of resources needed.
        max_wait_time: Maximum time to wait for fulfillment (seconds, default 3600).
        ttl: Lock TTL when resources are claimed (seconds, default 3600).

    Returns:
        Created Reservation object.

    Raises:
        InvalidReservationTags: If tags list is empty.
        ResourceNotFound: If no resources match the tags.
    """
    # Validate that tags is not empty
    if not tags:
        raise InvalidReservationTags(
            message="Tags list cannot be empty. Reservation must be done using a tag identifier.",
            payload={"tags": tags},
        )

    # Validate that at least some resources match the tags
    all_resources = get_all_resources()
    matching_count = 0

    for resource in all_resources:
        if not resource.tags:
            continue
        parsed_tags = [tag.strip() for tag in resource.tags.split(",") if tag.strip()]
        if set(parsed_tags).intersection(set(tags)) == set(tags):
            matching_count += 1

    if matching_count == 0:
        raise ResourceNotFound(
            message="No resources match the specified tags", payload={"tags": tags}
        )

    if matching_count < quantity:
        logger.warning(
            f"Not enough total resources match tags. Need {quantity}, total available: {matching_count}"
        )
        # Still allow creation - resources might be unlocked later

    now = datetime.now(timezone.utc)
    reservation_id = f"res_{str(uuid4()).replace('-', '')}"

    reservation = Reservation(
        reservation_id=reservation_id,
        tags=tags,
        quantity=quantity,
        ttl=ttl,
        status="pending",
        created_at=now,
        expires_at=now + timedelta(seconds=max_wait_time),
    )

    async with reservation_lock:
        reservations_by_id[reservation_id] = reservation

    logger.info(f"Reservation created. ID: {reservation_id}, Tags: {tags}, Quantity: {quantity}")
    return reservation


async def get_reservation(reservation_id: str) -> Reservation:
    """Get a reservation by ID with computed position in queue.

    Args:
        reservation_id: The reservation ID.

    Returns:
        Reservation object with position_in_queue filled.

    Raises:
        ReservationNotFound: If reservation doesn't exist.
    """
    async with reservation_lock:
        reservation = reservations_by_id.get(reservation_id)

        if reservation is None:
            raise ReservationNotFound(
                message="Reservation not found", payload={"reservation_id": reservation_id}
            )

        # Compute position in queue if pending
        if reservation.status == "pending":
            pending = [r for r in reservations_by_id.values() if r.status == "pending"]
            pending.sort(key=lambda r: r.created_at)
            position = next(
                (i + 1 for i, r in enumerate(pending) if r.reservation_id == reservation_id),
                None,
            )
            reservation = reservation.model_copy(update={"position_in_queue": position})

        return reservation


async def claim_reservation(reservation_id: str) -> Reservation:
    """Claim a fulfilled reservation.

    Args:
        reservation_id: The reservation ID to claim.

    Returns:
        Claimed reservation.

    Raises:
        ReservationNotFound: If reservation doesn't exist.
        ReservationNotFulfilled: If reservation is still pending.
        ReservationClaimExpired: If claim window has expired.
    """
    async with reservation_lock:
        reservation = reservations_by_id.get(reservation_id)

        if reservation is None:
            raise ReservationNotFound(
                message="Reservation not found", payload={"reservation_id": reservation_id}
            )

        if reservation.status == "pending":
            raise ReservationNotFulfilled(
                message="Reservation not yet fulfilled",
                payload={"reservation_id": reservation_id, "status": reservation.status},
            )

        if reservation.status != "fulfilled":
            raise ReservationNotFound(
                message=f"Reservation already {reservation.status}",
                payload={"reservation_id": reservation_id, "status": reservation.status},
            )

        # Check claim window
        now = datetime.now(timezone.utc)
        if reservation.claim_expires_at and reservation.claim_expires_at <= now:
            raise ReservationClaimExpired(
                message="Claim window has expired",
                payload={
                    "reservation_id": reservation_id,
                    "claim_expires_at": reservation.claim_expires_at.isoformat(),
                },
            )

        # Mark as claimed
        updated = reservation.model_copy(update={"status": "claimed", "claimed_at": now})
        reservations_by_id[reservation_id] = updated

        logger.info(f"Reservation claimed. ID: {reservation_id}")
        return updated


async def cancel_reservation(reservation_id: str) -> None:
    """Cancel a pending reservation.

    Args:
        reservation_id: The reservation ID to cancel.

    Raises:
        ReservationNotFound: If reservation doesn't exist.
        ReservationCannotBeCancelled: If reservation is fulfilled/claimed.
    """
    async with reservation_lock:
        reservation = reservations_by_id.get(reservation_id)

        if reservation is None:
            raise ReservationNotFound(
                message="Reservation not found", payload={"reservation_id": reservation_id}
            )

        if reservation.status in ["fulfilled", "claimed"]:
            raise ReservationCannotBeCancelled(
                message=f"Cannot cancel {reservation.status} reservation",
                payload={"reservation_id": reservation_id, "status": reservation.status},
            )

        # Delete the reservation
        del reservations_by_id[reservation_id]
        logger.info(f"Reservation cancelled. ID: {reservation_id}")


async def list_reservations() -> list[Reservation]:
    """List all active reservations.

    Returns:
        List of all reservations with positions computed for pending ones.
    """
    async with reservation_lock:
        reservations = list(reservations_by_id.values())

        # Compute positions for pending reservations
        pending = [r for r in reservations if r.status == "pending"]
        pending.sort(key=lambda r: r.created_at)

        result = []
        for reservation in reservations:
            if reservation.status == "pending":
                position = next(
                    (
                        i + 1
                        for i, r in enumerate(pending)
                        if r.reservation_id == reservation.reservation_id
                    ),
                    None,
                )
                result.append(reservation.model_copy(update={"position_in_queue": position}))
            else:
                result.append(reservation)

        return result


async def auto_fulfill_reservations() -> None:
    """Background task that matches freed resources to pending reservations.

    Runs periodically to clean up expired reservations and fulfill pending ones.
    """
    while True:
        try:
            await asyncio.sleep(10)  # Check every 10 seconds
            now = datetime.now(timezone.utc)

            # Take snapshot of reservations to avoid holding lock during operations
            async with reservation_lock:
                reservations_snapshot = list(reservations_by_id.items())

            # 1. Clean up expired pending reservations
            expired_pending = []
            for res_id, reservation in reservations_snapshot:
                if reservation.status == "pending" and reservation.expires_at <= now:
                    expired_pending.append((res_id, reservation))

            for res_id, reservation in expired_pending:
                async with reservation_lock:
                    # Re-check in case it was fulfilled during iteration
                    current = reservations_by_id.get(res_id)
                    if current and current.status == "pending" and current.expires_at <= now:
                        del reservations_by_id[res_id]
                        logger.info(
                            f"Expired pending reservation {res_id} (waited {(now - reservation.created_at).total_seconds()}s)"
                        )

            # 2. Clean up expired unclaimed fulfilled reservations
            expired_fulfilled = []
            for res_id, reservation in reservations_snapshot:
                if (
                    reservation.status == "fulfilled"
                    and reservation.claim_expires_at
                    and reservation.claim_expires_at <= now
                ):
                    expired_fulfilled.append((res_id, reservation))

            for res_id, reservation in expired_fulfilled:
                # Unlock the resources (this acquires resource_lock internally)
                for token in reservation.lock_tokens:
                    try:
                        await unlock_resource_by_token(token)
                    except ResourceNotFound:
                        logger.warning(
                            f"Resource with token {token} not found during reservation cleanup"
                        )

                # Remove reservation after unlocking resources
                async with reservation_lock:
                    # Re-check in case it was claimed during iteration
                    current = reservations_by_id.get(res_id)
                    if (
                        current
                        and current.status == "fulfilled"
                        and current.claim_expires_at
                        and current.claim_expires_at <= now
                    ):
                        del reservations_by_id[res_id]
                        logger.info(f"Expired unclaimed reservation {res_id}")

            # 3. Try to fulfill pending reservations (FIFO)
            pending = []
            async with reservation_lock:
                pending = [r for r in reservations_by_id.values() if r.status == "pending"]
                pending.sort(key=lambda r: r.created_at)  # FIFO

            for reservation in pending:
                try:
                    # Try to lock resources matching tags (this acquires resource_lock internally)
                    locked = await lock_resources_by_tags(
                        tags=reservation.tags,
                        quantity=reservation.quantity,
                        ttl=reservation.ttl,
                    )

                    # Success! Mark as fulfilled
                    fulfilled_at = datetime.now(timezone.utc)
                    async with reservation_lock:
                        # Re-check reservation still exists and is pending
                        current = reservations_by_id.get(reservation.reservation_id)
                        if current and current.status == "pending":
                            updated = current.model_copy(
                                update={
                                    "status": "fulfilled",
                                    "fulfilled_at": fulfilled_at,
                                    "claim_expires_at": fulfilled_at + timedelta(seconds=60),
                                    "resource_ids": [r.id for r in locked],
                                    "lock_tokens": [r.lock_token for r in locked],
                                }
                            )
                            reservations_by_id[reservation.reservation_id] = updated

                            logger.info(
                                f"Fulfilled reservation {reservation.reservation_id} "
                                f"with resources {[r.id for r in locked]}"
                            )

                except InsufficientResources:
                    # Not enough resources yet, keep waiting
                    continue
                except Exception as e:
                    logger.error(
                        f"Error fulfilling reservation {reservation.reservation_id}: {e}",
                        exc_info=True,
                    )

        except Exception as e:
            logger.error(f"Error in auto_fulfill_reservations task: {e}", exc_info=True)
