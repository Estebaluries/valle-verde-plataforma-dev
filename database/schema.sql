-- ============================================================
-- INMOBILIARIA VALLE VERDE - SCHEMA SQL
-- Multi-tenant PostgreSQL con RLS (Row Level Security)
-- ============================================================
-- Ejecutar en Supabase: Dashboard → SQL Editor → New Query

-- 1. TABLA MAESTRO: TENANTS
-- ============================================================
CREATE TABLE IF NOT EXISTS tenants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre TEXT NOT NULL,
  subdominio TEXT UNIQUE NOT NULL,
  logo_url TEXT,
  colores_tema JSONB DEFAULT '{}',
  email_notificaciones TEXT,
  activo BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),

  CONSTRAINT chk_nombre_not_empty CHECK (char_length(nombre) > 0),
  CONSTRAINT chk_subdominio_valid CHECK (subdominio ~ '^[a-z0-9\-]+$')
);

CREATE UNIQUE INDEX idx_tenants_subdominio ON tenants(subdominio);
CREATE INDEX idx_tenants_activo ON tenants(activo);

-- Insertar Valle Verde
INSERT INTO tenants (id, nombre, subdominio, email_notificaciones, activo)
VALUES (
  '123e4567-e89b-12d3-a456-426614174000'::UUID,
  'Inmobiliaria Valle Verde',
  'valle-verde',
  'admin@valleverde.com',
  true
)
ON CONFLICT (subdominio) DO NOTHING;


-- 2. TABLA: PROPIEDADES (Catálogo)
-- ============================================================
CREATE TABLE IF NOT EXISTS propiedades (
  id SERIAL PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

  -- Información básica
  titulo TEXT NOT NULL,
  descripcion TEXT,
  precio NUMERIC(15, 2) NOT NULL CHECK (precio > 0),
  moneda VARCHAR(3) DEFAULT 'MXN',

  -- Características
  tipo VARCHAR(50) NOT NULL,
  operacion VARCHAR(50) NOT NULL,
  colonia VARCHAR(100) NOT NULL,
  fraccionamiento VARCHAR(100),
  calle VARCHAR(200),
  numero VARCHAR(20),

  -- Detalles físicos
  habitaciones INT DEFAULT 0 CHECK (habitaciones >= 0),
  baños INT DEFAULT 0 CHECK (baños >= 0),
  m2_construccion NUMERIC(8, 2) CHECK (m2_construccion > 0),
  m2_terreno NUMERIC(8, 2) CHECK (m2_terreno > 0),
  estacionamientos INT DEFAULT 1 CHECK (estacionamientos >= 0),

  -- Amenidades (JSON)
  amenidades JSONB DEFAULT '[]',

  -- Estado
  activo BOOLEAN DEFAULT true,
  estatus_publicacion VARCHAR(50) DEFAULT 'activa',
  estatus_credito VARCHAR(50),
  banco VARCHAR(100),
  propiedad_id_externo TEXT,

  -- Meta
  agente_asignado UUID REFERENCES agentes(id) ON DELETE SET NULL,
  fecha_publicacion TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),

  CONSTRAINT fk_propiedades_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id),
  CONSTRAINT chk_tipo CHECK (tipo IN ('casa', 'apartamento', 'comercial', 'lote', 'otro')),
  CONSTRAINT chk_operacion CHECK (operacion IN ('venta', 'renta', 'venta_renta'))
);

CREATE INDEX idx_propiedades_tenant ON propiedades(tenant_id);
CREATE INDEX idx_propiedades_activa ON propiedades(tenant_id, activo);
CREATE INDEX idx_propiedades_colonia ON propiedades(tenant_id, colonia);
CREATE INDEX idx_propiedades_tipo_op ON propiedades(tenant_id, tipo, operacion, activo);
CREATE INDEX idx_propiedades_published ON propiedades(tenant_id, estatus_publicacion);

-- RLS: Propiedades - Agentes ven solo su tenant
ALTER TABLE propiedades ENABLE ROW LEVEL SECURITY;

CREATE POLICY propiedades_tenant_access ON propiedades
  FOR SELECT USING (tenant_id = current_setting('app.tenant_id')::UUID);

CREATE POLICY propiedades_insert_tenant ON propiedades
  FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id')::UUID);

CREATE POLICY propiedades_update_tenant ON propiedades
  FOR UPDATE USING (tenant_id = current_setting('app.tenant_id')::UUID);

CREATE POLICY propiedades_delete_tenant ON propiedades
  FOR DELETE USING (tenant_id = current_setting('app.tenant_id')::UUID);


-- 3. TABLA: IMAGENES_PROPIEDADES
-- ============================================================
CREATE TABLE IF NOT EXISTS imagenes_propiedades (
  id SERIAL PRIMARY KEY,
  propiedad_id INTEGER NOT NULL REFERENCES propiedades(id) ON DELETE CASCADE,
  url TEXT NOT NULL,
  descripcion TEXT,
  orden INT DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),

  CONSTRAINT fk_imagenes_propiedad FOREIGN KEY (propiedad_id) REFERENCES propiedades(id)
);

CREATE INDEX idx_imagenes_propiedad ON imagenes_propiedades(propiedad_id, orden);


-- 4. TABLA: AGENTES (Equipo del tenant)
-- ============================================================
CREATE TABLE IF NOT EXISTS agentes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

  nombre VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  telefono VARCHAR(20),

  rol VARCHAR(50) DEFAULT 'agente',
  foto_url TEXT,

  activo BOOLEAN DEFAULT true,

  -- Stats desnormalizadas
  leads_activos INT DEFAULT 0 CHECK (leads_activos >= 0),
  leads_cerrados INT DEFAULT 0 CHECK (leads_cerrados >= 0),
  comisiones_pendientes NUMERIC(15, 2) DEFAULT 0,

  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),

  CONSTRAINT fk_agentes_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id),
  CONSTRAINT chk_rol CHECK (rol IN ('admin', 'coordinador', 'agente', 'gerente')),
  CONSTRAINT uq_agentes_email_per_tenant UNIQUE (tenant_id, email)
);

CREATE INDEX idx_agentes_tenant ON agentes(tenant_id);
CREATE INDEX idx_agentes_active ON agentes(tenant_id, activo);
CREATE INDEX idx_agentes_email ON agentes(email);

-- RLS: Agentes - Ven solo agentes de su tenant
ALTER TABLE agentes ENABLE ROW LEVEL SECURITY;

CREATE POLICY agentes_tenant_access ON agentes
  FOR SELECT USING (tenant_id = current_setting('app.tenant_id')::UUID);


-- 5. TABLA: LEADS (CRM)
-- ============================================================
CREATE TABLE IF NOT EXISTS leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

  -- Información del cliente
  nombre VARCHAR(255) NOT NULL,
  email TEXT,
  telefono VARCHAR(20) NOT NULL,

  -- Contexto
  propiedad_interes_id INTEGER REFERENCES propiedades(id) ON DELETE SET NULL,
  origen VARCHAR(50) DEFAULT 'web',
  notas TEXT,

  -- Asignación y estado
  asignado_a UUID REFERENCES agentes(id) ON DELETE SET NULL,
  status VARCHAR(50) DEFAULT 'nuevo',
  probabilidad INT DEFAULT 0 CHECK (probabilidad BETWEEN 0 AND 100),

  -- Seguimiento
  proxima_accion_fecha DATE,
  proxima_accion_descripcion TEXT,

  -- Resultado
  cerrado_fecha DATE,
  tipo_cierre VARCHAR(50),
  comision_porciento NUMERIC(5, 2),
  comision_monto NUMERIC(15, 2),

  -- Meta
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),

  CONSTRAINT fk_leads_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id),
  CONSTRAINT fk_leads_agente FOREIGN KEY (asignado_a) REFERENCES agentes(id),
  CONSTRAINT chk_status CHECK (status IN ('nuevo', 'contactado', 'citado', 'oferta', 'cerrado', 'perdido')),
  CONSTRAINT chk_origen CHECK (origen IN ('web', 'whatsapp', 'referencia', 'portal', 'instagram', 'otro'))
);

CREATE INDEX idx_leads_tenant ON leads(tenant_id);
CREATE INDEX idx_leads_status ON leads(tenant_id, status);
CREATE INDEX idx_leads_agente ON leads(asignado_a);
CREATE INDEX idx_leads_telefono ON leads(tenant_id, telefono);
CREATE INDEX idx_leads_email ON leads(tenant_id, email);
CREATE INDEX idx_leads_created ON leads(tenant_id, created_at DESC);

-- RLS: Leads - Agentes ven solo su tenant
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

CREATE POLICY leads_tenant_access ON leads
  FOR SELECT USING (tenant_id = current_setting('app.tenant_id')::UUID);

CREATE POLICY leads_insert_tenant ON leads
  FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id')::UUID);

CREATE POLICY leads_update_tenant ON leads
  FOR UPDATE USING (tenant_id = current_setting('app.tenant_id')::UUID);

CREATE POLICY leads_delete_tenant ON leads
  FOR DELETE USING (tenant_id = current_setting('app.tenant_id')::UUID);


-- 6. TABLA: INTERACCIONES (Timeline de leads)
-- ============================================================
CREATE TABLE IF NOT EXISTS interacciones (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

  tipo VARCHAR(50) NOT NULL,
  fecha TIMESTAMP WITH TIME ZONE DEFAULT now(),
  notas TEXT,
  resultado VARCHAR(50),

  -- Quién registró
  registrado_por UUID REFERENCES agentes(id) ON DELETE SET NULL,

  -- Seguimiento
  proximo_contacto_fecha DATE,

  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),

  CONSTRAINT fk_interacciones_lead FOREIGN KEY (lead_id) REFERENCES leads(id),
  CONSTRAINT chk_tipo CHECK (tipo IN ('llamada', 'visita', 'email', 'whatsapp', 'oferta', 'otro')),
  CONSTRAINT chk_resultado CHECK (resultado IS NULL OR resultado IN ('positivo', 'neutral', 'negativo', 'pendiente'))
);

CREATE INDEX idx_interacciones_lead ON interacciones(lead_id);
CREATE INDEX idx_interacciones_fecha ON interacciones(fecha DESC);
CREATE INDEX idx_interacciones_agente ON interacciones(registrado_por);

-- RLS: Interacciones - Acceso a través de lead
ALTER TABLE interacciones ENABLE ROW LEVEL SECURITY;

CREATE POLICY interacciones_tenant_access ON interacciones
  FOR SELECT USING (
    lead_id IN (
      SELECT id FROM leads
      WHERE tenant_id = current_setting('app.tenant_id')::UUID
    )
  );


-- 7. TABLA: CONFIGURACION_TENANT
-- ============================================================
CREATE TABLE IF NOT EXISTS configuracion_tenant (
  id SERIAL PRIMARY KEY,
  tenant_id UUID NOT NULL UNIQUE REFERENCES tenants(id) ON DELETE CASCADE,

  -- Notificaciones
  email_nuevos_leads BOOLEAN DEFAULT true,
  email_visitas BOOLEAN DEFAULT true,
  sms_alertas BOOLEAN DEFAULT false,

  -- Integraciones
  sendgrid_api_key TEXT,
  twilio_api_key TEXT,

  -- Branding
  logo_url TEXT,
  colores JSONB DEFAULT '{}',

  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),

  CONSTRAINT fk_config_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);


-- 8. FUNCIONES Y TRIGGERS (Opcional)
-- ============================================================

-- Trigger: Actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar a tablas principales
CREATE TRIGGER propiedades_updated_at BEFORE UPDATE ON propiedades
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER leads_updated_at BEFORE UPDATE ON leads
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER agentes_updated_at BEFORE UPDATE ON agentes
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER tenants_updated_at BEFORE UPDATE ON tenants
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER configuracion_tenant_updated_at BEFORE UPDATE ON configuracion_tenant
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- 9. PERMISOS (RLS) - Configurar app.tenant_id
-- ============================================================
-- En backend: SET app.tenant_id = '123e4567...' antes de queries
-- Supabase lo hace automáticamente con JWT
-- Ver: https://supabase.com/docs/guides/auth/row-level-security


-- 10. SEED DATA (Opcional - Para testing)
-- ============================================================
-- Insertar datos de prueba si es necesario
-- INSERT INTO propiedades (tenant_id, titulo, precio, tipo, operacion, colonia, ...)
-- VALUES ('123e4567...', 'Casa 3 hab', 280000, 'casa', 'venta', 'Col. Juárez', ...)
