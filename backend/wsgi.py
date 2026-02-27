"""
WSGI entry point para Gunicorn/Render
Usado en producción para exponer la aplicación Flask
"""
from app.main import create_app

# Crear aplicación
app = create_app()

if __name__ == "__main__":
    # Este archivo se usa con: gunicorn wsgi:app
    # NO debe ejecutarse directamente
    app.run()
