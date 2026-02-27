"""
Seguridad: JWT, validación de tokens y tenant_id
"""
import jwt
import json
from datetime import datetime, timedelta, timezone
from uuid import UUID
from functools import wraps
from flask import request, jsonify
from typing import Dict, Optional, Tuple

from .config import get_config


class JWTManager:
    """Gestor centralizado de tokens JWT"""

    def __init__(self, secret: str, algorithm: str = "HS256", expiration_hours: int = 24):
        self.secret = secret
        self.algorithm = algorithm
        self.expiration_hours = expiration_hours

    def create_token(self, payload: Dict) -> str:
        """
        Crea un JWT con el payload proporcionado.

        Payload esperado:
        {
            "sub": "agent-uuid",
            "email": "agent@valleverde.com",
            "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
            "role": "admin|agente|coordinador"
        }
        """
        # Copiar payload para no modificar el original
        data = payload.copy()

        # Agregar exp claim (expiración)
        exp_time = datetime.now(timezone.utc) + timedelta(hours=self.expiration_hours)
        data["exp"] = exp_time
        data["iat"] = datetime.now(timezone.utc)

        try:
            token = jwt.encode(data, self.secret, algorithm=self.algorithm)
            return token
        except Exception as e:
            raise ValueError(f"Error al crear token JWT: {str(e)}")

    def decode_token(self, token: str) -> Optional[Dict]:
        """
        Decodifica y valida un JWT.

        Returns:
            Dict con el payload si es válido
            None si es inválido o expirado
        """
        try:
            # Remover "Bearer " prefix si existe
            if token.startswith("Bearer "):
                token = token[7:]

            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception:
            return None

    def validate_token_and_extract_tenant(self, token: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Valida el token y extrae tenant_id + claims.

        Returns:
            (is_valid: bool, tenant_id: str | None, claims: dict | None)
        """
        payload = self.decode_token(token)

        if not payload:
            return False, None, None

        tenant_id = payload.get("tenant_id")
        if not tenant_id:
            return False, None, payload

        return True, tenant_id, payload


class SecurityContext:
    """Contexto de seguridad para el request actual"""

    def __init__(self, user_id: str, tenant_id: str, email: str, role: str, claims: Dict):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.email = email
        self.role = role
        self.claims = claims

    def __repr__(self):
        return f"<SecurityContext user={self.user_id} tenant={self.tenant_id} role={self.role}>"


def create_jwt_manager() -> JWTManager:
    """Factory para crear un JWTManager configurado"""
    cfg = get_config()
    return JWTManager(
        secret=cfg.JWT_SECRET,
        algorithm=cfg.JWT_ALGORITHM,
        expiration_hours=cfg.JWT_EXPIRATION_HOURS
    )


def token_required(f):
    """
    Decorador para proteger rutas que requieren autenticación.

    Valida:
    1. Presencia del token en Authorization header
    2. Validez del JWT (firma, expiración)
    3. Presencia de tenant_id en el claims

    Si es válido, inyecta el SecurityContext en request.security
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1. Extraer token del header Authorization
        auth_header = request.headers.get("Authorization", "")
        token = None

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

        if not token:
            return jsonify({
                "status": "error",
                "message": "Acceso denegado: Token faltante",
                "data": None
            }), 401

        # 2. Validar token y extraer tenant_id
        jwt_manager = create_jwt_manager()
        is_valid, tenant_id, claims = jwt_manager.validate_token_and_extract_tenant(token)

        if not is_valid or not tenant_id:
            return jsonify({
                "status": "error",
                "message": "Acceso denegado: Token inválido o expirado",
                "data": None
            }), 401

        # 3. Crear contexto de seguridad e inyectarlo en el request
        user_id = claims.get("sub")
        email = claims.get("email")
        role = claims.get("role", "agente")

        request.security = SecurityContext(
            user_id=user_id,
            tenant_id=tenant_id,
            email=email,
            role=role,
            claims=claims
        )

        # 4. Continuar con el request
        return f(*args, **kwargs)

    return decorated


def require_role(*allowed_roles):
    """
    Decorador que requiere un rol específico.
    Se usa DESPUÉS de @token_required.

    Ejemplo:
        @app.route('/admin')
        @token_required
        @require_role('admin', 'coordinador')
        def admin_endpoint():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(request, 'security'):
                return jsonify({
                    "status": "error",
                    "message": "Security context no disponible",
                    "data": None
                }), 401

            if request.security.role not in allowed_roles:
                return jsonify({
                    "status": "error",
                    "message": f"Acceso denegado: Rol requerido {allowed_roles}",
                    "data": None
                }), 403

            return f(*args, **kwargs)

        return decorated
    return decorator
