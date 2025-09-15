import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID
from maleo.dtos.contexts.operation import generate_operation_context
from maleo.dtos.contexts.service import ServiceContext
from maleo.enums.operation import (
    OperationType,
    SystemOperationType,
    Origin,
    Layer,
    Target,
)
from maleo.exceptions import InternalServerError
from maleo.logging.enums import Level
from maleo.logging.logger import Middleware
from maleo.mixins.timestamp import OperationTimestamp
from maleo.schemas.operation.system import (
    SystemOperationAction,
    SuccessfulSystemOperation,
)
from maleo.schemas.response import (
    InternalServerErrorResponse,
    NoDataResponse,
    SingleDataResponse,
)
from maleo.types.base.integer import OptionalInteger
from maleo.types.base.string import ListOfStrings
from maleo.utils.name import get_fully_qualified_name
from .config import RateLimiterConfig
from .dtos import InactiveKeys


class RateLimiter:
    """RateLimiter class"""

    key = "rate_limiter"
    name = "RateLimiter"

    def __init__(
        self,
        operation_id: UUID,
        config: RateLimiterConfig,
        logger: Middleware,
        service_context: Optional[ServiceContext] = None,
    ) -> None:
        self._logger = logger
        self._service_context = (
            service_context
            if service_context is not None
            else ServiceContext.from_env()
        )
        operation_context = generate_operation_context(
            origin=Origin.SERVICE,
            layer=Layer.MIDDLEWARE,
            layer_details={
                "identifier": {
                    "key": "base_middleware",
                    "name": "Base Middleware",
                },
                "component": {"key": self.key, "name": self.name},
            },
            target=Target.INTERNAL,
            target_details={"fully_qualified_name": get_fully_qualified_name()},
        )
        operation_action = SystemOperationAction(
            type=SystemOperationType.INITIALIZATION,
            details={
                "type": "class_initialization",
                "class_key": self.key,
                "class_name": self.name,
            },
        )

        self.limit = config.limit
        self.window = config.window
        self.idle_timeout = config.idle_timeout
        self.cleanup_interval = config.cleanup_interval
        self._requests: Dict[str, List[datetime]] = defaultdict(list)
        self._last_seen: Dict[str, datetime] = {}
        self._last_cleanup = datetime.now()
        self._lock = asyncio.Lock()

        # Background task management
        self._cleanup_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

        SuccessfulSystemOperation[None, NoDataResponse[None]](
            service_context=self._service_context,
            id=operation_id,
            context=operation_context,
            timestamp=OperationTimestamp.now(),
            summary=f"Successfully initialized {self.name}",
            request_context=None,
            authentication=None,
            action=operation_action,
            response=NoDataResponse[None](metadata=None, other=None),
        ).log(self._logger, Level.INFO)

    def _generate_key(
        self,
        ip_address: str = "unknown",
        user_id: OptionalInteger = None,
        organization_id: OptionalInteger = None,
    ) -> str:
        """Generate a combination key from ip_address, user_id, and organization_id"""
        return f"{ip_address}|{str(user_id)}|{str(organization_id)}"

    async def is_rate_limited(
        self,
        ip_address: str = "unknown",
        user_id: OptionalInteger = None,
        organization_id: OptionalInteger = None,
    ) -> bool:
        """
        Check if the combination of ip_address, user_id, and organization_id is rate limited.

        Args:
            ip_address: Client IP address (required)
            user_id: User ID (optional, can be None or integer >= 1)
            organization_id: Organization ID (optional, can be None or integer >= 1)

        Returns:
            True if rate limited, False otherwise
        """
        async with self._lock:
            now = datetime.now(tz=timezone.utc)

            rate_limit_key = self._generate_key(ip_address, user_id, organization_id)

            self._last_seen[rate_limit_key] = now

            # Remove old requests outside the window
            self._requests[rate_limit_key] = [
                timestamp
                for timestamp in self._requests[rate_limit_key]
                if (now - timestamp).total_seconds() <= self.window
            ]

            # Check rate limit
            if len(self._requests[rate_limit_key]) >= self.limit:
                return True

            # Record this request
            self._requests[rate_limit_key].append(now)
            return False

    async def get_current_count(
        self,
        ip_address: str = "unknown",
        user_id: OptionalInteger = None,
        organization_id: OptionalInteger = None,
    ) -> int:
        """Get current request count for the combination key"""
        async with self._lock:
            now = datetime.now(tz=timezone.utc)
            rate_limit_key = self._generate_key(ip_address, user_id, organization_id)

            # Remove old requests and count current ones
            valid_requests = [
                timestamp
                for timestamp in self._requests[rate_limit_key]
                if (now - timestamp).total_seconds() <= self.window
            ]

            return len(valid_requests)

    async def get_remaining_requests(
        self,
        ip_address: str,
        user_id: OptionalInteger = None,
        organization_id: OptionalInteger = None,
    ) -> int:
        """Get remaining requests allowed for the combination key"""
        current_count = await self.get_current_count(
            ip_address, user_id, organization_id
        )
        return max(0, self.limit - current_count)

    async def get_reset_time(
        self,
        ip_address: str,
        user_id: OptionalInteger = None,
        organization_id: OptionalInteger = None,
    ) -> float:
        """Get time in seconds until the rate limit resets for the combination key"""
        async with self._lock:
            now = datetime.now(tz=timezone.utc)
            rate_limit_key = self._generate_key(ip_address, user_id, organization_id)

            valid_requests = [
                timestamp
                for timestamp in self._requests[rate_limit_key]
                if (now - timestamp).total_seconds() <= self.window
            ]

            if not valid_requests:
                return 0.0

            # Time until the oldest request expires
            oldest_request = min(valid_requests)
            reset_time = self.window - (now - oldest_request).total_seconds()
            return max(0.0, reset_time)

    async def cleanup_old_data(self, operation_id: UUID) -> None:
        """Clean up old request data to prevent memory growth."""
        operation_context = generate_operation_context(
            origin=Origin.SERVICE,
            layer=Layer.MIDDLEWARE,
            layer_details={
                "identifier": {
                    "key": "base_middleware",
                    "name": "Base Middleware",
                },
                "component": {"key": self.key, "name": self.name},
            },
            target=Target.INTERNAL,
            target_details={"fully_qualified_name": get_fully_qualified_name()},
        )
        async with self._lock:
            now = datetime.now(tz=timezone.utc)
            inactive_keys: ListOfStrings = []

            for key in list(self._requests.keys()):
                # Remove keys with empty request lists
                if not self._requests[key]:
                    inactive_keys.append(key)
                    continue

                # Remove keys that haven't been active recently
                last_active = self._last_seen.get(
                    key, datetime.min.replace(tzinfo=timezone.utc)
                )
                if (now - last_active).total_seconds() > self.idle_timeout:
                    inactive_keys.append(key)

            if len(inactive_keys) > 0:
                # Clean up inactive keys
                for key in inactive_keys:
                    self._requests.pop(key, None)
                    self._last_seen.pop(key, None)

                SuccessfulSystemOperation[None, SingleDataResponse[InactiveKeys, None]](
                    service_context=self._service_context,
                    id=operation_id,
                    context=operation_context,
                    timestamp=OperationTimestamp.completed_now(now),
                    summary=f"Successfully cleaned up {len(inactive_keys)} inactive keys in RateLimiter",
                    request_context=None,
                    authentication=None,
                    action=SystemOperationAction(
                        type=SystemOperationType.BACKGROUND_JOB, details=None
                    ),
                    response=SingleDataResponse[InactiveKeys, None](
                        data=InactiveKeys(keys=inactive_keys), metadata=None, other=None
                    ),
                ).log(self._logger, Level.INFO)

    async def start_cleanup_task(self, operation_id: UUID):
        """Start the background cleanup task"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._shutdown_event.clear()  # Reset shutdown event
            self._cleanup_task = asyncio.create_task(
                self._background_cleanup(operation_id)
            )

    async def stop_cleanup_task(self):
        """Stop the background cleanup task"""
        self._shutdown_event.set()
        if self._cleanup_task and not self._cleanup_task.done():
            try:
                await asyncio.wait_for(self._cleanup_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass

    async def _background_cleanup(self, operation_id: UUID):
        """Background task that runs cleanup periodically"""
        operation_context = generate_operation_context(
            origin=Origin.SERVICE,
            layer=Layer.MIDDLEWARE,
            layer_details={
                "identifier": {
                    "key": "base_middleware",
                    "name": "Base Middleware",
                },
                "component": {"key": self.key, "name": self.name},
            },
            target=Target.INTERNAL,
            target_details={"fully_qualified_name": get_fully_qualified_name()},
        )
        operation_action = SystemOperationAction(
            type=SystemOperationType.BACKGROUND_JOB, details=None
        )
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(self.cleanup_interval)
                if not self._shutdown_event.is_set():
                    await self.cleanup_old_data(operation_id)
            except asyncio.CancelledError:
                break
            except Exception as e:
                details = {
                    "exc_type": type(e).__name__,
                    "exc_data": {
                        "message": str(e),
                        "args": e.args,
                    },
                }
                error = InternalServerError[None](
                    OperationType.SYSTEM,
                    service_context=self._service_context,
                    operation_id=operation_id,
                    operation_context=operation_context,
                    operation_timestamp=OperationTimestamp.now(),
                    operation_summary="Exception raised when performing RateLimiter background cleanup",
                    request_context=None,
                    authentication=None,
                    operation_action=operation_action,
                    details=details,
                    response=InternalServerErrorResponse(other=details),
                )

                operation = error.generate_operation(OperationType.SYSTEM)
                operation.log(self._logger, Level.ERROR)
