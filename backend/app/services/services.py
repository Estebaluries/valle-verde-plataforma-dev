"""
Services - Capa de lógica de negocio
Orquesta repositories y aplica reglas de negocio
"""
from uuid import UUID
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from supabase import Client

from ..repositories import (
    PropiedadRepository,
    LeadRepository,
    InteraccionRepository,
    AgenteRepository
)
from ..models import (
    LeadCreate,
    LeadUpdate,
    PropiedadCreate,
    PropiedadUpdate,
    AgenteCreate,
    UserResponse
)
from ..middleware import (
    ValidationError,
    NotFoundError,
    ConflictError,
    UnauthorizedError
)
from ..core import JWTManager


class AuthService:
    """
    Servicio de autenticación.
    Maneja login de agentes, validación de credenciales y generación de JWT.
    """

    def __init__(self, supabase_client: Client, jwt_manager: JWTManager):
        self.client = supabase_client
        self.jwt = jwt_manager
        self.agente_repo = AgenteRepository(supabase_client)

    def login(self, email: str, password: str, tenant_id: UUID) -> Dict:
        """
        Autentica un agente y retorna JWT.

        Args:
            email: Email del agente
            password: Contraseña (en producción: contra Supabase Auth)
            tenant_id: Tenant ID

        Returns:
            {
                "token": "jwt-token",
                "expiresIn": 86400,
                "user": UserResponse
            }

        Raises:
            UnauthorizedError si credenciales son inválidas
        """
        # 1. Mock auth (En producción: usar Supabase Auth)
        if email == "admin@valleverde.com" and password == "demo123":
            agente_id = "b0000000-0000-0000-0000-000000000001"
            nombre = "Admin Valle Verde"
            rol = "admin"
        else:
            # Buscar agente en BD
            agente = self.agente_repo.find_by_email(email, tenant_id)
            if not agente:
                raise UnauthorizedError("Email o contraseña incorrectos")

            # En producción: validar contra Supabase Auth
            agente_id = agente.get("id")
            nombre = agente.get("nombre")
            rol = agente.get("rol", "agente")

        # 2. Crear JWT
        payload = {
            "sub": agente_id,
            "email": email,
            "tenant_id": str(tenant_id),
            "role": rol
        }

        token = self.jwt.create_token(payload)
        exp_time = int(self.jwt.expiration_hours * 3600)

        # 3. Retornar respuesta
        user = UserResponse(
            id=agente_id,
            email=email,
            nombre=nombre,
            role=rol,
            tenant_id=str(tenant_id)
        )

        return {
            "token": token,
            "expiresIn": exp_time,
            "user": user.model_dump()
        }


class CatalogoService:
    """
    Servicio de catálogo público de propiedades.
    Obtiene propiedades activas del tenant para visitantes.
    """

    def __init__(self, supabase_client: Client):
        self.repo = PropiedadRepository(supabase_client)

    def listar_propiedades(self, tenant_id: UUID, limit: int = 30, offset: int = 0) -> List[Dict]:
        """Obtiene propiedades activas del catálogo público"""
        return self.repo.get_active(tenant_id, limit, offset)

    def obtener_propiedad(self, propiedad_id: int, tenant_id: UUID) -> Dict:
        """Obtiene detalle de una propiedad"""
        propiedad = self.repo.find_by_id(propiedad_id, tenant_id)
        if not propiedad:
            raise NotFoundError("Propiedad no encontrada")
        return propiedad

    def buscar_propiedades(self, tenant_id: UUID, tipo: Optional[str] = None,
                           operacion: Optional[str] = None, colonia: Optional[str] = None,
                           min_precio: Optional[float] = None, max_precio: Optional[float] = None,
                           limit: int = 30) -> List[Dict]:
        """Búsqueda avanzada de propiedades con filtros"""
        return self.repo.search_by_filters(tenant_id, tipo, operacion, colonia, min_precio,
                                            max_precio, limit)


class CRMService:
    """
    Servicio de CRM - Gestión de leads.
    Registra, actualiza y genera reportes sobre leads.
    """

    def __init__(self, supabase_client: Client):
        self.client = supabase_client
        self.lead_repo = LeadRepository(supabase_client)
        self.interaccion_repo = InteraccionRepository(supabase_client)
        self.propiedad_repo = PropiedadRepository(supabase_client)

    def registrar_lead_public(self, tenant_id: UUID, datos: LeadCreate) -> Dict:
        """
        Registra un lead desde el formulario público de catálogo.
        Validación básica + inyección de tenant_id.
        """
        # Validar teléfono mexicano
        telefono = ''.join(c for c in datos.telefono if c.isdigit())
        if len(telefono) < 10:
            raise ValidationError("Teléfono debe tener al menos 10 dígitos")

        # Preparar datos
        lead_data = {
            "nombre": datos.nombre,
            "email": datos.email,
            "telefono": telefono,
            "notas": datos.notas,
            "propiedad_interes_id": datos.propiedad_interes_id,
            "origen": datos.origen or "web",
            "status": "nuevo",
            "tenant_id": str(tenant_id)
        }

        # Crear en BD
        nuevo_lead = self.lead_repo.create(tenant_id, lead_data)

        # TODO: En próximas fases, aquí se enviaría email a admin
        # email_service.notify_new_lead(nuevo_lead, tenant_id)

        return nuevo_lead

    def obtener_lead(self, lead_id: str, tenant_id: UUID) -> Dict:
        """Obtiene un lead con sus interacciones"""
        lead = self.lead_repo.find_with_details(lead_id, tenant_id)
        if not lead:
            raise NotFoundError("Lead no encontrado")
        return lead

    def listar_leads(self, tenant_id: UUID, status: Optional[str] = None,
                     agente_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """
        Lista leads con filtros opcionales.
        Usualmente para dashboard admin que ve todos los leads del tenant.
        """
        if agente_id:
            # Leads asignados a un agente específico
            return self.lead_repo.get_by_agente(tenant_id, agente_id, limit)
        elif status:
            # Leads por status
            return self.lead_repo.get_by_status(tenant_id, status, limit)
        else:
            # Todos los leads del tenant
            return self.lead_repo.find_all(tenant_id, limit)

    def actualizar_lead(self, lead_id: str, tenant_id: UUID, datos: LeadUpdate) -> Dict:
        """Actualiza un lead existente"""
        # Validar que el lead existe y pertenece al tenant
        lead = self.lead_repo.find_by_id(lead_id, tenant_id)
        if not lead:
            raise NotFoundError("Lead no encontrado")

        # Preparar datos de actualización (sin None values)
        update_data = {k: v for k, v in datos.model_dump().items() if v is not None}

        # Actualizar
        lead_actualizado = self.lead_repo.update(lead_id, tenant_id, update_data)
        return lead_actualizado

    def registrar_interaccion(self, lead_id: str, tenant_id: UUID, tipo: str, notas: Optional[str],
                              resultado: Optional[str]) -> Dict:
        """
        Registra una interacción (llamada, visita, email, etc.) en la timeline del lead.
        """
        # Validar que el lead existe y pertenece al tenant
        lead = self.lead_repo.find_by_id(lead_id, tenant_id)
        if not lead:
            raise NotFoundError("Lead no encontrado")

        # Crear interacción
        interaccion_data = {
            "lead_id": lead_id,
            "tipo": tipo,
            "notas": notas,
            "resultado": resultado,
            "fecha": datetime.utcnow().isoformat()
        }

        return self.interaccion_repo.create_for_lead(lead_id, interaccion_data)

    def obtener_timeline(self, lead_id: str, tenant_id: UUID) -> List[Dict]:
        """Obtiene la timeline de interacciones de un lead"""
        # Validar pertenencia al tenant
        lead = self.lead_repo.find_by_id(lead_id, tenant_id)
        if not lead:
            raise NotFoundError("Lead no encontrado")

        return self.interaccion_repo.get_by_lead(lead_id)


class PropiedadService:
    """
    Servicio de gestión de propiedades.
    CRUD completo (solo para ADMIN).
    """

    def __init__(self, supabase_client: Client):
        self.repo = PropiedadRepository(supabase_client)

    def crear_propiedad(self, tenant_id: UUID, datos: PropiedadCreate) -> Dict:
        """Crea una propiedad (solo ADMIN)"""
        # Validaciones adicionales de negocio
        if datos.precio <= 0:
            raise ValidationError("El precio debe ser mayor a 0")

        propiedad_data = {
            **datos.model_dump(exclude_none=True),
            "tenant_id": str(tenant_id),
            "activo": True
        }

        return self.repo.create(tenant_id, propiedad_data)

    def actualizar_propiedad(self, propiedad_id: int, tenant_id: UUID,
                             datos: PropiedadUpdate) -> Dict:
        """Actualiza una propiedad existente"""
        propiedad = self.repo.find_by_id(propiedad_id, tenant_id)
        if not propiedad:
            raise NotFoundError("Propiedad no encontrada")

        update_data = {k: v for k, v in datos.model_dump().items() if v is not None}
        return self.repo.update(propiedad_id, tenant_id, update_data)

    def listar_propiedades(self, tenant_id: UUID, limit: int = 100) -> List[Dict]:
        """Lista todas las propiedades del tenant (incluyendo inactivas)"""
        return self.repo.find_all(tenant_id, limit)

    def archivar_propiedad(self, propiedad_id: int, tenant_id: UUID) -> bool:
        """Marca una propiedad como inactiva (soft delete)"""
        return self.repo.delete(propiedad_id, tenant_id)


class AgenteService:
    """
    Servicio de gestión de equipo de agentes.
    CRUD completo (solo para ADMIN).
    """

    def __init__(self, supabase_client: Client):
        self.repo = AgenteRepository(supabase_client)

    def crear_agente(self, tenant_id: UUID, datos: AgenteCreate) -> Dict:
        """Crea un nuevo agente en el equipo"""
        # Validar que el email no esté duplicado
        existente = self.repo.find_by_email(datos.email, tenant_id)
        if existente:
            raise ConflictError(f"Email {datos.email} ya está registrado")

        agente_data = {
            **datos.model_dump(exclude_none=True),
            "tenant_id": str(tenant_id),
            "activo": True,
            "leads_activos": 0,
            "leads_cerrados": 0,
            "comisiones_pendientes": 0.0
        }

        return self.repo.create(tenant_id, agente_data)

    def actualizar_agente(self, agente_id: str, tenant_id: UUID, datos: AgenteCreate) -> Dict:
        """Actualiza datos de un agente"""
        agente = self.repo.find_by_id(agente_id, tenant_id)
        if not agente:
            raise NotFoundError("Agente no encontrado")

        update_data = {k: v for k, v in datos.model_dump().items() if v is not None}
        return self.repo.update(agente_id, tenant_id, update_data)

    def listar_agentes(self, tenant_id: UUID) -> List[Dict]:
        """Lista todos los agentes activos del tenant"""
        return self.repo.get_active(tenant_id)

    def desactivar_agente(self, agente_id: str, tenant_id: UUID) -> bool:
        """Desactiva un agente (soft delete)"""
        return self.repo.delete(agente_id, tenant_id)


class ReporteService:
    """
    Servicio de reportes y analítica.
    Genera estadísticas, pipelines, y KPIs.
    """

    def __init__(self, supabase_client: Client):
        self.client = supabase_client
        self.lead_repo = LeadRepository(supabase_client)

    def obtener_kpis_dashboard(self, tenant_id: UUID) -> Dict:
        """Obtiene KPIs principales para dashboard"""
        # TODO: Implementar queries más sofisticadas con agregaciones
        # Por ahora, valores calculados simples

        leads_nuevos = len(self.lead_repo.get_by_status(tenant_id, "nuevo", limit=999))
        leads_cerrados = len(self.lead_repo.get_by_status(tenant_id, "cerrado", limit=999))

        return {
            "leads_nuevos": leads_nuevos,
            "leads_activos": leads_nuevos + len(self.lead_repo.get_by_status(tenant_id, "contactado", limit=999)),
            "leads_cerrados": leads_cerrados,
            "propiedades_activas": 30,  # TODO: Calc real
            "ingresos_mes": 0.0  # TODO: Calc real
        }

    def obtener_pipeline(self, tenant_id: UUID) -> Dict:
        """Obtiene estado del pipeline por etapa"""
        etapas = ["nuevo", "contactado", "citado", "oferta", "cerrado"]
        pipeline = {}

        for etapa in etapas:
            count = len(self.lead_repo.get_by_status(tenant_id, etapa, limit=999))
            pipeline[etapa] = count

        return pipeline

    def obtener_stats_agente(self, agente_id: str, tenant_id: UUID) -> Dict:
        """Obtiene estadísticas de un agente específico"""
        leads_agente = self.lead_repo.get_by_agente(tenant_id, agente_id, limit=999)

        leads_activos = [l for l in leads_agente if l.get("status") != "cerrado"]
        leads_cerrados = [l for l in leads_agente if l.get("status") == "cerrado"]

        conversion_rate = (len(leads_cerrados) / len(leads_agente) * 100) if leads_agente else 0

        return {
            "leads_activos": len(leads_activos),
            "leads_cerrados": len(leads_cerrados),
            "leads_totales": len(leads_agente),
            "conversion_rate": round(conversion_rate, 2),
            "comisiones_pendientes": sum([l.get("comision_monto", 0) for l in leads_cerrados])
        }
