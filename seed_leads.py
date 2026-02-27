import os
import sys
from supabase import create_client
from dotenv import load_dotenv
import random

# Configuración de rutas para importar .env correctamente
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: No se encontraron las credenciales de Supabase en .env")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Datos ficticios
nombres = ["Ana García", "Carlos López", "María Rodríguez", "Jorge Martínez", "Sofía Hernández"]
intereses = ["Casa en Campestre", "Departamento Centro", "Terreno Industrial", "Local Comercial"]

def seed_leads():
    print("🌱 Iniciando siembra de datos (Seeding)...")
    
    # Obtenemos un ID de propiedad real para relacionar (opcional, o usamos NULL si la FK lo permite)
    # Para este ejemplo, asumimos que hay propiedades o dejamos el campo nulo si no es estricto
    props = supabase.table("propiedades").select("id").limit(1).execute()
    prop_id = props.data[0]['id'] if props.data else None

    leads_generados = []
    for i in range(5):
        lead = {
            "nombre": random.choice(nombres),
            "email": f"cliente{random.randint(1000,9999)}@gmail.com",
            "telefono": f"656{random.randint(1000000, 9999999)}",
            "notas": "Cliente generado automáticamente por script de seeding.",
            "propiedad_interes_id": prop_id,
            "origen": "seed_script",
            "tenant_id": "123e4567-e89b-12d3-a456-426614174000" # ID Valle Verde
        }
        leads_generados.append(lead)

    resultado = supabase.table("leads").insert(leads_generados).execute()
    print(f"✅ Se han insertado {len(resultado.data)} leads de prueba exitosamente.")

if __name__ == "__main__":
    seed_leads()