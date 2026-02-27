# Inmobiliaria Valle Verde - Plataforma SaaS Multi-Tenant

**Estado:** FASE 1 Completada (Backend Refactorizado) | **Versión:** 2.0
**Última actualización:** 2026-02-26

---

## 🎯 Visión del Proyecto

**Valle Verde** es una plataforma SaaS completa diseñada para inmobiliarias de Ciudad Juárez, que proporciona:

- 📱 **Catálogo público** de propiedades (30+ activas)
- 💼 **CRM de leads** con pipeline Kanban
- 📊 **Dashboard de reportes** (KPIs, conversiones, comisiones)
- 👥 **Gestión de equipo** de agentes
- 📞 **Timeline de interacciones** (llamadas, visitas, ofertas)

Diseñada desde cero para ser **escalable, segura y lista para integrarse a una plataforma multi-tenant global** (Ejecutivos Inmobiliarios).

---

## 🚀 Quick Start

### 1. Backend (Flask REST API)

```bash
# Instalar dependencias
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env.local.dev
# Editar .env.local.dev con credenciales Supabase

# Ejecutar servidor de desarrollo
python -m app.main
# API en http://localhost:5000
```

**Endpoints principales:**
```bash
GET    /                          # Health check
POST   /api/auth/login            # Autenticación
GET    /api/propiedades           # Catálogo público
POST   /api/leads                 # Crear lead
GET    /api/leads                 # Listar leads (requiere JWT)
```

### 2. Database (Supabase PostgreSQL)

```sql
-- En Supabase: SQL Editor → Pegar contenido de database/schema.sql
-- Ejecutar completo ← Crea tablas, RLS, índices, triggers

-- Verifica que las tablas existan:
-- tenants, propiedades, imagenes_propiedades, leads, interacciones, agentes
```

### 3. Frontend (En desarrollo - FASE 3)

```bash
# Próximamente: React + Vite
```

---

## 📁 Estructura del Proyecto

```
valle-verde-plataforma/
│
├── backend/                           # API REST Flask (COMPLETADA)
│   ├── app/
│   │   ├── core/                     # Config, security, JWT
│   │   ├── middleware/               # Error handling
│   │   ├── models/                   # Pydantic schemas
│   │   ├── repositories/             # Data access + multi-tenancy
│   │   ├── services/                 # Business logic
│   │   ├── routes/                   # Endpoints Flask
│   │   └── main.py                   # Application factory
│   ├── requirements.txt
│   ├── .env.example
│   ├── wsgi.py                       # Gunicorn entry
│   └── README.md                     # Backend documentation
│
├── database/                          # SQL Schema (COMPLETADA)
│   ├── schema.sql                    # Tables, RLS, indexes, triggers
│   └── migrations/                   # Future: Migration files
│
├── frontend/                          # React + Vite (PRÓXIMA FASE)
│   ├── src/
│   │   ├── components/               # Atomic Design
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── styles/
│   └── package.json
│
├── docs/                              # Documentación
│   ├── ARQUITECTURA.md               # Architecture overview
│   ├── API.md                        # Endpoint spec
│   ├── UX-DESIGN.md                  # UI/UX flows
│   └── DATABASE.md                   # Schema documentation
│
├── FASE_1_RESUMEN.md                 # Resumen de progreso
├── README.md                         # Este archivo
└── .gitignore                        # Git configuration

```

---

## 🏗️ Arquitectura

### Backend: Clean Architecture + Multi-Tenancy

```
┌─────────────────────────────────────────┐
│         API Routes (Flask Blueprint)   │
│   GET/POST /api/{resource}/*           │
└──────────────────┬──────────────────────┘
                   │ (valida JWT + tenant)
┌──────────────────▼──────────────────────┐
│         Services Layer                  │
│   AuthService | CRMService | Etc       │
│   (Business logic + validations)        │
└──────────────────┬──────────────────────┘
                   │ (inyecta tenant_id)
┌──────────────────▼──────────────────────┐
│      Repositories Layer                 │
│   PropiedadRepository | LeadRepository  │
│   (CRUD + multi-tenancy filtering)      │
└──────────────────┬──────────────────────┘
                   │ (queries)
┌──────────────────▼──────────────────────┐
│    Supabase PostgreSQL + RLS           │
│   (Tables + Row Level Security)         │
└──────────────────────────────────────────┘
```

### Seguridad: JWT + Multi-Tenancy + RLS

```
Cliente
  │
  ├─→ POST /api/auth/login
  │       ↓
  │    Backend valida credenciales
  │    (email + password)
  │       ↓
  │    Genera JWT con tenant_id en claims
  │       ↓
  │    Retorna: { token, expiresIn, user }
  │
  ├─→ GET /api/leads
  │    Authorization: Bearer <jwt-token>
  │       ↓
  │    Backend valida JWT
  │    Extrae tenant_id del token
  │       ↓
  │    Todas las queries filtran por tenant_id
  │       ↓
  │    Supabase RLS agrega capa extra de seguridad
  │       (SELECT * WHERE tenant_id = actual_tenant)
  │
  └─→ Respuesta filtrada solo para este tenant
```

---

## 🔐 Características Implementadas (FASE 1)

### ✅ Backend

| Característica | Status | Detalles |
|---|---|---|
| **JWT Auth** | ✅ | PyJWT real, HS256, decoradores @token_required |
| **Multi-Tenancy** | ✅ | tenant_id en schema + inyección en repositories |
| **Validación** | ✅ | Pydantic schemas con validadores custom |
| **Clean Arch** | ✅ | Routes → Services → Repositories |
| **Error Handling** | ✅ | Respuestas JSON estructuradas |
| **RLS BD** | ✅ | Row Level Security en Supabase |
| **Documentation** | ✅ | README + Ejemplos curl |

### ✅ Database

| Característica | Status | Detalles |
|---|---|---|
| **Tablas** | ✅ | tenants, propiedades, leads, agentes, interacciones |
| **Indices** | ✅ | Optimizados para búsquedas rápidas |
| **RLS** | ✅ | Políticas de seguridad multi-tenant |
| **Triggers** | ✅ | updated_at automático |
| **Constraints** | ✅ | Validación de datos en BD |

### ⏳ Frontend (FASE 3)

| Característica | Status | Detalles |
|---|---|---|
| **React + Vite** | ⏳ | Próxima fase |
| **Design System** | ⏳ | Atomic Design con tokens |
| **Componentes** | ⏳ | Atoms, Molecules, Organisms |
| **Páginas** | ⏳ | Home, Led Dashboard, CRM |

---

## 📊 Stack Tecnológico

### Backend
- **Framework:** Flask 3.1.2
- **Validación:** Pydantic 2.12.5
- **Auth:** PyJWT 2.10.0
- **Database:** Supabase (PostgreSQL)
- **Server:** Gunicorn 25.1.0
- **CORS:** flask-cors 6.0.2

### Frontend (Próxima)
- **Framework:** React 18+
- **Build:** Vite
- **HTTP:** Axios
- **Router:** React Router v6
- **State:** Zustand / Context API

### Deployment
- **Backend:** Render.com
- **Frontend:** Vercel
- **Database:** Supabase

---

## 🧪 Endpoints Disponibles

### Autenticación
```bash
POST /api/auth/login              # Login (email + password)
POST /api/auth/logout             # Logout
GET  /api/auth/me                 # Obtener usuario actual
```

### Propiedades (Catálogo)
```bash
GET  /api/propiedades             # Listar (público, filtrable)
GET  /api/propiedades/:id         # Detalle (público)
POST /api/propiedades             # Crear (admin)
PUT  /api/propiedades/:id         # Editar (admin)
DELETE /api/propiedades/:id       # Archivar (admin)
```

### Leads (CRM)
```bash
GET  /api/leads                   # Listar (filtrable)
GET  /api/leads/:id               # Detalle con interacciones
POST /api/leads                   # Crear (público + admin)
PUT  /api/leads/:id               # Editar (admin)
DELETE /api/leads/:id             # Archivar (admin)
GET  /api/leads/:id/actividad     # Timeline
POST /api/leads/:id/interacciones # Registrar interacción
```

**Documentación completa:** Ver `backend/README.md`

---

## 🔄 Flujos de Usuario Principales

### 1. Visitante ve propiedades y envía lead
```
Home (catálogo) → Filtra propiedades → Ve detalle → Envía datos contacto
POST /api/leads (público) ← Sin autenticación
```

### 2. Agente revisa sus leads
```
Login → Dashboard → "Mis Leads" → Ver lead → Registrar interacción
GET /api/leads (con JWT) → Authorization requerido
POST /api/leads/:id/interacciones (con JWT)
```

### 3. Coordinador supervisa equipo
```
Login (admin) → Reportes → Ver comisiones agentes → Asignar leads
GET /api/reportes/dashboard → Ver KPIs
PUT /api/leads/:id → Cambiar asignado_a
```

---

## 📈 Próximas Fases

### FASE 2: Backend Completo
- [ ] Endpoints de Agentes (CRUD)
- [ ] Reportes (dashboard, pipeline, estadísticas)
- [ ] Upload de imágenes (Supabase Storage)
- [ ] Notificaciones por email (SendGrid)
- [ ] Tests unitarios (pytest)

### FASE 3: Frontend React
- [ ] Setup React + Vite
- [ ] Design System + componentes
- [ ] Home/Catálogo
- [ ] Dashboard admin
- [ ] Integración API

### FASE 4: Integraciones
- [ ] SendGrid (emails)
- [ ] Twilio (SMS)
- [ ] WhatsApp API
- [ ] Sincronización con portales

### FASE 5: DevOps + Observabilidad
- [ ] CI/CD (GitHub Actions)
- [ ] Monitoreo (Sentry)
- [ ] Logging (Python logging)
- [ ] Métricas (Prometheus)

---

## 🤝 Contribuir

Cuando agregues features:
1. Sigue estructura de carpetas (Clean Architecture)
2. Usa Pydantic para validación
3. Documenta con docstrings
4. Protege rutas sensibles con @token_required
5. Filtra siempre por tenant_id

---

## 📞 Soporte

**Documentación:**
- `backend/README.md` - Setup y endpoints backend
- `FASE_1_RESUMEN.md` - Resumen de progreso

**Contacto:**
- Desarrollado para Inmobiliaria Valle Verde
- Preparado para integración a Ejecutivos Inmobiliarios

---

## 📄 Licencia

**Propietario** - Inmobiliaria Valle Verde 2025

---

## ✨ Versiones

### v2.0 (Actual) - FASE 1 Completada
- ✅ Backend refactorizado con Clean Architecture
- ✅ JWT real + Multi-tenancy
- ✅ Pydantic validation
- ✅ Database schema + RLS
- ✅ 13 endpoints core

### v1.0 - Prototipo Original
- Monolito en Flask
- Mock auth
- Sin validaciones robustas

---

**¿Listo para comenzar?** → Ver `backend/README.md` para setup detallado.
