"""
Inmobiliaria Valle Verde - Backend API
Aplicación Flask con arquitectura limpia, multi-tenancy segura y JWT auth
"""
import os
from uuid import UUID
from flask import Flask
from flask_cors import CORS
from supabase import create_client, Client

# Importar capas de la arquitectura
from app.core import get_config
from app.middleware import register_error_handlers
from app.routes import (
    init_health_routes,
    init_auth_routes,
    init_propiedades_routes,
    init_leads_routes
)


def create_app(config=None) -> Flask:
    """
    Factory function para crear la aplicación Flask.

    Args:
        config: Configuración personalizada (para testing)

    Returns:
        Flask application instance
    """
    app = Flask(__name__)

    # 1. ==================== CONFIGURACIÓN ====================
    cfg = config or get_config()
    cfg.validate()  # Validar que todas las variables críticas existan

    app.config.from_object(cfg)

    # 2. ==================== CORS ====================
    CORS(app, resources={
        r"/*": {
            "origins": cfg.ALLOWED_ORIGINS,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Length", "X-Total-Count"],
            "supports_credentials": True,
            "max_age": 3600
        }
    })

    # 3. ==================== SUPABASE CLIENT ====================
    try:
        supabase: Client = create_client(cfg.SUPABASE_URL, cfg.SUPABASE_KEY)
        app.supabase = supabase
    except Exception as e:
        raise ValueError(f"Error conectando a Supabase: {str(e)}")

    # 4. ==================== ERROR HANDLERS ====================
    register_error_handlers(app)

    # 5. ==================== ROUTES ====================
    # Tenant ID fijo para Valle Verde (en futuro: dinámico desde header o JWT)
    tenant_id: UUID = UUID(cfg.TENANT_ID)

    # Health check (sin autenticación)
    health_bp = init_health_routes()
    app.register_blueprint(health_bp)

    # Auth (login, logout, me)
    auth_bp = init_auth_routes(supabase, tenant_id)
    app.register_blueprint(auth_bp)

    # Propiedades (catálogo público + admin CRUD)
    propiedades_bp = init_propiedades_routes(supabase, tenant_id)
    app.register_blueprint(propiedades_bp)

    # Leads (CRM público + admin)
    leads_bp = init_leads_routes(supabase, tenant_id)
    app.register_blueprint(leads_bp)

    # Futuras rutas:
    # - agentes.py (CRUD de agentes, solo admin)
    # - interacciones.py (timeline de leads)
    # - reportes.py (KPIs, estadísticas, pipelines)

    # 6. ==================== REQUEST CONTEXT ====================
    @app.before_request
    def before_request():
        """Hook ejecutado antes de cada request"""
        # Aquí podría:
        # - Validar tenant_id desde header para futuro multi-tenancy flexible
        # - Loguear requests
        # - Configurar logging context
        pass

    @app.after_request
    def after_request(response):
        """Hook ejecutado después de cada request"""
        # Aquí podría:
        # - Agregar headers de seguridad
        # - Loguear respuestas
        response.headers['X-API-Version'] = '2.0'
        return response

    # 7. ==================== LOGGING (Opcional) ====================
    # En futuro: Agregar logger estructurado (Python logging module)
    # Integrar con servicios como Sentry para monitoreo

    return app


if __name__ == '__main__':
    # Crear app
    app = create_app()

    # Correr servidor de desarrollo
    # En producción: Usar Gunicorn
    # gunicorn wsgi:app --workers 4 --bind 0.0.0.0:5000
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    )
