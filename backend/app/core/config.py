"""
Configuración centralizada de la aplicación
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuración base"""
    # Flask
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    TESTING = False

    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    # JWT
    JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-change-in-production")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24

    # CORS
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:5500").split(",")

    # Tenant
    TENANT_ID = os.getenv("TENANT_ID", "123e4567-e89b-12d3-a456-426614174000")  # Valle Verde hardcoded por ahora

    @staticmethod
    def validate():
        """Valida que todas las variables críticas estén configuradas"""
        required_vars = ["SUPABASE_URL", "SUPABASE_KEY"]
        missing = [var for var in required_vars if not os.getenv(var)]

        if missing:
            raise ValueError(f"¡Faltan configuraciones requeridas en .env: {', '.join(missing)}")


class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Configuración para testing"""
    DEBUG = True
    TESTING = True
    SUPABASE_URL = "http://localhost:54321"
    SUPABASE_KEY = "test-key"


# Selector de configuración por ambiente
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig
}


def get_config() -> Config:
    """Obtiene la configuración según el ambiente"""
    env = os.getenv("FLASK_ENV", "development")
    return config.get(env, config["default"])
