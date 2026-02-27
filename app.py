import os
from flask import Flask, jsonify, request
from functools import wraps
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargamos secretos del .env
load_dotenv()

app = Flask(__name__)

# ==========================================
# 1. CONFIGURACIÓN DE SEGURIDAD CORS
# ==========================================
# Leemos las URLs permitidas desde Render o el .env local
origenes_secretos = os.getenv("ALLOWED_ORIGINS", "")
URLS_PERMITIDAS = [url.strip() for url in origenes_secretos.split(",") if url.strip()]

# Si por alguna razón falla, protegemos dejando solo el entorno local
if not URLS_PERMITIDAS:
    URLS_PERMITIDAS = ["http://localhost:3000", "http://127.0.0.1:5500"]

# Aplicamos el candado a todas las rutas
CORS(app, resources={r"/*": {"origins": URLS_PERMITIDAS}})

# ==========================================
# 2. CONEXIÓN A SUPABASE
# ==========================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Validación para evitar que el servidor arranque ciego
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("¡Faltan las credenciales de Supabase en las variables de entorno!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================================
# 3. CORE & UTILS (Shared Kernel)
# ==========================================
def api_response(data=None, message="Success", status=200, error=None):
    """
    Estandariza todas las respuestas de la API (JSON Envelope Pattern).
    Esto facilita el consumo desde el Frontend y futuros clientes.
    """
    response = {
        "status": "success" if status < 400 else "error",
        "message": message,
        "data": data,
        "timestamp": os.getenv("FLASK_ENV", "dev")
    }
    if error:
        response["error_details"] = str(error)
    return jsonify(response), status

def token_required(f):
    """
    Middleware (Decorador) para proteger rutas privadas.
    Verifica que el Header 'Authorization' contenga el token válido.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return api_response(status=401, message="Acceso denegado: Token faltante")
        
        # Validación del Mock (En producción aquí decodificaríamos el JWT real)
        if token != "mock-jwt-token-123":
            return api_response(status=403, message="Acceso denegado: Token inválido")
            
        return f(*args, **kwargs)
    return decorated

# ==========================================
# 4. CAPA DE REPOSITORIO (Data Access Layer)
# ==========================================
class BaseRepository:
    def __init__(self, client: Client):
        self.client = client

class PropiedadRepository(BaseRepository):
    def get_all_active(self):
        # TODO: Filtrar por tenant_id en el futuro
        return self.client.table("propiedades").select("*, imagenes(url)").eq("activo", True).execute()

class LeadRepository(BaseRepository):
    def create(self, lead_data):
        return self.client.table("leads").insert(lead_data).execute()

    def get_all(self):
        # Obtenemos leads y el título de la propiedad relacionada
        return self.client.table("leads").select("*, propiedades(titulo)").order("created_at", desc=True).execute()

class AgenteRepository(BaseRepository):
    def get_all(self):
        # Simulamos tabla agentes si no existe aún
        try:
            return self.client.table("agentes").select("*").eq("activo", True).execute()
        except Exception:
            return None

# ==========================================
# 5. CAPA DE SERVICIO (Business Logic Layer)
# ==========================================
class CatalogoService:
    def __init__(self):
        self.repo = PropiedadRepository(supabase)

    def listar_propiedades(self):
        # Aquí iría lógica de negocio: formateo de precios, ordenamiento, etc.
        resultado = self.repo.get_all_active()
        return resultado.data

class CRMService:
    def __init__(self):
        self.repo = LeadRepository(supabase)

    def registrar_lead(self, datos):
        # 1. Validación de Negocio (Fail Fast)
        campos_requeridos = ['nombre', 'email', 'telefono', 'propiedad_interes_id']
        errores = [campo for campo in campos_requeridos if not datos.get(campo)]
        
        if errores:
            raise ValueError(f"Faltan campos obligatorios: {', '.join(errores)}")

        # 2. Preparación del DTO
        nuevo_lead = {
            "nombre": datos['nombre'],
            "email": datos['email'],
            "telefono": datos['telefono'],
            "notas": datos.get('notas', ''),
            "propiedad_interes_id": datos['propiedad_interes_id'],
            "origen": "web_valle_verde_dev",
            # "tenant_id": "..." # Inyectar aquí en el futuro
        }
        
        # 3. Persistencia
        return self.repo.create(nuevo_lead).data

    def listar_leads(self):
        resultado = self.repo.get_all()
        return resultado.data

class AuthService:
    def login(self, email, password):
        # Mock de autenticación para el Dashboard
        if email == "admin@valleverde.com" and password == "demo123":
            return {"token": "mock-jwt-token-123", "role": "admin", "nombre": "Admin Valle Verde"}
        raise ValueError("Credenciales inválidas")

# Instancias Globales (Singleton pattern simplificado)
catalogo_service = CatalogoService()
crm_service = CRMService()
auth_service = AuthService()

# ==========================================
# 6. CONTROLADORES (API Routes)
# ==========================================

@app.route('/', methods=['GET'])
def health_check():
    return api_response(
        message="Motor de Inmobiliaria Valle Verde (Dev) funcionando al 100% 🚀",
        data={"version": "1.0.0", "mode": "tenant-isolated"}
    )

# --- MÓDULO: PROPIEDADES ---
@app.route('/api/propiedades', methods=['GET'])
def obtener_propiedades():
    try:
        data = catalogo_service.listar_propiedades()
        return api_response(data=data, message="Inventario recuperado exitosamente")
    except Exception as e:
        return api_response(status=500, message="Error al conectar con inventario", error=e)

# --- MÓDULO: LEADS (CRM) ---
@app.route('/api/leads', methods=['POST'])
def crear_lead():
    try:
        data = crm_service.registrar_lead(request.json)
        return api_response(data=data, message="Lead registrado correctamente", status=201)
    except ValueError as ve:
        return api_response(status=400, message=str(ve))
    except Exception as e:
        print(f"Error al guardar lead: {e}")
        return api_response(status=500, message="No se pudo registrar el interesado", error=e)

@app.route('/api/leads', methods=['GET'])
@token_required
def listar_leads():
    try:
        data = crm_service.listar_leads()
        return api_response(data=data, message="Leads recuperados")
    except Exception as e:
        return api_response(status=500, message="Error al obtener leads", error=e)

# --- MÓDULO: AGENTES & AUTH (Nuevo) ---
@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        creds = request.json
        user = auth_service.login(creds.get('email'), creds.get('password'))
        return api_response(data=user, message="Bienvenido al Dashboard")
    except ValueError as e:
        return api_response(status=401, message=str(e))

@app.route('/api/agentes', methods=['GET'])
def listar_agentes():
    # Endpoint para mostrar equipo en "Sobre Nosotros"
    repo = AgenteRepository(supabase)
    agentes = repo.get_all()
    return api_response(data=agentes.data if agentes else [], message="Lista de agentes")

if __name__ == '__main__':
    app.run(debug=True, port=5000)