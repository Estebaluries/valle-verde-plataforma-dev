# Inmobiliaria Valle Verde - Backend API (v2.0)

Arquitectura moderna y escalable basada en **Clean Architecture** diseñada para multi-tenancy seguro.

## Arquitectura

```
┌─────────────────────────────────────────┐
│          API Routes (Flask Blueprints)  │
├─────────────────────────────────────────┤
│   health.py | auth.py | propiedades.py  │
│            leads.py | ... (futures)     │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│         Services Layer (Negocio)         │
├──────────────────────────────────────────┤
│ AuthService | CatalogoService | CRMSvc  │
│ PropiedadService | AgenteService | Rpt  │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│      Repositories (Acceso a Datos)      │
├──────────────────────────────────────────┤
│ BaseRepository | PropiedadRepository     │
│ LeadRepository | InteraccionRepository   │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│   Supabase PostgreSQL + RLS + JWT       │
└──────────────────────────────────────────┘
```

## Estructura de Carpetas

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Punto de entrada Flask
│   ├── core/
│   │   ├── config.py              # Configuración centralizada
│   │   ├── security.py            # JWT, decoradores auth
│   │   └── logger.py              # Logging (futuro)
│   ├── middleware/
│   │   ├── error_handler.py       # Errores globales
│   │   └── cors.py                # CORS dinámico
│   ├── models/
│   │   └── schemas.py             # Pydantic DTOs
│   ├── repositories/
│   │   └── base.py                # CRUD genéricos + específicos
│   ├── services/
│   │   └── services.py            # Lógica de negocio
│   └── routes/
│       ├── health.py              # Health check
│       ├── auth.py                # Login, logout, me
│       ├── propiedades.py         # Catálogo + CRUD
│       └── leads.py               # CRM leads
├── wsgi.py                         # Gunicorn entry point
├── requirements.txt                # Dependencias Python
├── .env.example                    # Template de variables
└── README.md                       # Este archivo
```

## Setup Rápido

### 1. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env.local.dev
# Editar .env.local.dev con tus credenciales Supabase
```

### 4. Ejecutar en desarrollo

```bash
# Opción 1: Flask dev server (reloader automático)
python -m app.main

# Opción 2: Gunicorn (similar a prod)
gunicorn wsgi:app --reload
```

El API estará disponible en `http://localhost:5000`

## Endpoints Principales

### Autenticación

```bash
# Login
POST /api/auth/login
{
  "email": "admin@valleverde.com",
  "password": "demo123"
}

# Obtener usuario actual (requiere JWT)
GET /api/auth/me
Authorization: Bearer <jwt-token>
```

### Propiedades (Catálogo)

```bash
# Listar propiedades (público)
GET /api/propiedades?tipo=casa&operacion=venta&limit=30

# Detalle de propiedad (público)
GET /api/propiedades/1

# Crear propiedad (admin)
POST /api/propiedades
Authorization: Bearer <jwt-admin-token>
{
  "titulo": "Casa 3 hab",
  "precio": 280000,
  "tipo": "casa",
  "operacion": "venta",
  ...
}
```

### Leads (CRM)

```bash
# Crear lead (público, desde formulario)
POST /api/leads
{
  "nombre": "María García",
  "telefono": "6144556789",
  "email": "maria@example.com",
  "propiedad_interes_id": 1
}

# Listar leads (requiere JWT)
GET /api/leads?status=nuevo&limit=50
Authorization: Bearer <jwt-token>

# Registrar interacción
POST /api/leads/<lead-id>/interacciones
Authorization: Bearer <jwt-token>
{
  "tipo": "llamada",
  "notas": "Muy interesada",
  "resultado": "positivo"
}
```

## Validación de Datos

Todos los DTOs usan **Pydantic** para validación automática en entrada:

```python
# schemas.py
class LeadCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    telefono: str = Field(...)

    @field_validator("telefono")
    def validar_telefono_mx(cls, v):
        # Valida formato mexicano (10+ dígitos)
        ...
```

**Errores de validación retornan status 422:**

```json
{
  "status": "error",
  "message": "Error de validación",
  "error_code": "VALIDATION_ERROR",
  "data": {
    "errors": [
      {"loc": ["nombre"], "msg": "..."}
    ]
  }
}
```

## Autenticación JWT

### 1. Login genera JWT

```bash
POST /api/auth/login
→ { token: "eyJhbGc...", user: {...} }
```

### 2. Token contiene claims

```python
{
  "sub": "agent-uuid",
  "email": "admin@valleverde.com",
  "tenant_id": "123e4567...",
  "role": "admin",
  "exp": 1704067200
}
```

### 3. Cliente guarda en localStorage

```javascript
localStorage.setItem('token', response.token)
```

### 4. Requests posteriores incluyen JWT

```javascript
fetch('/api/leads', {
  headers: {
    'Authorization': 'Bearer ' + token
  }
})
```

### 5. Backend valida automáticamente

```python
@app.route('/api/leads', methods=['GET'])
@token_required  # Decorador valida JWT
def listar_leads():
    # request.security contiene usuario
    agent_id = request.security.user_id
    ...
```

## Multi-Tenancy

### Actualidad

- **Tenant ID hardcodeado:** `TENANT_ID=123e4567...` en `.env`
- **Inyección automática:** Repositories inyectan `tenant_id` a todas las queries
- **Filtrado en BD:** Supabase RLS filtra resultados por tenant

### Query segura

```python
# En LeadRepository:
def get_all(self, tenant_id: UUID):
    response = self.client.table('leads') \
        .select("*") \
        .eq('tenant_id', str(tenant_id))  # ← Filtro automático
        .execute()
    return response.data
```

### Futuro (Plataforma Ejecutivos)

- Leer `tenant_id` desde JWT claims
- Validar coincidencia: JWT tenant_id == recurso tenant_id
- RLS global gestiona seguridad

## Row Level Security (RLS) en Supabase

### Habilitar RLS

```sql
ALTER TABLE propiedades ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE agentes ENABLE ROW LEVEL SECURITY;
```

### Crear políticas

```sql
-- Agentes ven solo propiedades su tenant
CREATE POLICY "tenant_access" ON propiedades
  FOR SELECT USING (
    tenant_id = current_setting('app.tenant_id')::UUID
  );
```

### Usar en queries (backend)

```python
# Supabase client internamente configura:
supabase.auth.set_session(token)
# O manually:
response = supabase.table('leads') \
    .select("*") \
    .eq('tenant_id', tenant_id) \
    .execute()
```

## Manejo de Errores

Todos los errores retornan JSON estructurado:

### 400 Bad Request
```json
{
  "status": "error",
  "message": "Solicitud inválida",
  "error_code": "BAD_REQUEST"
}
```

### 401 Unauthorized
```json
{
  "status": "error",
  "message": "No autorizado",
  "error_code": "UNAUTHORIZED"
}
```

### 403 Forbidden
```json
{
  "status": "error",
  "message": "Acceso prohibido - Rol insuficiente",
  "error_code": "FORBIDDEN"
}
```

### 404 Not Found
```json
{
  "status": "error",
  "message": "Lead no encontrado",
  "error_code": "NOT_FOUND"
}
```

### 422 Validation Error
```json
{
  "status": "error",
  "message": "Error de validación",
  "error_code": "VALIDATION_ERROR",
  "data": {
    "errors": [...]
  }
}
```

### 500 Internal Server Error
```json
{
  "status": "error",
  "message": "Error interno del servidor",
  "error_code": "INTERNAL_ERROR"
}
```

## Variables de Entorno

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| FLASK_ENV | Ambiente (development/production) | development |
| FLASK_DEBUG | Debug mode | True |
| PORT | Puerto de escucha | 5000 |
| SUPABASE_URL | URL de Supabase | https://xxx.supabase.co |
| SUPABASE_KEY | Public API Key | eyJhbGc... |
| JWT_SECRET | Clave para firmar tokens | super-secret-key |
| ALLOWED_ORIGINS | URLs permitidas (CORS) | http://localhost:3000 |
| TENANT_ID | UUID del tenant | 123e4567... |

## Próximas Etapas

### FASE 2: Expandir endpoints
- [ ] Agentes CRUD (admin)
- [ ] Reportes y estadísticas
- [ ] Interacciones CRUD
- [ ] Upload de imágenes (Supabase Storage)

### FASE 3: Integraciones
- [ ] SendGrid para emails (notificaciones de leads)
- [ ] Twilio para SMS (alertas a agentes)
- [ ] Portales (sincronización Inmuebles24, Vivanuncios)
- [ ] WhatsApp API

### FASE 4: Observabilidad
- [ ] Logging estructurado (Python logging)
- [ ] Monitoreo (Sentry)
- [ ] Metrics (Prometheus)
- [ ] Traces (OpenTelemetry)

## Testing

```bash
# (Próximamente) Ejecutar tests
pytest tests/

# Coverage
pytest --cov=app tests/
```

## Deployment

### Local (Dev)
```bash
python -m app.main
```

### Docker (Futuro)
```bash
docker build -t valle-verde-backend .
docker run -p 5000:5000 valle-verde-backend
```

### Render.com (Actual)
```bash
# Variables de entorno en Render dashboard
# Comando: gunicorn wsgi:app --bind 0.0.0.0:$PORT
```

## Stack Técnico

| Capa | Tecnología |
|------|-----------|
| Framework | Flask 3.1.2 |
| Validación | Pydantic 2.12.5 |
| Auth | PyJWT 2.10.0 |
| Database | Supabase (PostgreSQL) |
| RLS | Row Level Security |
| Server | Gunicorn 25.1.0 |
| Deployment | Render.com |
| CORS | flask-cors 6.0.2 |

## Preguntas Frecuentes

**¿Cómo agregar un nuevo endpoint?**

1. Crear función en `routes/nombre.py`
2. Registrar blueprint en `main.py`
3. Inyectar dependencias (servicios, supabase)
4. Validar con Pydantic
5. Usar `create_api_response()` para respuestas

**¿Cómo agregar validación customizada?**

```python
@field_validator("campo")
def validar_campo(cls, v):
    if condicion:
        raise ValueError("Mensaje de error")
    return v
```

**¿Cómo proteger un endpoint?**

```python
@app.route('/admin')
@token_required              # Requiere JWT
@require_role('admin')      # Requiere rol admin
def admin_endpoint():
    ...
```

## Contribuir

- Mantener estructura de carpetas
- Usar nombres PEP 8 (snake_case funciones)
- Documentar con docstrings
- Validar con Pydantic
- Usar arquitectura Clean Architecture

## Licencia

Propietario - Inmobiliaria Valle Verde 2025
