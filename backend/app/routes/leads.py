"""
Routes: Leads (CRM)
GET /api/leads - Listar leads (filtrable)
GET /api/leads/:id - Detalle de lead con interacciones
POST /api/leads - Crear lead (público con datos mínimos, o admin con datos completos)
PUT /api/leads/:id - Actualizar lead (admin)
DELETE /api/leads/:id - Archivar lead (admin)
GET /api/leads/:id/actividad - Timeline de interacciones
POST /api/leads/:id/interacciones - Registrar interacción
"""
from flask import Blueprint, request, jsonify
from uuid import UUID

from ..core import token_required
from ..middleware import create_api_response
from ..models import LeadCreate, LeadUpdate
from ..services import CRMService
from supabase import Client

leads_bp = Blueprint('leads', __name__, url_prefix='/api/leads')


def init_leads_routes(supabase_client: Client, tenant_id: UUID):
    """Factory que inyecta dependencias"""

    crm_service = CRMService(supabase_client)

    @leads_bp.route('', methods=['GET'])
    @token_required
    def listar_leads():
        """GET /api/leads - Listar leads del tenant (filtrable)"""
        try:
            status = request.args.get('status', None, type=str)
            agente_id = request.args.get('asignado_a', None, type=str)
            limit = request.args.get('limit', 50, type=int)

            # Obtener desde security context si no se pasa agente_id (ver "mis" leads)
            if not agente_id and hasattr(request, 'security'):
                # Agente solo ve sus leads
                agente_id = request.security.user_id

            leads = crm_service.listar_leads(tenant_id, status, agente_id, limit)

            data = {
                "items": leads,
                "total": len(leads),
                "limit": limit
            }

            response, status_code = create_api_response(
                status="success",
                message="Leads obtenidos",
                data=data,
                http_status=200
            )
            return jsonify(response), status_code

        except Exception as e:
            response, status_code = create_api_response(
                status="error",
                message=f"Error: {str(e)}",
                error_code="FETCH_ERROR",
                http_status=500
            )
            return jsonify(response), status_code

    @leads_bp.route('/<lead_id>', methods=['GET'])
    @token_required
    def obtener_lead(lead_id: str):
        """GET /api/leads/:id - Detalle de lead con interacciones"""
        try:
            lead = crm_service.obtener_lead(lead_id, tenant_id)

            response, status_code = create_api_response(
                status="success",
                message="Lead encontrado",
                data=lead,
                http_status=200
            )
            return jsonify(response), status_code

        except Exception as e:
            response, status_code = create_api_response(
                status="error",
                message=f"Error: {str(e)}",
                error_code="NOT_FOUND",
                http_status=404
            )
            return jsonify(response), status_code

    @leads_bp.route('', methods=['POST'])
    def crear_lead():
        """POST /api/leads - Crear lead (público o admin)"""
        try:
            data = request.get_json()
            if not data:
                response, status_code = create_api_response(
                    status="error",
                    message="Body vacío",
                    error_code="EMPTY_BODY",
                    http_status=400
                )
                return jsonify(response), status_code

            # Validar schema
            try:
                lead_req = LeadCreate(**data)
            except ValueError as e:
                response, status_code = create_api_response(
                    status="error",
                    message=f"Error de validación: {str(e)}",
                    error_code="VALIDATION_ERROR",
                    http_status=422
                )
                return jsonify(response), status_code

            # Crear desde formulario público
            nuevo_lead = crm_service.registrar_lead_public(tenant_id, lead_req)

            response, status_code = create_api_response(
                status="success",
                message="Lead registrado",
                data=nuevo_lead,
                http_status=201
            )
            return jsonify(response), status_code

        except Exception as e:
            response, status_code = create_api_response(
                status="error",
                message=f"Error: {str(e)}",
                error_code="CREATE_ERROR",
                http_status=500
            )
            return jsonify(response), status_code

    @leads_bp.route('/<lead_id>', methods=['PUT'])
    @token_required
    def actualizar_lead(lead_id: str):
        """PUT /api/leads/:id - Actualizar lead (admin)"""
        try:
            data = request.get_json() or {}

            # Validar schema
            try:
                lead_update = LeadUpdate(**data)
            except ValueError as e:
                response, status_code = create_api_response(
                    status="error",
                    message=f"Error de validación: {str(e)}",
                    error_code="VALIDATION_ERROR",
                    http_status=422
                )
                return jsonify(response), status_code

            # Actualizar
            actualizado = crm_service.actualizar_lead(lead_id, tenant_id, lead_update)

            response, status_code = create_api_response(
                status="success",
                message="Lead actualizado",
                data=actualizado,
                http_status=200
            )
            return jsonify(response), status_code

        except Exception as e:
            response, status_code = create_api_response(
                status="error",
                message=f"Error: {str(e)}",
                error_code="UPDATE_ERROR",
                http_status=500
            )
            return jsonify(response), status_code

    @leads_bp.route('/<lead_id>', methods=['DELETE'])
    @token_required
    def archivar_lead(lead_id: str):
        """DELETE /api/leads/:id - Archivar lead (soft delete)"""
        try:
            crm_service.lead_repo.delete(lead_id, tenant_id)

            response, status_code = create_api_response(
                status="success",
                message="Lead archivado",
                data=None,
                http_status=204
            )
            return jsonify(response), status_code

        except Exception as e:
            response, status_code = create_api_response(
                status="error",
                message=f"Error: {str(e)}",
                error_code="DELETE_ERROR",
                http_status=500
            )
            return jsonify(response), status_code

    @leads_bp.route('/<lead_id>/actividad', methods=['GET'])
    @token_required
    def obtener_timeline(lead_id: str):
        """GET /api/leads/:id/actividad - Timeline de interacciones"""
        try:
            timeline = crm_service.obtener_timeline(lead_id, tenant_id)

            data = {
                "items": timeline,
                "total": len(timeline)
            }

            response, status_code = create_api_response(
                status="success",
                message="Timeline obtenida",
                data=data,
                http_status=200
            )
            return jsonify(response), status_code

        except Exception as e:
            response, status_code = create_api_response(
                status="error",
                message=f"Error: {str(e)}",
                error_code="FETCH_ERROR",
                http_status=500
            )
            return jsonify(response), status_code

    @leads_bp.route('/<lead_id>/interacciones', methods=['POST'])
    @token_required
    def crear_interaccion(lead_id: str):
        """POST /api/leads/:id/interacciones - Registrar interacción"""
        try:
            data = request.get_json() or {}

            tipo = data.get('tipo')
            notas = data.get('notas')
            resultado = data.get('resultado')

            if not tipo:
                response, status_code = create_api_response(
                    status="error",
                    message="Campo 'tipo' es obligatorio",
                    error_code="VALIDATION_ERROR",
                    http_status=422
                )
                return jsonify(response), status_code

            # Crear interacción
            interaccion = crm_service.registrar_interaccion(lead_id, tenant_id, tipo, notas, resultado)

            response, status_code = create_api_response(
                status="success",
                message="Interacción registrada",
                data=interaccion,
                http_status=201
            )
            return jsonify(response), status_code

        except Exception as e:
            response, status_code = create_api_response(
                status="error",
                message=f"Error: {str(e)}",
                error_code="CREATE_ERROR",
                http_status=500
            )
            return jsonify(response), status_code

    return leads_bp
