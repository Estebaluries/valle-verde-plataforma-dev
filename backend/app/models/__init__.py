"""
Models - Schemas de datos y DTOs
"""
from .schemas import (
    # Enums
    OperacionEnum,
    TipoPropiedad,
    StatusLead,
    RolAgente,
    # Auth
    LoginRequest,
    LoginResponse,
    UserResponse,
    # Leads
    LeadCreate,
    LeadUpdate,
    LeadResponse,
    # Propiedades
    PropiedadCreate,
    PropiedadUpdate,
    PropiedadResponse,
    # Interacciones
    InteraccionCreate,
    InteraccionResponse,
    # Agentes
    AgenteCreate,
    AgenteResponse,
    # Generics
    APIResponse,
    PaginatedResponse
)

__all__ = [
    "OperacionEnum",
    "TipoPropiedad",
    "StatusLead",
    "RolAgente",
    "LoginRequest",
    "LoginResponse",
    "UserResponse",
    "LeadCreate",
    "LeadUpdate",
    "LeadResponse",
    "PropiedadCreate",
    "PropiedadUpdate",
    "PropiedadResponse",
    "InteraccionCreate",
    "InteraccionResponse",
    "AgenteCreate",
    "AgenteResponse",
    "APIResponse",
    "PaginatedResponse"
]
