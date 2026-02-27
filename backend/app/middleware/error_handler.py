"""
Middleware y error handling globalizado
"""
from flask import jsonify
from typing import Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)


class APIException(Exception):
    """Excepción base para errores de API"""
    def __init__(self, message: str, status_code: int = 500, error_code: str = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or "INTERNAL_ERROR"
        super().__init__(message)


class ValidationError(APIException):
    """Error de validación de datos"""
    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        super().__init__(message, 400, error_code)


class UnauthorizedError(APIException):
    """Error de autenticación (sin token o token inválido)"""
    def __init__(self, message: str = "No autorizado"):
        super().__init__(message, 401, "UNAUTHORIZED")


class ForbiddenError(APIException):
    """Error de autorización (sin permisos)"""
    def __init__(self, message: str = "Acceso prohibido"):
        super().__init__(message, 403, "FORBIDDEN")


class NotFoundError(APIException):
    """Error de recurso no encontrado"""
    def __init__(self, message: str = "Recurso no encontrado"):
        super().__init__(message, 404, "NOT_FOUND")


class ConflictError(APIException):
    """Error de conflicto (ej: email duplicado)"""
    def __init__(self, message: str):
        super().__init__(message, 409, "CONFLICT")


class TenantMismatchError(APIException):
    """Error de tenant mismatch"""
    def __init__(self, message: str = "Acceso denegado: tenant mismatch"):
        super().__init__(message, 403, "TENANT_MISMATCH")


def create_api_response(
    status: str,
    message: str,
    data: Any = None,
    error_code: str = None,
    http_status: int = 200
) -> Tuple[Dict, int]:
    """
    Crea una respuesta API estándar.

    Returns:
        (response_dict, http_status_code)
    """
    response = {
        "status": status,
        "message": message,
        "data": data
    }

    if error_code:
        response["error_code"] = error_code

    return response, http_status


def register_error_handlers(app):
    """Registra todos los error handlers en la aplicación Flask"""

    @app.errorhandler(APIException)
    def handle_api_exception(error: APIException):
        """Maneja excepciones de API personalizadas"""
        response, status = create_api_response(
            status="error",
            message=error.message,
            error_code=error.error_code,
            http_status=error.status_code
        )
        return jsonify(response), status

    @app.errorhandler(400)
    def handle_bad_request(error):
        """Error 400: Bad Request"""
        response, status = create_api_response(
            status="error",
            message="Solicitud inválida",
            error_code="BAD_REQUEST",
            http_status=400
        )
        return jsonify(response), status

    @app.errorhandler(401)
    def handle_unauthorized(error):
        """Error 401: Unauthorized"""
        response, status = create_api_response(
            status="error",
            message="No autorizado",
            error_code="UNAUTHORIZED",
            http_status=401
        )
        return jsonify(response), status

    @app.errorhandler(403)
    def handle_forbidden(error):
        """Error 403: Forbidden"""
        response, status = create_api_response(
            status="error",
            message="Acceso prohibido",
            error_code="FORBIDDEN",
            http_status=403
        )
        return jsonify(response), status

    @app.errorhandler(404)
    def handle_not_found(error):
        """Error 404: Not Found"""
        response, status = create_api_response(
            status="error",
            message="Recurso no encontrado",
            error_code="NOT_FOUND",
            http_status=404
        )
        return jsonify(response), status

    @app.errorhandler(500)
    def handle_internal_error(error):
        """Error 500: Internal Server Error"""
        logger.error(f"Internal server error: {error}", exc_info=True)
        response, status = create_api_response(
            status="error",
            message="Error interno del servidor",
            error_code="INTERNAL_ERROR",
            http_status=500
        )
        return jsonify(response), status

    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        """Maneja cualquier otra excepción no anticipada"""
        logger.error(f"Unhandled exception: {error}", exc_info=True)

        # Si es Pydantic ValidationError, extraer detalles
        if hasattr(error, 'errors'):
            response, status = create_api_response(
                status="error",
                message="Error de validación",
                data={"errors": error.errors()},
                error_code="VALIDATION_ERROR",
                http_status=422
            )
        else:
            response, status = create_api_response(
                status="error",
                message="Error inesperado en el servidor",
                error_code="INTERNAL_ERROR",
                http_status=500
            )

        return jsonify(response), status
