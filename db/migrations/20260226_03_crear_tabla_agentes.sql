-- MIGRACIÓN: CREACIÓN DE TABLA AGENTES
-- Fecha: 2026-02-26
-- Descripción: Tabla para gestionar el equipo de ventas del tenant.

CREATE TABLE IF NOT EXISTS agentes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    nombre TEXT NOT NULL,
    email TEXT NOT NULL,
    telefono TEXT,
    rol TEXT DEFAULT 'agente', -- 'admin', 'agente'
    foto_url TEXT,
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    
    -- Relación con Tenant
    CONSTRAINT fk_agentes_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    -- Email único por tenant (o global si prefieres)
    CONSTRAINT uq_agentes_email UNIQUE (email)
);

-- Habilitar RLS
ALTER TABLE agentes ENABLE ROW LEVEL SECURITY;

-- Política básica (Por ahora permisiva para desarrollo, ajustar en prod)
CREATE POLICY "Acceso total a agentes del mismo tenant" ON agentes
    USING (tenant_id = '123e4567-e89b-12d3-a456-426614174000'); -- ID hardcodeado de Valle Verde por ahora

-- Insertar un agente Admin por defecto
INSERT INTO agentes (tenant_id, nombre, email, rol, activo)
VALUES ('123e4567-e89b-12d3-a456-426614174000', 'Admin Valle Verde', 'admin@valleverde.com', 'admin', true)
ON CONFLICT DO NOTHING;