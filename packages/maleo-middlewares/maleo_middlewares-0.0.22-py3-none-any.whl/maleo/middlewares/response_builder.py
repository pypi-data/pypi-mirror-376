from Crypto.PublicKey.RSA import RsaKey
from datetime import datetime
from fastapi import Response
from typing import Optional
from uuid import UUID, uuid4
from maleo.crypto.signature import sign
from maleo.crypto.token import encode
from maleo.dtos.authentication import OptionalAuthentication
from maleo.dtos.contexts.operation import generate_operation_context
from maleo.dtos.contexts.request import RequestContext
from maleo.dtos.contexts.service import ServiceContext
from maleo.dtos.token import GeneralCredentialPayload, TimestampPayload, GeneralPayload
from maleo.enums.operation import (
    SystemOperationType,
    Origin,
    Layer,
    Target,
)
from maleo.enums.token import TokenType
from maleo.logging.enums import Level
from maleo.logging.logger import Middleware
from maleo.mixins.timestamp import OperationTimestamp
from maleo.schemas.operation.system import (
    SystemOperationAction,
    SuccessfulSystemOperation,
)
from maleo.schemas.response import NoDataResponse
from maleo.types.base.uuid import OptionalUUID
from maleo.utils.name import get_fully_qualified_name


class ResponseBuilder:
    """ResponseBuilder class"""

    key = "response_builder"
    name = "ResponseBuilder"

    def __init__(
        self,
        logger: Middleware,
        private_key: RsaKey,
        service_context: Optional[ServiceContext] = None,
        operation_id: OptionalUUID = None,
    ) -> None:
        self._logger = logger
        self._private_key = private_key
        self._service_context = (
            service_context
            if service_context is not None
            else ServiceContext.from_env()
        )
        operation_id = operation_id if operation_id is not None else uuid4()
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
        ).log(logger=self._logger, level=Level.INFO)

    def _should_regenerate_auth(
        self,
        request_context: RequestContext,
        authentication: OptionalAuthentication,
        response: Response,
    ) -> bool:
        if authentication.credentials.token is not None:
            return (
                authentication.user.is_authenticated
                and authentication.credentials.token.type == TokenType.REFRESH
                and 200 <= response.status_code < 300
                and not request_context.url.endswith(
                    ("login", "logout", "token", "refresh")
                )
            )
        return False

    def _add_new_authorization_header(
        self,
        request_context: RequestContext,
        authentication: OptionalAuthentication,
        response: Response,
    ) -> Response:
        if authentication.credentials.token is None:
            return response

        if not self._should_regenerate_auth(
            request_context=request_context,
            authentication=authentication,
            response=response,
        ):
            return response

        credential = GeneralCredentialPayload(
            iss=authentication.credentials.token.payload.iss,
            sub=authentication.credentials.token.payload.sub,
            sr=authentication.credentials.token.payload.sr,
            u_i=authentication.credentials.token.payload.u_i,
            u_uu=authentication.credentials.token.payload.u_uu,
            u_u=authentication.credentials.token.payload.u_u,
            u_e=authentication.credentials.token.payload.u_e,
            u_ut=authentication.credentials.token.payload.u_ut,
            o_i=authentication.credentials.token.payload.o_i,
            o_uu=authentication.credentials.token.payload.o_uu,
            o_k=authentication.credentials.token.payload.o_k,
            o_ot=authentication.credentials.token.payload.o_ot,
            uor=authentication.credentials.token.payload.uor,
        )
        timestamp = TimestampPayload.new_timestamp()
        payload = GeneralPayload.model_validate(
            {**credential.model_dump(), **timestamp.model_dump()}
        )
        try:
            token = encode(
                payload=payload.model_dump(mode="json"), key=self._private_key
            )
        except Exception:
            token = None

        if token is not None:
            response.headers["x-new-authorization"] = token

        return response

    def _add_signature_header(
        self,
        operation_id: UUID,
        request_id: UUID,
        method: str,
        url: str,
        requested_at: datetime,
        responded_at: datetime,
        process_time: float,
        response: Response,
    ) -> Response:
        message = (
            f"{str(operation_id)}|"
            f"{str(request_id)}"
            f"{method}|"
            f"{url}|"
            f"{requested_at.isoformat()}|"
            f"{responded_at.isoformat()}|"
            f"{str(process_time)}|"
        )

        try:
            signature = sign(message=message, key=self._private_key)
            response.headers["x-signature"] = signature
        except Exception:
            pass

        return response

    def add_headers(
        self,
        operation_id: UUID,
        request_context: RequestContext,
        authentication: OptionalAuthentication,
        response: Response,
        responded_at: datetime,
        process_time: float,
    ) -> Response:
        """Add custom headers to response"""
        # Basic headers
        response.headers["x-operation-id"] = str(operation_id)
        response.headers["x-request-id"] = str(request_context.id)
        response.headers["x-requested-at"] = request_context.requested_at.isoformat()
        response.headers["x-responded-at"] = responded_at.isoformat()
        response.headers["x-process-time"] = str(process_time)

        # Signature header
        response = self._add_signature_header(
            operation_id=operation_id,
            request_id=request_context.id,
            method=request_context.method,
            url=request_context.url,
            requested_at=request_context.requested_at,
            responded_at=responded_at,
            process_time=process_time,
            response=response,
        )

        # New Authorization header
        response = self._add_new_authorization_header(
            request_context=request_context,
            authentication=authentication,
            response=response,
        )

        return response
