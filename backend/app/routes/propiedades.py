"""
Routes: Propiedades (Catálogo público + Admin CRUD)
GET /api/propiedades - Listar propiedades (público, filtrable)
GET /api/propiedades/:id - Detalle (público)
POST /api/propiedades - Crear (admin)
PUT /api/propiedades/:id - Actualizar (admin)
DELETE /api/propiedades/:id - Archivar (admin)
"""
from flask import Blueprint, request, jsonify
from uuid import UUID
from typing import Optional

from ..core import token_required, require_role
from ..middleware import create_api_response
from ..models import PropiedadCreate, PropiedadUpdate
from ..services import CatalogoService, PropiedadService
from supabase import Client

propiedades_bp = Blueprint('propiedades', __name__, url_prefix='/api/propiedades')


def init_propiedades_routes(supabase_client: Client, tenant_id: UUID):
    """Factory que inyecta dependencias en los routes"""

    catalogo_service = CatalogoService(supabase_client)
    propiedad_service = PropiedadService(supabase_client)

    @propiedades_bp.route('', methods=['GET'])
    def listar_propiedades():
        """GET /api/propiedades - Lista propiedades del catálogo (público)"""
        try:
            # Parámetros de query
            page = request.args.get('page', 1, type=int)
            limit = request.args.get('limit', 30, type=int)
            tipo = request.args.get('tipo', None, type=str)
            operacion = request.args.get('operacion', None, type=str)
            colonia = request.args.get('colonia', None, type=str)
            min_precio = request.args.get('min_precio', None, type=float)
            max_precio = request.args.get('max_precio', None, type=float)

            offset = (page - 1) * limit

            # Buscar propiedades
            propiedades = catalogo_service.buscar_propiedades(
                tenant_id=tenant_id,
                tipo=tipo,
                operacion=operacion,
                colonia=colonia,
                min_precio=min_precio,
                max_precio=max_precio,
                limit=limit
            )

            # Paginar manualmente (idealmente en función de query)
            total = len(propiedades)
            paginas = (total + limit - 1) // limit
            propiedades = propiedades[offset:offset + limit]

            data = {
                "items": propiedades,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": paginas
            }

            response, status = create_api_response(
                status="success",
                message="Catálogo recuperado",
                data=data,
                http_status=200
            )
            return jsonify(response), status

        except Exception as e:
            response, status = create_api_response(
                status="error",
                message=f"Error al obtener propiedades: {str(e)}",
                error_code="FETCH_ERROR",
                http_status=500
            )
            return jsonify(response), status

    @propiedades_bp.route('/<int:propiedad_id>', methods=['GET'])
    def obtener_propiedad(propiedad_id: int):
        """GET /api/propiedades/:id - Detalle de propiedad (público)"""
        try:
            propiedad = catalogo_service.obtener_propiedad(propiedad_id, tenant_id)

            response, status = create_api_response(
                status="success",
                message="Propiedad encontrada",
                data=propiedad,
                http_status=200
            )
            return jsonify(response), status

        except Exception as e:
            response, status = create_api_response(
                status="error",
                message=f"Error: {str(e)}",
                error_code="NOT_FOUND",
                http_status=404
            )
            return jsonify(response), status

    @propiedades_bp.route('', methods=['POST'])
    @token_required
    @require_role('admin')
    def crear_propiedad():
        """POST /api/propiedades - Crear propiedad (admin)"""
        try:
            data = request.get_json()
            if not data:
                response, status = create_api_response(
                    status="error",
                    message="Body vacío",
                    error_code="EMPTY_BODY",
                    http_status=400
                )
                return jsonify(response), status

            # Validar schema
            try:
                prop_req = PropiedadCreate(**data)
            except ValueError as e:
                response, status = create_api_response(
                    status="error",
                    message=f"Error de validación: {str(e)}",
                    error_code="VALIDATION_ERROR",
                    http_status=422
                )
                return jsonify(response), status

            # Crear
            nueva = propiedad_service.crear_propiedad(tenant_id, prop_req)

            response, status = create_api_response(
                status="success",
                message="Propiedad creada",
                data=nueva,
                http_status=201
            )
            return jsonify(response), status

        except Exception as e:
            response, status = create_api_response(
                status="error",
                message=f"Error al crear: {str(e)}",
                error_code="CREATE_ERROR",
                http_status=500
            )
            return jsonify(response), status

    @propiedades_bp.route('/<int:propiedad_id>', methods=['PUT'])
    @token_required
    @require_role('admin')
    def actualizar_propiedad(propiedad_id: int):
        """PUT /api/propiedades/:id - Actualizar propiedad (admin)"""
        try:
            data = request.get_json() or {}

            # Validar schema
            try:
                prop_update = PropiedadUpdate(**data)
            except ValueError as e:
                response, status = create_api_response(
                    status="error",
                    message=f"Error de validación: {str(e)}",
                    error_code="VALIDATION_ERROR",
                    http_status=422
                )
                return jsonify(response), status

            # Actualizar
            actualizada = propiedad_service.actualizar_propiedad(propiedad_id, tenant_id, prop_update)

            response, status = create_api_response(
                status="success",
                message="Propiedad actualizada",
                data=actualizada,
                http_status=200
            )
            return jsonify(response), status

        except Exception as e:
            response, status = create_api_response(
                status="error",
                message=f"Error: {str(e)}",
                error_code="UPDATE_ERROR",
                http_status=500
            )
            return jsonify(response), status

    @propiedades_bp.route('/<int:propiedad_id>', methods=['DELETE'])
    @token_required
    @require_role('admin')
    def archivar_propiedad(propiedad_id: int):
        """DELETE /api/propiedades/:id - Archivar propiedad (admin, soft delete)"""
        try:
            propiedad_service.archivar_propiedad(propiedad_id, tenant_id)

            response, status = create_api_response(
                status="success",
                message="Propiedad archivada",
                data=None,
                http_status=204
            )
            return jsonify(response), status

        except Exception as e:
            response, status = create_api_response(
                status="error",
                message=f"Error: {str(e)}",
                error_code="DELETE_ERROR",
                http_status=500
            )
            return jsonify(response), status

    return propiedades_bp
