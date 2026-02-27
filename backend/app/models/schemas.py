"""
Pydantic schemas para validación de datos de entrada y respuestas
Estos DTOs aseguran que los datos cumplan con los requisitos antes de llegar a services
"""
from pydantic import BaseModel, EmailStr, Field, validator, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ==================== ENUMERACIONES ====================

class OperacionEnum(str):
    """Tipos de operación permitidas"""
    VENTA = "venta"
    RENTA = "renta"
    VENTA_RENTA = "venta_renta"


class TipoPropiedad(str):
    """Tipos de propiedades"""
    CASA = "casa"
    APARTAMENTO = "apartamento"
    COMERCIAL = "comercial"
    LOTE = "lote"
    OTRO = "otro"


class StatusLead(str):
    """Estados posibles de un lead"""
    NUEVO = "nuevo"
    CONTACTADO = "contactado"
    CITADO = "citado"
    OFERTA = "oferta"
    CERRADO = "cerrado"
    PERDIDO = "perdido"


class RolAgente(str):
    """Roles de agentes"""
    ADMIN = "admin"
    COORDINADOR = "coordinador"
    AGENTE = "agente"
    GERENTE = "gerente"


# ==================== AUTENTICACIÓN ====================

class LoginRequest(BaseModel):
    """Request para POST /api/auth/login"""
    email: EmailStr
    password: str = Field(..., min_length=4, description="Contraseña mínimo 4 caracteres")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "admin@valleverde.com",
                "password": "demo123"
            }
        }


class UserResponse(BaseModel):
    """Response de usuario autenticado"""
    id: str
    email: str
    nombre: str
    role: RolAgente
    tenant_id: str
    foto_url: Optional[str] = None


class LoginResponse(BaseModel):
    """Response para POST /api/auth/login"""
    token: str
    expiresIn: int = Field(86400, description="Segundos hasta expiración")
    user: UserResponse


# ==================== LEADS ====================

class LeadCreate(BaseModel):
    """Request para crear un lead"""
    nombre: str = Field(..., min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    telefono: str = Field(..., min_length=10, max_length=20)
    notas: Optional[str] = Field(None, max_length=500)
    propiedad_interes_id: Optional[int] = None
    origen: Optional[str] = Field("web", description="web, whatsapp, referencia, portal")

    @field_validator("telefono")
    def validar_telefono_mx(cls, v):
        """Valida formato de teléfono mexicano (básico)"""
        # Remover espacios y caracteres especiales
        telefono_limpio = ''.join(c for c in v if c.isdigit())

        if len(telefono_limpio) < 10:
            raise ValueError("Teléfono debe tener al menos 10 dígitos")

        return telefono_limpio

    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "María García",
                "email": "maria.garcia@example.com",
                "telefono": "6144556789",
                "notas": "Interesada en casas de 3 habitaciones",
                "propiedad_interes_id": 1,
                "origen": "web"
            }
        }


class LeadUpdate(BaseModel):
    """Request para actualizar un lead"""
    nombre: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, min_length=10, max_length=20)
    notas: Optional[str] = Field(None, max_length=500)
    status: Optional[StatusLead] = None
    asignado_a: Optional[str] = None  # UUID del agente
    probabilidad: Optional[int] = Field(None, ge=0, le=100)
    proxima_accion_fecha: Optional[str] = None
    proxima_accion_descripcion: Optional[str] = None

    @field_validator("telefono")
    def validar_telefono_mx(cls, v):
        if v is None:
            return v
        telefono_limpio = ''.join(c for c in v if c.isdigit())
        if len(telefono_limpio) < 10:
            raise ValueError("Teléfono debe tener al menos 10 dígitos")
        return telefono_limpio


class LeadResponse(BaseModel):
    """Response de un lead completo"""
    id: str
    nombre: str
    email: Optional[str]
    telefono: str
    propiedad_interes_id: Optional[int]
    origen: str
    notas: Optional[str]
    status: StatusLead
    asignado_a: Optional[str]
    probabilidad: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== PROPIEDADES ====================

class PropiedadCreate(BaseModel):
    """Request para crear una propiedad (solo ADMIN)"""
    titulo: str = Field(..., min_length=5, max_length=255)
    descripcion: Optional[str] = Field(None, max_length=2000)
    precio: float = Field(..., gt=0, description="Precio debe ser > 0")
    moneda: str = Field("MXN", max_length=3)
    operacion: OperacionEnum
    tipo: TipoPropiedad
    colonia: str = Field(..., min_length=2, max_length=100)
    fraccionamiento: Optional[str] = Field(None, max_length=100)
    calle: Optional[str] = None
    numero: Optional[str] = None
    habitaciones: int = Field(0, ge=0)
    baños: int = Field(0, ge=0)
    m2_construccion: Optional[float] = Field(None, gt=0)
    m2_terreno: Optional[float] = Field(None, gt=0)
    estacionamientos: int = Field(1, ge=0)
    amenidades: Optional[List[str]] = None
    estatus_publicacion: str = Field("activa")
    estatus_credito: Optional[str] = None
    banco: Optional[str] = None
    propiedad_id_externo: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "titulo": "Casa Moderna en Col. Juárez",
                "descripcion": "Casa 3 hab, 2 baños, con alberca",
                "precio": 280000,
                "moneda": "MXN",
                "operacion": "venta",
                "tipo": "casa",
                "colonia": "Col. Juárez",
                "habitaciones": 3,
                "baños": 2,
                "amenidades": ["alberca", "jardin", "estacionamiento"]
            }
        }


class PropiedadUpdate(BaseModel):
    """Request para actualizar una propiedad"""
    titulo: Optional[str] = Field(None, min_length=5, max_length=255)
    descripcion: Optional[str] = None
    precio: Optional[float] = Field(None, gt=0)
    operacion: Optional[OperacionEnum] = None
    colonia: Optional[str] = None
    estatus_publicacion: Optional[str] = None
    estacionamientos: Optional[int] = Field(None, ge=0)
    amenidades: Optional[List[str]] = None


class PropiedadResponse(BaseModel):
    """Response de una propiedad"""
    id: int
    titulo: str
    descripcion: Optional[str]
    precio: float
    moneda: str
    operacion: str
    tipo: str
    colonia: str
    habitaciones: int
    baños: int
    m2_construccion: Optional[float]
    m2_terreno: Optional[float]
    estacionamientos: int
    activo: bool
    estatus_publicacion: str
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== INTERACCIONES ====================

class InteraccionCreate(BaseModel):
    """Request para crear una interacción"""
    lead_id: str
    tipo: str = Field(..., description="llamada, visita, email, whatsapp, oferta, otro")
    notas: Optional[str] = None
    resultado: Optional[str] = Field(None, description="positivo, neutral, negativo, pendiente")
    propiedad_id: Optional[int] = None
    proxima_contacto_fecha: Optional[str] = None


class InteraccionResponse(BaseModel):
    """Response de una interacción"""
    id: str
    lead_id: str
    tipo: str
    fecha: datetime
    notas: Optional[str]
    resultado: Optional[str]
    registrado_por: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== AGENTES ====================

class AgenteCreate(BaseModel):
    """Request para crear un agente (ADMIN)"""
    nombre: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    telefono: Optional[str] = None
    rol: RolAgente = Field("agente")
    foto_url: Optional[str] = None


class AgenteResponse(BaseModel):
    """Response de un agente"""
    id: str
    nombre: str
    email: str
    telefono: Optional[str]
    rol: str
    foto_url: Optional[str]
    activo: bool
    leads_activos: int = 0
    leads_cerrados: int = 0
    comisiones_pendientes: float = 0.0
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== RESPONSES GENÉRICAS ====================

class APIResponse(BaseModel):
    """Response envelope para todos los endpoints"""
    status: str = Field(..., description="success o error")
    message: str
    data: Optional[dict] = None
    timestamp: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Operación exitosa",
                "data": {}
            }
        }


class PaginatedResponse(BaseModel):
    """Response para listados paginados"""
    data: list
    total: int
    page: int
    limit: int
    pages: int

    @field_validator('pages', mode='after')
    def calculate_pages(cls, v, info):
        if info.data.get('limit') and info.data.get('total'):
            return (info.data['total'] + info.data['limit'] - 1) // info.data['limit']
        return 0
