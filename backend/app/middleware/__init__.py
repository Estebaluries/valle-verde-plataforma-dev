"""
Middleware - Manejo de autenticación, CORS, errores, etc.
"""
from .error_handler import (
    APIException,
    ValidationError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    ConflictError,
    TenantMismatchError,
    create_api_response,
    register_error_handlers
)

__all__ = [
    "APIException",
    "ValidationError",
    "UnauthorizedError",
    "ForbiddenError",
    "NotFoundError",
    "ConflictError",
    "TenantMismatchError",
    "create_api_response",
    "register_error_handlers"
]
