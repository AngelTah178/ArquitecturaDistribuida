-- =============================================================================
-- Universidad Politécnica de Quintana Roo - Proyecto Final Integrador
-- Arquitectura Distribuida y Sincronizada (PostgreSQL Neon)
-- Script de Inicialización de Seguridad, Roles, Usuarios y Esquema Normalizado (3FN)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. ADMINISTRACIÓN DE ROLES Y USUARIOS
-- -----------------------------------------------------------------------------

-- Crear Rol: postgres_developer (Login, Connect, Create, Usage, CRUD, Alter Default Privileges)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'postgres_developer') THEN
        CREATE ROLE postgres_developer WITH LOGIN PASSWORD 'devPassword2026!' CREATEDB;
    END IF;
END $$;

-- Crear Rol: postgres_user (Login, CRUD, Uso de vistas y funciones)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'postgres_user') THEN
        CREATE ROLE postgres_user WITH LOGIN PASSWORD 'usrPassword2026!';
    END IF;
END $$;

-- Crear Usuario dev1 asociado o heredero de postgres_developer
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'dev1') THEN
        CREATE ROLE dev1 WITH LOGIN PASSWORD 'dev1Secret2026!';
        GRANT postgres_developer TO dev1;
    END IF;
END $$;

-- Crear Usuario usr1 asociado o heredero de postgres_user
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'usr1') THEN
        CREATE ROLE usr1 WITH LOGIN PASSWORD 'usr1Secret2026!';
        GRANT postgres_user TO usr1;
    END IF;
END $$;

-- Otorgar privilegios a nivel de base de datos
GRANT CONNECT, CREATE ON DATABASE current_database() TO postgres_developer;
GRANT CONNECT ON DATABASE current_database() TO postgres_user;

-- Otorgar uso de schema public
GRANT USAGE, CREATE ON SCHEMA public TO postgres_developer;
GRANT USAGE ON SCHEMA public TO postgres_user;

-- -----------------------------------------------------------------------------
-- 2. MODELO DE DATOS: 5 TABLAS NORMALIZADAS (PK, FK, ÍNDICES)
-- -----------------------------------------------------------------------------

-- Tabla 1: clientes
CREATE TABLE IF NOT EXISTS clientes (
    cliente_id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    correo VARCHAR(150) NOT NULL UNIQUE,
    telefono VARCHAR(30),
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla 2: productos
CREATE TABLE IF NOT EXISTS productos (
    producto_id SERIAL PRIMARY KEY,
    sku VARCHAR(50) UNIQUE,
    nombre VARCHAR(150) NOT NULL,
    precio NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    stock INT NOT NULL DEFAULT 0,
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla 3: pedidos
CREATE TABLE IF NOT EXISTS pedidos (
    pedido_id SERIAL PRIMARY KEY,
    cliente_id INT NOT NULL,
    fecha TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    mongo_id VARCHAR(64) UNIQUE,
    cluster_origen VARCHAR(20) DEFAULT 'Cluster #1',
    estado VARCHAR(30) DEFAULT 'COMPLETADO',
    total NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    sincronizado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pedidos_cliente FOREIGN KEY (cliente_id) REFERENCES clientes(cliente_id) ON DELETE RESTRICT
);

-- Tabla 4: detalle_pedido
CREATE TABLE IF NOT EXISTS detalle_pedido (
    detalle_id SERIAL PRIMARY KEY,
    pedido_id INT NOT NULL,
    producto_id INT NOT NULL,
    cantidad INT NOT NULL CHECK (cantidad > 0),
    precio_unitario NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    subtotal NUMERIC(12, 2) GENERATED ALWAYS AS (cantidad * precio_unitario) STORED,
    CONSTRAINT fk_detalle_pedido FOREIGN KEY (pedido_id) REFERENCES pedidos(pedido_id) ON DELETE CASCADE,
    CONSTRAINT fk_detalle_producto FOREIGN KEY (producto_id) REFERENCES productos(producto_id) ON DELETE RESTRICT
);

-- Tabla 5: sync_logs (Trazabilidad y Auditoría de Sincronización ETL)
CREATE TABLE IF NOT EXISTS sync_logs (
    sync_id SERIAL PRIMARY KEY,
    fecha_ejecucion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    cluster_origen VARCHAR(30) NOT NULL,
    registros_extraidos INT DEFAULT 0,
    registros_cargados INT DEFAULT 0,
    estado VARCHAR(30) NOT NULL, -- 'SINCRONIZADO', 'EN_EJECUCION', 'ERROR'
    tiempo_ms INT DEFAULT 0,
    mensaje TEXT
);

-- -----------------------------------------------------------------------------
-- 3. ÍNDICES DE RENDIMIENTO E INTEGRIDAD
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_clientes_correo ON clientes(correo);
CREATE INDEX IF NOT EXISTS idx_pedidos_cliente_id ON pedidos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_fecha ON pedidos(fecha);
CREATE INDEX IF NOT EXISTS idx_pedidos_mongo_id ON pedidos(mongo_id);
CREATE INDEX IF NOT EXISTS idx_detalle_pedido_pedido ON detalle_pedido(pedido_id);
CREATE INDEX IF NOT EXISTS idx_detalle_pedido_producto ON detalle_pedido(producto_id);
CREATE INDEX IF NOT EXISTS idx_sync_logs_fecha ON sync_logs(fecha_ejecucion DESC);

-- -----------------------------------------------------------------------------
-- 4. VISTAS Y ASIGNACIÓN FINAL DE PERMISOS
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vista_resumen_sincronizacion AS
SELECT 
    COUNT(DISTINCT p.pedido_id) AS total_pedidos_sincronizados,
    COUNT(DISTINCT c.cliente_id) AS total_clientes,
    COALESCE(SUM(p.total), 0) AS monto_total_acumulado,
    MAX(p.sincronizado_en) AS ultima_sincronizacion
FROM pedidos p
LEFT JOIN clientes c ON p.cliente_id = c.cliente_id;

-- Privilegios CRUD para postgres_developer sobre todas las tablas y secuencias
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres_developer;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres_developer;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO postgres_developer;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO postgres_developer;

-- Privilegios CRUD y Vistas para postgres_user
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO postgres_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO postgres_user;
GRANT SELECT ON vista_resumen_sincronizacion TO postgres_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO postgres_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO postgres_user;

-- Insertar catálogo semilla de productos iniciales si no existen
INSERT INTO productos (sku, nombre, precio, stock)
VALUES 
    ('PROD-001', 'Sensor IoT de Temperatura', 450.00, 100),
    ('PROD-002', 'Microcontrolador ESP32 WiFi/BLE', 180.00, 250),
    ('PROD-003', 'Módulo Gateway LoRaWAN', 1250.00, 50),
    ('PROD-004', 'Actuador Relevador 4 Canales', 120.00, 300),
    ('PROD-005', 'Fuente de Poder 12V 5A', 320.00, 80)
ON CONFLICT (sku) DO NOTHING;
