# MIGRACIÓN: Arquitectura Anterior → Arquitectura v2.0

**Para:** Desarrolladores que necesitan entender qué cambió
**Estado:** FASE 1 Completada 2026-02-26

---

## 📊 Comparación: v1 vs v2

### Arquitectura

| Aspecto | v1.0 | v2.0 |
|---------|------|------|
| **Patrón** | Monolito | Clean Architecture |
| **Organización** | Todo en app.py | Routes → Services → Repos |
| **Autenticación** | Mock hardcodeado | JWT real con PyJWT |
| **Validación** | Manual (try/except) | Pydantic automático |
| **Multi-tenancy** | Schema solo | JWT + RLS + validación |
| **Error Handling** | Inconsistente | JSON estructura |
| **Config** | Hardcodeada | Centralizada .env |
| **Testing** | 0% | Pronto: pytest |

### Archivos

| Archivo v1 | Cambio | Archivo v2 |
|---|---|---|
| `app.py` (217 líneas) | ➡️ Refactorizado | `app/main.py` + servicios |
| Ninguno | ➡️ **Creado** | `app/core/config.py` |
| Ninguno | ➡️ **Creado** | `app/core/security.py` |
| Ninguno | ➡️ **Creado** | `app/middleware/error_handler.py` |
| Ninguno | ➡️ **Creado** | `app/models/schemas.py` |
| Ninguno | ➡️ **Creado** | `app/repositories/base.py` |
| Ninguno | ➡️ **Creado** | `app/services/services.py` |
| Ninguno | ➡️ **Creado** | `app/routes/*` (5 files) |
| Ninguno | ➡️ **Creado** | `database/schema.sql` |
| `requirements.txt` | 📝 Actualizado | `backend/requirements.txt` |
| `.env` | 📝 Actualizado | `backend/.env.example` |

---

## 🔄 Cómo Migrar del Código Antiguo

### Paso 1: Backend Antiguo (MANTENER COMO REFERENCIA)

El `app.py` antiguo sigue existiendo en la raíz. **NO hay que eliminarlo aún**, ya que puede servir de referencia para:
- Comparar endpoints que funcionaban
- Entender la lógica de negocio original
- Testing gradual

```
c:\...\app.py (antiguo)           ← Mantener
c:\...\backend\app\main.py (nuevo) ← Usar este ahora
```

### Paso 2: Cambios en Imports

**Antes (v1):**
```python
from app import app, CatalogoService, LeadRepository
```

**Después (v2):**
```python
from app.main import create_app
from app.services import CatalogoService, CRMService
from app.repositories import LeadRepository
from app.core import token_required
```

### Paso 3: Uso de Servicios

**Antes (v1):**
```python
catalogo_service = CatalogoService()
propiedades = catalogo_service.listar_propiedades()  # Sin tenant_id
```

**Después (v2):**
```python
from uuid import UUID

tenant_id = UUID("123e4567-e89b-12d3-a456-426614174000")
catalogo_service = CatalogoService(supabase_client)
propiedades = catalogo_service.listar_propiedades(tenant_id, limit=30)
```

### Paso 4: Validación de Datos

**Antes (v1):**
```python
@app.route('/api/leads', methods=['POST'])
def crear_lead():
    data = request.json
    # Solo validaciones manuales
    if not data.get('nombre'):
        return {"error": "nombre required"}, 400
    # Más validaciones manuales...
```

**Después (v2):**
```python
from app.models import LeadCreate

@leads_bp.route('', methods=['POST'])
def crear_lead():
    data = request.json
    # Pydantic valida automáticamente
    try:
        lead_req = LeadCreate(**data)  # ← Valida todo
    except ValueError as e:
        return create_api_response(
            status="error",
            message=str(e),
            error_code="VALIDATION_ERROR",
            http_status=422
        )
```

### Paso 5: Autenticación

**Antes (v1):**
```python
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if token != "mock-jwt-token-123":  # ← Hardcodeado
            return {"error": "Invalid token"}, 403
        return f(*args, **kwargs)
    return decorated
```

**Después (v2):**
```python
from app.core import token_required

# Decorador ya maneja JWT real
@app.route('/api/leads')
@token_required  # ← Valida JWT, extrae tenant_id
def listar_leads():
    tenant_id = request.security.tenant_id  # ← JWT payload
    user_id = request.security.user_id
    role = request.security.role
    # Ya tienes el usuario autenticado
```

### Paso 6: Multi-Tenancy

**Antes (v1):**
```python
def get_all_active(self):
    # TODO: Filtrar por tenant_id en el futuro
    return self.client.table("propiedades") \
        .select("*").eq("activo", True).execute()
```

**Después (v2):**
```python
def get_active(self, tenant_id: UUID, limit: int = 100) -> List[Dict]:
    """Obtiene solo propiedades activas del tenant"""
    response = self.client.table(self.table_name) \
        .select("*, imagenes_propiedades(url)") \
        .eq("tenant_id", str(tenant_id))     # ← Filtro automático
        .eq("activo", True) \
        .eq("estatus_publicacion", "activa") \
        .limit(limit).execute()
    return response.data if response.data else []
```

---

## 🧪 Testing: Endpoints Antigos vs Nuevos

### Health Check

**Antes:**
```bash
curl http://localhost:5000/
# Respuesta: {"status": "success", "message": "...", "data": {...}}
```

**Después:**
```bash
curl http://localhost:5000/
# Misma respuesta, pero mejor estructurada
# {"status": "success", "message": "...", "data": {"service": "...", "status": "operational"}}
```

### Login

**Antes:**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@valleverde.com","password":"demo123"}'

# Respuesta: {"status": "success", "message": "...", "data": {"token": "mock-jwt-token-123", ...}}
```

**Después:**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@valleverde.com","password":"demo123"}'

# Respuesta: Mismo estructura, pero "token" es un JWT real
# {"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", ...}
```

### Crear Lead

**Antes:**
```bash
curl -X POST http://localhost:5000/api/leads \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Juan",
    "email": "juan@test.com",
    "telefono": "6144556789"
  }'

# Respuesta: {"status": "success", ...} o {"status": "error", "error_details": "..."}
```

**Después:**
```bash
curl -X POST http://localhost:5000/api/leads \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Juan",
    "email": "juan@test.com",
    "telefono": "6144556789"
  }'

# Respuesta mejoreda: Validación automática
# Si phone es inválido: {"status": "error", "error_code": "VALIDATION_ERROR", ...}
# Si OK: {"status": "success", ...}
```

### Listar Leads (Protegido)

**Antes:**
```bash
curl http://localhost:5000/api/leads \
  -H "Authorization: mock-jwt-token-123"

# Respuesta: {"status": "success", "data": [...]}
```

**Después:**
```bash
# 1. Primero obtén JWT real
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@valleverde.com","password":"demo123"}' \
  | jq -r '.data.token')

# 2. Usa ese token
curl http://localhost:5000/api/leads \
  -H "Authorization: Bearer $TOKEN"

# Respuesta: {"status": "success", "data": [...]}
```

---

## 📚 Documentación para Devs

**Archivos clave:**

| Archivo | Propósito |
|---------|-----------|
| `backend/README.md` | Setup, endpoints, validación, JWT |
| `FASE_1_RESUMEN.md` | Resumen arquitectura + próximos pasos |
| `README.md` (raíz) | Overview del proyecto |
| `database/schema.sql` | Estructura de BD, RLS, triggers |

---

## ⚡ Cambios de Configuración

### .env

**Antes (v1):**
```
SUPABASE_URL=...
SUPABASE_KEY=...
ALLOWED_ORIGINS=...
```

**Ahora (v2):**
```
FLASK_ENV=development
SUPABASE_URL=...
SUPABASE_KEY=...
JWT_SECRET=...
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
ALLOWED_ORIGINS=...
TENANT_ID=123e4567...
```

### Variables Obligatorias

```python
# En app/core/config.py: validate()
required_vars = ["SUPABASE_URL", "SUPABASE_KEY"]
# ← Si faltan, la app NO arranca
```

---

## 🚀 Pasos para Producción (Render.com)

### Antes (v1)
1. Cambiar puerto en app.run()
2. Variables de entorno en Render
3. Executar: `gunicorn app:app`

### Ahora (v2)
1. Instalar requirements.txt
2. Variables de entorno en Render
3. Ejecutar: `gunicorn wsgi:app --bind 0.0.0.0:$PORT`

**El rest siguen igual:**
- Usar Python 3.9+
- Configurar domain
- Health checks

---

## 🔄 Roadmap de Transición

### Semana 1 (Ahora)
- ✅ Backend v2 listo
- ✅ DB schema listo
- ⏳ Testing local

### Semana 2
- [ ] Deploy backend v2 en Render (sin cambiar URL)
- [ ] Ejecutar schema.sql en Supabase
- [ ] Tests de endpoints en prod

### Semana 3
- [ ] Frontend React + Vite
- [ ] Consumir nuevo API
- [ ] Validar flujos

### Semana 4
- [ ] FASE 2: Endpoints faltantes
- [ ] Tests unitarios

---

## ❓ FAQ: Migración

**P: ¿Qué pasa con el app.py antiguo?**
R: Mantenlo como referencia. Se puede eliminar después que verifiques que todo funciona en v2.

**P: ¿Los endpoints son los mismos?**
R: Sí, pero con respuestas mejorables (error_code, estructurado). Los parámetros son los mismos.

**P: ¿Puedo usar ambas versiones en paralelo?**
R: No es recomendado. Mejor: Testear v2 local → Deploy v2 → Eliminar v1.

**P: ¿El JWT antiguo sigue funcionando?**
R: No. Los tokens nuevos son JWT reales. Necesitas hacer login nuevamente.

**P: ¿Cómo hago rollback?**
R: Guardaste el app.py antiguo? Revertir en git + redeploy versión anterior.

---

## 📝 Checklist para Validar v2

- [ ] Backend arranca: `python -m app.main`
- [ ] Health check responde: GET /
- [ ] Login retorna JWT real: POST /api/auth/login
- [ ] Listar propiedades sin auth: GET /api/propiedades
- [ ] Crear lead público: POST /api/leads
- [ ] Listar leads con JWT: GET /api/leads (usar token del login)
- [ ] BD schema ejecutado: tablas existen en Supabase
- [ ] RLS habilitado: verificar en Supabase console

---

**Documentación completa:** Ver archivos README en cada sección.
