"""
Capa de Repositories - Acceso a datos desde Supabase
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from supabase import Client
from datetime import datetime

from ..middleware import NotFoundError


class BaseRepository:
    """
    Clase base para todos los repositorios.
    Proporciona métodos CRUD genéricos usando Supabase.
    """

    def __init__(self, client: Client, table_name: str):
        self.client = client
        self.table_name = table_name

    def find_by_id(self, id: Any, tenant_id: Optional[UUID] = None) -> Optional[Dict]:
        """Obtiene un registro por ID"""
        query = self.client.table(self.table_name).select("*")

        if tenant_id:
            query = query.eq("tenant_id", str(tenant_id))

        response = query.eq("id", str(id)).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        return None

    def find_all(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Obtiene todos los registros del tenant con paginación"""
        response = self.client.table(self.table_name).select("*") \
            .eq("tenant_id", str(tenant_id)) \
            .limit(limit) \
            .offset(offset) \
            .order("created_at", desc=True) \
            .execute()

        return response.data if response.data else []

    def count(self, tenant_id: UUID) -> int:
        """Cuenta registros del tenant"""
        response = self.client.table(self.table_name).select("id", count="exact") \
            .eq("tenant_id", str(tenant_id)) \
            .execute()

        return response.count if hasattr(response, 'count') else 0

    def create(self, tenant_id: UUID, data: Dict) -> Dict:
        """Crea un nuevo registro"""
        # Inyectar tenant_id automáticamente
        data["tenant_id"] = str(tenant_id)
        data["created_at"] = datetime.utcnow().isoformat()
        data["updated_at"] = datetime.utcnow().isoformat()

        response = self.client.table(self.table_name).insert(data).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        raise Exception(f"Error al crear {self.table_name}")

    def update(self, id: Any, tenant_id: UUID, data: Dict) -> Dict:
        """Actualiza un registro, asegurando que pertenece al tenant"""
        # Remover IDs y timestamps que no debería actualizar
        data.pop("id", None)
        data.pop("tenant_id", None)
        data.pop("created_at", None)

        data["updated_at"] = datetime.utcnow().isoformat()

        # Verificar que el recurso pertenece al tenant
        existing = self.find_by_id(id, tenant_id)
        if not existing:
            raise NotFoundError(f"{self.table_name} no encontrado o no pertenece a tu tenant")

        response = self.client.table(self.table_name).update(data) \
            .eq("id", str(id)) \
            .eq("tenant_id", str(tenant_id)) \
            .execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        raise Exception(f"Error al actualizar {self.table_name}")

    def delete(self, id: Any, tenant_id: UUID) -> bool:
        """Soft-delete: marca un registro como inactivo"""
        existing = self.find_by_id(id, tenant_id)
        if not existing:
            raise NotFoundError(f"{self.table_name} no encontrado")

        response = self.client.table(self.table_name).update({"activo": False, "updated_at": datetime.utcnow().isoformat()}) \
            .eq("id", str(id)) \
            .eq("tenant_id", str(tenant_id)) \
            .execute()

        return bool(response.data)

    def find_with_filters(self, tenant_id: UUID, filters: Dict[str, Any], limit: int = 100,
                          offset: int = 0) -> List[Dict]:
        """Busca registros con filtros adicionales"""
        query = self.client.table(self.table_name).select("*").eq("tenant_id", str(tenant_id))

        for key, value in filters.items():
            if value is not None:
                query = query.eq(key, value)

        response = query.limit(limit).offset(offset).execute()
        return response.data if response.data else []


class PropiedadRepository(BaseRepository):
    """Repository específico para la tabla propiedades"""

    def __init__(self, client: Client):
        super().__init__(client, "propiedades")

    def get_active(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Obtiene solo propiedades activas y publicadas"""
        response = self.client.table(self.table_name).select("*, imagenes_propiedades(url)") \
            .eq("tenant_id", str(tenant_id)) \
            .eq("activo", True) \
            .eq("estatus_publicacion", "activa") \
            .limit(limit) \
            .offset(offset) \
            .execute()

        return response.data if response.data else []

    def search_by_filters(self, tenant_id: UUID, tipo: Optional[str] = None,
                          operacion: Optional[str] = None, colonia: Optional[str] = None,
                          min_precio: Optional[float] = None, max_precio: Optional[float] = None,
                          limit: int = 30) -> List[Dict]:
        """Búsqueda avanzada de propiedades"""
        query = self.client.table(self.table_name).select("*, imagenes_propiedades(url)") \
            .eq("tenant_id", str(tenant_id)) \
            .eq("activo", True) \
            .eq("estatus_publicacion", "activa")

        if tipo:
            query = query.eq("tipo", tipo)
        if operacion:
            query = query.eq("operacion", operacion)
        if colonia:
            query = query.ilike("colonia", f"%{colonia}%")
        if min_precio:
            query = query.gte("precio", min_precio)
        if max_precio:
            query = query.lte("precio", max_precio)

        response = query.limit(limit).execute()
        return response.data if response.data else []


class LeadRepository(BaseRepository):
    """Repository específico para la tabla leads"""

    def __init__(self, client: Client):
        super().__init__(client, "leads")

    def get_by_status(self, tenant_id: UUID, status: str, limit: int = 50) -> List[Dict]:
        """Obtiene leads por estatus"""
        response = self.client.table(self.table_name).select("*, propiedades(titulo), agentes(nombre)") \
            .eq("tenant_id", str(tenant_id)) \
            .eq("status", status) \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()

        return response.data if response.data else []

    def get_by_agente(self, tenant_id: UUID, agente_id: str, limit: int = 50) -> List[Dict]:
        """Obtiene leads asignados a un agente"""
        response = self.client.table(self.table_name).select("*, propiedades(titulo)") \
            .eq("tenant_id", str(tenant_id)) \
            .eq("asignado_a", agente_id) \
            .order("updated_at", desc=True) \
            .limit(limit) \
            .execute()

        return response.data if response.data else []

    def find_with_details(self, id: str, tenant_id: UUID) -> Optional[Dict]:
        """Obtiene lead completo con interacciones"""
        response = self.client.table(self.table_name) \
            .select("*, propiedades(titulo, precio), agentes(nombre), interacciones(*)") \
            .eq("tenant_id", str(tenant_id)) \
            .eq("id", id) \
            .single() \
            .execute()

        return response.data if response.data else None


class InteraccionRepository(BaseRepository):
    """Repository específico para la tabla interacciones"""

    def __init__(self, client: Client):
        # Note: interacciones no tiene tenant_id directamente, se filtra por lead_id
        super().__init__(client, "interacciones")

    def get_by_lead(self, lead_id: str, limit: int = 100) -> List[Dict]:
        """Obtiene todas las interacciones de un lead"""
        response = self.client.table(self.table_name).select("*, agentes(nombre)") \
            .eq("lead_id", lead_id) \
            .order("fecha", desc=True) \
            .limit(limit) \
            .execute()

        return response.data if response.data else []

    def create_for_lead(self, lead_id: str, data: Dict) -> Dict:
        """Crea una interacción para un lead (sin tenant_id requerido)"""
        data["lead_id"] = lead_id
        data["fecha"] = datetime.utcnow().isoformat()

        response = self.client.table(self.table_name).insert(data).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        raise Exception("Error al crear interacción")


class AgenteRepository(BaseRepository):
    """Repository específico para la tabla agentes"""

    def __init__(self, client: Client):
        super().__init__(client, "agentes")

    def find_by_email(self, email: str, tenant_id: UUID) -> Optional[Dict]:
        """Busca un agente por email"""
        response = self.client.table(self.table_name).select("*") \
            .eq("tenant_id", str(tenant_id)) \
            .eq("email", email) \
            .execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        return None

    def get_active(self, tenant_id: UUID) -> List[Dict]:
        """Obtiene solo agentes activos"""
        response = self.client.table(self.table_name).select("*") \
            .eq("tenant_id", str(tenant_id)) \
            .eq("activo", True) \
            .execute()

        return response.data if response.data else []
