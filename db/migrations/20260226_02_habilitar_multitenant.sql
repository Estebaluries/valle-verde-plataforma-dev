-- 1. Habilitar extensión para generar UUIDs seguros
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Crear la tabla Maestra de Tenants (Inmobiliarias)
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre TEXT NOT NULL,
    subdominio TEXT UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 3. Insertar a "Valle Verde" como el primer Tenant oficial
-- Le asignaremos un UUID estático específico para facilitarte la conexión en tu código
INSERT INTO tenants (id, nombre, subdominio) 
VALUES (
    '123e4567-e89b-12d3-a456-426614174000', 
    'Inmobiliaria Valle Verde', 
    'valle-verde'
) ON CONFLICT DO NOTHING;

-- 4. Añadir la columna tenant_id a las tablas existentes
ALTER TABLE propiedades ADD COLUMN tenant_id UUID;
ALTER TABLE leads ADD COLUMN tenant_id UUID;

-- 5. Asignar TODAS las propiedades y leads actuales a Valle Verde
UPDATE propiedades SET tenant_id = '123e4567-e89b-12d3-a456-426614174000' WHERE tenant_id IS NULL;
UPDATE leads SET tenant_id = '123e4567-e89b-12d3-a456-426614174000' WHERE tenant_id IS NULL;

-- 6. Hacer que la columna sea OBLIGATORIA de ahora en adelante
ALTER TABLE propiedades ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE leads ALTER COLUMN tenant_id SET NOT NULL;

-- 7. Crear las Relaciones (Llaves Foráneas)
ALTER TABLE propiedades 
    ADD CONSTRAINT fk_propiedades_tenant 
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

ALTER TABLE leads 
    ADD CONSTRAINT fk_leads_tenant 
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

-- ¡Éxito! Ahora tu base de datos es oficialmente Multi-Tenant.