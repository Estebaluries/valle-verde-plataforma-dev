-- Migración 01: Esquema Inicial Valle Verde (Single Tenant)
-- Fecha: 26 Feb 2026

CREATE TABLE propiedades (
    id SERIAL PRIMARY KEY,
    titulo TEXT NOT NULL,
    descripcion TEXT,
    precio NUMERIC NOT NULL,
    moneda TEXT DEFAULT 'MXN',
    operacion TEXT NOT NULL,
    tipo TEXT NOT NULL,
    colonia TEXT NOT NULL,
    habitaciones INTEGER DEFAULT 0,
    banos INTEGER DEFAULT 0,
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

CREATE TABLE imagenes (
    id SERIAL PRIMARY KEY,
    propiedad_id INTEGER REFERENCES propiedades(id),
    url TEXT NOT NULL
);

CREATE TABLE leads (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    email TEXT NOT NULL,
    telefono TEXT NOT NULL,
    notas TEXT,
    propiedad_interes_id INTEGER REFERENCES propiedades(id),
    origen TEXT DEFAULT 'web_vverde',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);