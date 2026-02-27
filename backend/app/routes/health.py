"""
Routes: Health Check
GET / - Health check del servicio
GET /health - Health check (alias)
"""
from flask import Blueprint, jsonify
from datetime import datetime

from ..middleware import create_api_response

health_bp = Blueprint('health', __name__)


def init_health_routes():
    """Factory para health routes (sin dependencias)"""

    @health_bp.route('/', methods=['GET'])
    def root():
        """GET / - Root con health check"""
        response, status = create_api_response(
            status="success",
            message="Inmobiliaria Valle Verde - Backend API (v2.0)",
            data={
                "service": "Valle Verde API",
                "version": "2.0.0",
                "environment": "development",
                "timestamp": datetime.utcnow().isoformat(),
                "architecture": "clean-architecture",
                "status": "operational"
            },
            http_status=200
        )
        return jsonify(response), status

    @health_bp.route('/health', methods=['GET'])
    def health_check():
        """GET /health - Healthcheck simple"""
        response, status = create_api_response(
            status="success",
            message="Sistema operativo",
            data={"status": "healthy"},
            http_status=200
        )
        return jsonify(response), status

    return health_bp
