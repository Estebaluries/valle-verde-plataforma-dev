"""
Routes - Enrutamiento de la aplicación Flask
"""
from .health import init_health_routes
from .auth import init_auth_routes
from .propiedades import init_propiedades_routes
from .leads import init_leads_routes

__all__ = [
    "init_health_routes",
    "init_auth_routes",
    "init_propiedades_routes",
    "init_leads_routes"
]
