import os
from flask import Flask, jsonify, request
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
# 3. RUTAS DE LA API
# ==========================================

# --- RUTA 0: Health Check (La prueba de vida) ---
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        "status": "online", 
        "message": "Motor de Inmobiliaria Valle Verde (Dev) funcionando al 100% 🚀",
        "clientes_autorizados": len(URLS_PERMITIDAS)
    }), 200

# --- RUTA 1: Obtener Propiedades (Con sus imágenes) ---
@app.route('/api/propiedades', methods=['GET'])
def obtener_propiedades():
    try:
        respuesta = supabase.table("propiedades").select("*, imagenes(url)").eq("activo", True).execute()
        return jsonify(respuesta.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- RUTA 2: Recibir Leads del Formulario ---
@app.route('/api/leads', methods=['POST'])
def crear_lead():
    try:
        datos_cliente = request.json
        
        resultado = supabase.table("leads").insert({
            "nombre": datos_cliente['nombre'],
            "email": datos_cliente['email'],
            "telefono": datos_cliente['telefono'],
            "notas": datos_cliente.get('notas', ''),
            "propiedad_interes_id": datos_cliente['propiedad_interes_id'],
            "origen": "web_valle_verde_dev"
        }).execute()
        
        return jsonify({"status": "success", "data": resultado.data}), 201
    except Exception as e:
        print(f"Error al guardar lead: {e}")
        return jsonify({"error": "No se pudo registrar el interesado"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)