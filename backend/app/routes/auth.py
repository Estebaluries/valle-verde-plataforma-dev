"""
Routes: Autenticación
POST /api/auth/login - Login de agentes
POST /api/auth/logout - Logout (opcional)
GET /api/auth/me - Datos del usuario autenticado
"""
from flask import Blueprint, request, jsonify
from uuid import UUID

from ..core import token_required, create_jwt_manager
from ..middleware import (
    ValidationError,
    UnauthorizedError,
    create_api_response
)
from ..models import LoginRequest
from ..services import AuthService
from supabase import Client

# Blueprint para organizar rutas
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def init_auth_routes(supabase_client: Client, tenant_id: UUID):
    """Factory que inyecta dependencias en los routes"""

    auth_service = AuthService(supabase_client, create_jwt_manager())

    @auth_bp.route('/login', methods=['POST'])
    def login():
        """POST /api/auth/login - Login de agente"""
        try:
            # 1. Validar request
            data = request.get_json()
            if not data:
                response, status = create_api_response(
                    status="error",
                    message="Body vacío",
                    error_code="EMPTY_BODY",
                    http_status=400
                )
                return jsonify(response), status

            # 2. Parsear y validar schema
            try:
                login_req = LoginRequest(**data)
            except ValueError as e:
                response, status = create_api_response(
                    status="error",
                    message=f"Error de validación: {str(e)}",
                    error_code="VALIDATION_ERROR",
                    http_status=422
                )
                return jsonify(response), status

            # 3. Ejecutar login con tenant_id fijo
            result = auth_service.login(login_req.email, login_req.password, tenant_id)

            response, status = create_api_response(
                status="success",
                message="Autenticación exitosa",
                data=result,
                http_status=200
            )
            return jsonify(response), status

        except UnauthorizedError as e:
            response, status = create_api_response(
                status="error",
                message=str(e.message),
                error_code="UNAUTHORIZED",
                http_status=401
            )
            return jsonify(response), status
        except Exception as e:
            response, status = create_api_response(
                status="error",
                message="Error en login",
                error_code="LOGIN_ERROR",
                http_status=500
            )
            return jsonify(response), status

    @auth_bp.route('/logout', methods=['POST'])
    @token_required
    def logout():
        """POST /api/auth/logout - Logout (principalmente para frontend limpiar token)"""
        # Con JWT stateless, no hay mucho que hacer en backend
        # El frontend simplemente elimina el token del localStorage
        response, status = create_api_response(
            status="success",
            message="Logout exitoso",
            data={"message": "Token invalidado en cliente"},
            http_status=200
        )
        return jsonify(response), status

    @auth_bp.route('/me', methods=['GET'])
    @token_required
    def get_current_user():
        """GET /api/auth/me - Obtiene datos del usuario autenticado"""
        from flask import request

        user_data = {
            "id": request.security.user_id,
            "email": request.security.email,
            "tenant_id": request.security.tenant_id,
            "role": request.security.role
        }

        response, status = create_api_response(
            status="success",
            message="Usuario autenticado",
            data=user_data,
            http_status=200
        )
        return jsonify(response), status

    return auth_bp
