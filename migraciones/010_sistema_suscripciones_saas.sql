-- =====================================================
-- Script de Migración - Sistema de Suscripciones SaaS
-- Base de Datos: PostgreSQL (auth schema)
-- Versión: 1.0.0
-- Fecha: 11 de diciembre de 2024
-- Descripción: Implementa sistema completo de suscripciones,
--              planes y facturación para modelo SaaS
-- =====================================================

-- =====================================================
-- 1. TABLA DE PLANES DE SUSCRIPCIÓN
-- =====================================================
CREATE TABLE IF NOT EXISTS auth.planes_suscripcion (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    
    -- Precios
    precio_mensual DECIMAL(10, 2) NOT NULL DEFAULT 0,
    precio_anual DECIMAL(10, 2) NOT NULL DEFAULT 0,
    
    -- Límites del plan
    max_usuarios INTEGER,
    max_empresas INTEGER,
    max_transacciones_mes INTEGER,
    almacenamiento_gb INTEGER,
    
    -- Características
    incluye_soporte BOOLEAN DEFAULT FALSE,
    nivel_soporte VARCHAR(20) DEFAULT 'basico',
    periodo_prueba_dias INTEGER DEFAULT 0,
    
    -- UI/Presentación
    destacado BOOLEAN DEFAULT FALSE,
    activo BOOLEAN DEFAULT TRUE,
    
    -- Configuración adicional (JSON)
    configuracion_json JSONB,
    
    -- Auditoría
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP,
    
    CONSTRAINT chk_codigo_plan CHECK (codigo ~ '^[a-z0-9_]+$'),
    CONSTRAINT chk_nivel_soporte CHECK (nivel_soporte IN ('basico', 'premium', 'enterprise', '24x7')),
    CONSTRAINT chk_precios_positivos CHECK (precio_mensual >= 0 AND precio_anual >= 0)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_planes_codigo ON auth.planes_suscripcion(codigo);
CREATE INDEX IF NOT EXISTS idx_planes_activo ON auth.planes_suscripcion(activo);
CREATE INDEX IF NOT EXISTS idx_planes_precio ON auth.planes_suscripcion(precio_mensual);

-- Comentarios
COMMENT ON TABLE auth.planes_suscripcion IS 'Catálogo de planes de suscripción disponibles en el SaaS';
COMMENT ON COLUMN auth.planes_suscripcion.codigo IS 'Identificador único del plan (ej: basico, profesional, empresarial)';
COMMENT ON COLUMN auth.planes_suscripcion.precio_mensual IS 'Precio de suscripción mensual en CLP';
COMMENT ON COLUMN auth.planes_suscripcion.precio_anual IS 'Precio de suscripción anual en CLP (usualmente con descuento)';
COMMENT ON COLUMN auth.planes_suscripcion.max_usuarios IS 'Número máximo de usuarios permitidos (NULL = ilimitado)';
COMMENT ON COLUMN auth.planes_suscripcion.destacado IS 'Si es el plan recomendado/destacado en la UI';

-- =====================================================
-- 2. RELACIÓN MÓDULOS POR PLAN
-- =====================================================
CREATE TABLE IF NOT EXISTS auth.modulos_plan (
    id SERIAL PRIMARY KEY,
    id_plan INTEGER NOT NULL,
    id_modulo INTEGER NOT NULL,
    incluido BOOLEAN DEFAULT TRUE,
    
    -- Auditoría
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    CONSTRAINT fk_modulos_plan_plan FOREIGN KEY (id_plan) 
        REFERENCES auth.planes_suscripcion(id) ON DELETE CASCADE,
    CONSTRAINT fk_modulos_plan_modulo FOREIGN KEY (id_modulo) 
        REFERENCES auth.modulos_sistema(id) ON DELETE CASCADE,
    
    -- Constraint único
    CONSTRAINT uk_plan_modulo UNIQUE (id_plan, id_modulo)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_modulos_plan_plan ON auth.modulos_plan(id_plan);
CREATE INDEX IF NOT EXISTS idx_modulos_plan_modulo ON auth.modulos_plan(id_modulo);

-- Comentarios
COMMENT ON TABLE auth.modulos_plan IS 'Define qué módulos están incluidos en cada plan de suscripción';

-- =====================================================
-- 3. TABLA DE SUSCRIPCIONES
-- =====================================================
CREATE TABLE IF NOT EXISTS auth.suscripciones (
    id SERIAL PRIMARY KEY,
    id_base_datos INTEGER NOT NULL,
    id_plan INTEGER NOT NULL,
    
    -- Estado y configuración
    estado VARCHAR(30) NOT NULL DEFAULT 'activa',
    periodo VARCHAR(20) NOT NULL DEFAULT 'mensual',
    
    -- Fechas
    fecha_inicio TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_vencimiento TIMESTAMP,
    fecha_proximo_cobro TIMESTAMP,
    
    -- Configuración de pago
    auto_renovacion BOOLEAN DEFAULT TRUE,
    metodo_pago VARCHAR(50),
    precio_actual DECIMAL(10, 2) NOT NULL,
    moneda VARCHAR(3) DEFAULT 'CLP',
    
    -- Período de prueba
    en_periodo_prueba BOOLEAN DEFAULT FALSE,
    fecha_fin_prueba TIMESTAMP,
    
    -- Cancelación
    cancelada_en TIMESTAMP,
    motivo_cancelacion TEXT,
    
    -- Metadata adicional
    metadata_json JSONB,
    
    -- Auditoría
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP,
    
    -- Foreign Keys
    CONSTRAINT fk_suscripcion_base_datos FOREIGN KEY (id_base_datos) 
        REFERENCES auth.bases_datos_mysql(id) ON DELETE CASCADE,
    CONSTRAINT fk_suscripcion_plan FOREIGN KEY (id_plan) 
        REFERENCES auth.planes_suscripcion(id) ON DELETE RESTRICT,
    
    -- Constraints
    CONSTRAINT chk_suscripcion_estado CHECK (
        estado IN ('activa', 'periodo_prueba', 'suspendida', 'cancelada', 
                   'pendiente_pago', 'pendiente_cancelacion', 'vencida')
    ),
    CONSTRAINT chk_suscripcion_periodo CHECK (periodo IN ('mensual', 'anual')),
    CONSTRAINT chk_precio_positivo CHECK (precio_actual >= 0)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_suscripcion_base_datos ON auth.suscripciones(id_base_datos);
CREATE INDEX IF NOT EXISTS idx_suscripcion_plan ON auth.suscripciones(id_plan);
CREATE INDEX IF NOT EXISTS idx_suscripcion_estado ON auth.suscripciones(estado);
CREATE INDEX IF NOT EXISTS idx_suscripcion_vencimiento ON auth.suscripciones(fecha_vencimiento);
CREATE INDEX IF NOT EXISTS idx_suscripcion_proximo_cobro ON auth.suscripciones(fecha_proximo_cobro);

-- Comentarios
COMMENT ON TABLE auth.suscripciones IS 'Registro de suscripciones activas e históricas de cada tenant/cliente';
COMMENT ON COLUMN auth.suscripciones.estado IS 'Estado actual de la suscripción';
COMMENT ON COLUMN auth.suscripciones.periodo IS 'Período de facturación (mensual/anual)';
COMMENT ON COLUMN auth.suscripciones.auto_renovacion IS 'Si se renueva automáticamente al vencer';
COMMENT ON COLUMN auth.suscripciones.en_periodo_prueba IS 'Si está en período de prueba gratuito';

-- =====================================================
-- 4. TABLA DE TRANSACCIONES/PAGOS
-- =====================================================
CREATE TABLE IF NOT EXISTS auth.transacciones (
    id SERIAL PRIMARY KEY,
    id_suscripcion INTEGER NOT NULL,
    
    -- Información de la transacción
    tipo VARCHAR(30) NOT NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'pendiente',
    monto DECIMAL(10, 2) NOT NULL,
    moneda VARCHAR(3) DEFAULT 'CLP',
    
    -- Información del pago
    metodo_pago VARCHAR(50),
    pasarela_pago VARCHAR(50),
    id_externo_transaccion VARCHAR(200),
    id_externo_pago VARCHAR(200),
    
    -- Fechas
    fecha_transaccion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_procesada TIMESTAMP,
    fecha_completada TIMESTAMP,
    
    -- Detalles
    descripcion TEXT,
    metadata_json JSONB,
    
    -- Facturación
    numero_factura VARCHAR(50),
    url_factura TEXT,
    
    -- Auditoría
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    CONSTRAINT fk_transaccion_suscripcion FOREIGN KEY (id_suscripcion) 
        REFERENCES auth.suscripciones(id) ON DELETE CASCADE,
    
    -- Constraints
    CONSTRAINT chk_transaccion_tipo CHECK (
        tipo IN ('pago_mensual', 'pago_anual', 'upgrade', 'downgrade', 
                 'reembolso', 'ajuste', 'periodo_prueba')
    ),
    CONSTRAINT chk_transaccion_estado CHECK (
        estado IN ('pendiente', 'procesando', 'completada', 'fallida', 
                   'cancelada', 'reembolsada')
    ),
    CONSTRAINT chk_monto_positivo CHECK (monto >= 0)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_transaccion_suscripcion ON auth.transacciones(id_suscripcion);
CREATE INDEX IF NOT EXISTS idx_transaccion_estado ON auth.transacciones(estado);
CREATE INDEX IF NOT EXISTS idx_transaccion_tipo ON auth.transacciones(tipo);
CREATE INDEX IF NOT EXISTS idx_transaccion_fecha ON auth.transacciones(fecha_transaccion);
CREATE INDEX IF NOT EXISTS idx_transaccion_id_externo ON auth.transacciones(id_externo_transaccion);

-- Comentarios
COMMENT ON TABLE auth.transacciones IS 'Registro de todas las transacciones y pagos realizados';
COMMENT ON COLUMN auth.transacciones.tipo IS 'Tipo de transacción (pago, upgrade, reembolso, etc.)';
COMMENT ON COLUMN auth.transacciones.id_externo_transaccion IS 'ID de transacción en la pasarela de pago';

-- =====================================================
-- 5. TABLA DE MÉTODOS DE PAGO
-- =====================================================
CREATE TABLE IF NOT EXISTS auth.metodos_pago (
    id SERIAL PRIMARY KEY,
    id_base_datos INTEGER NOT NULL,
    
    -- Información del método
    tipo VARCHAR(30) NOT NULL,
    proveedor VARCHAR(50),
    
    -- Información de tarjeta (parcial/tokenizada)
    ultimos_4_digitos VARCHAR(4),
    marca_tarjeta VARCHAR(30),
    mes_expiracion INTEGER,
    anio_expiracion INTEGER,
    
    -- Token/ID externo (de Stripe, MercadoPago, etc.)
    token_pago VARCHAR(200),
    id_cliente_externo VARCHAR(200),
    
    -- Estado
    predeterminado BOOLEAN DEFAULT FALSE,
    activo BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    metadata_json JSONB,
    
    -- Auditoría
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP,
    
    -- Foreign Keys
    CONSTRAINT fk_metodo_pago_base_datos FOREIGN KEY (id_base_datos) 
        REFERENCES auth.bases_datos_mysql(id) ON DELETE CASCADE,
    
    -- Constraints
    CONSTRAINT chk_metodo_tipo CHECK (
        tipo IN ('tarjeta_credito', 'tarjeta_debito', 'transferencia', 
                 'webpay', 'mercadopago', 'stripe')
    )
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_metodo_pago_base_datos ON auth.metodos_pago(id_base_datos);
CREATE INDEX IF NOT EXISTS idx_metodo_pago_predeterminado ON auth.metodos_pago(predeterminado);
CREATE INDEX IF NOT EXISTS idx_metodo_pago_activo ON auth.metodos_pago(activo);

-- Comentarios
COMMENT ON TABLE auth.metodos_pago IS 'Métodos de pago registrados por cada cliente/tenant';
COMMENT ON COLUMN auth.metodos_pago.token_pago IS 'Token seguro proporcionado por la pasarela de pago';

-- =====================================================
-- DATOS INICIALES - PLANES DE SUSCRIPCIÓN
-- =====================================================

-- Plan Gratuito
INSERT INTO auth.planes_suscripcion 
(codigo, nombre, descripcion, precio_mensual, precio_anual, 
 max_usuarios, max_empresas, max_transacciones_mes, almacenamiento_gb,
 incluye_soporte, nivel_soporte, periodo_prueba_dias, destacado)
VALUES 
('gratuito', 'Plan Gratuito', 
 'Ideal para probar el sistema y pequeños emprendimientos', 
 0, 0, 1, 5, 100, 1, 
 FALSE, 'basico', 0, FALSE)
ON CONFLICT (codigo) DO NOTHING;

-- Plan Básico
INSERT INTO auth.planes_suscripcion 
(codigo, nombre, descripcion, precio_mensual, precio_anual, 
 max_usuarios, max_empresas, max_transacciones_mes, almacenamiento_gb,
 incluye_soporte, nivel_soporte, periodo_prueba_dias, destacado)
VALUES 
('basico', 'Plan Básico', 
 'Perfecto para consultorías pequeñas y contadores independientes', 
 29990, 299900, 3, 15, 500, 5, 
 TRUE, 'basico', 14, FALSE)
ON CONFLICT (codigo) DO NOTHING;

-- Plan Profesional (Destacado)
INSERT INTO auth.planes_suscripcion 
(codigo, nombre, descripcion, precio_mensual, precio_anual, 
 max_usuarios, max_empresas, max_transacciones_mes, almacenamiento_gb,
 incluye_soporte, nivel_soporte, periodo_prueba_dias, destacado)
VALUES 
('profesional', 'Plan Profesional', 
 'Para consultorías en crecimiento con múltiples clientes', 
 59990, 599900, 10, 50, 2000, 20, 
 TRUE, 'premium', 14, TRUE)
ON CONFLICT (codigo) DO NOTHING;

-- Plan Empresarial
INSERT INTO auth.planes_suscripcion 
(codigo, nombre, descripcion, precio_mensual, precio_anual, 
 max_usuarios, max_empresas, max_transacciones_mes, almacenamiento_gb,
 incluye_soporte, nivel_soporte, periodo_prueba_dias, destacado)
VALUES 
('empresarial', 'Plan Empresarial', 
 'Solución completa para grandes consultorías y estudios contables', 
 119990, 1199900, NULL, NULL, NULL, 100, 
 TRUE, 'enterprise', 14, FALSE)
ON CONFLICT (codigo) DO NOTHING;

-- =====================================================
-- ASIGNAR MÓDULOS A PLANES
-- =====================================================

-- Plan Gratuito - Solo módulos básicos
INSERT INTO auth.modulos_plan (id_plan, id_modulo, incluido)
SELECT p.id, m.id, TRUE
FROM auth.planes_suscripcion p
CROSS JOIN auth.modulos_sistema m
WHERE p.codigo = 'gratuito'
  AND m.codigo IN ('inicio', 'consulta_f29')
ON CONFLICT (id_plan, id_modulo) DO NOTHING;

-- Plan Básico - Módulos esenciales
INSERT INTO auth.modulos_plan (id_plan, id_modulo, incluido)
SELECT p.id, m.id, TRUE
FROM auth.planes_suscripcion p
CROSS JOIN auth.modulos_sistema m
WHERE p.codigo = 'basico'
  AND m.codigo IN ('inicio', 'consulta_f29', 'consolidado', 'tareas', 'observaciones')
ON CONFLICT (id_plan, id_modulo) DO NOTHING;

-- Plan Profesional - Todos excepto IA
INSERT INTO auth.modulos_plan (id_plan, id_modulo, incluido)
SELECT p.id, m.id, TRUE
FROM auth.planes_suscripcion p
CROSS JOIN auth.modulos_sistema m
WHERE p.codigo = 'profesional'
  AND m.codigo IN ('inicio', 'consulta_f29', 'consolidado', 'tareas', 
                   'observaciones', 'proveedores', 'email', 'reportes')
ON CONFLICT (id_plan, id_modulo) DO NOTHING;

-- Plan Empresarial - Todos los módulos
INSERT INTO auth.modulos_plan (id_plan, id_modulo, incluido)
SELECT p.id, m.id, TRUE
FROM auth.planes_suscripcion p
CROSS JOIN auth.modulos_sistema m
WHERE p.codigo = 'empresarial'
  AND m.activo = TRUE
ON CONFLICT (id_plan, id_modulo) DO NOTHING;

-- =====================================================
-- VISTAS ÚTILES
-- =====================================================

-- Vista: Resumen de planes con conteo de módulos
CREATE OR REPLACE VIEW auth.vista_planes_resumen AS
SELECT 
    p.id,
    p.codigo,
    p.nombre,
    p.descripcion,
    p.precio_mensual,
    p.precio_anual,
    p.max_usuarios,
    p.max_empresas,
    p.destacado,
    p.activo,
    COUNT(mp.id) as total_modulos,
    CASE 
        WHEN p.precio_mensual = 0 THEN 0
        ELSE ROUND((p.precio_mensual * 12 - p.precio_anual) / (p.precio_mensual * 12) * 100, 1)
    END as porcentaje_ahorro_anual
FROM auth.planes_suscripcion p
LEFT JOIN auth.modulos_plan mp ON p.id = mp.id_plan AND mp.incluido = TRUE
WHERE p.activo = TRUE
GROUP BY p.id
ORDER BY p.precio_mensual ASC;

COMMENT ON VIEW auth.vista_planes_resumen IS 'Vista resumen de planes con métricas calculadas';

-- Vista: Suscripciones activas con información del cliente
CREATE OR REPLACE VIEW auth.vista_suscripciones_activas AS
SELECT 
    s.id as id_suscripcion,
    bd.nombre_base_datos,
    bd.nombre_cliente,
    p.codigo as codigo_plan,
    p.nombre as nombre_plan,
    s.estado,
    s.periodo,
    s.precio_actual,
    s.fecha_inicio,
    s.fecha_vencimiento,
    s.auto_renovacion,
    s.en_periodo_prueba,
    CASE 
        WHEN s.fecha_vencimiento IS NULL THEN NULL
        ELSE EXTRACT(DAY FROM (s.fecha_vencimiento - CURRENT_TIMESTAMP))
    END as dias_hasta_vencimiento
FROM auth.suscripciones s
INNER JOIN auth.bases_datos_mysql bd ON s.id_base_datos = bd.id
INNER JOIN auth.planes_suscripcion p ON s.id_plan = p.id
WHERE s.estado IN ('activa', 'periodo_prueba')
  AND bd.activo = TRUE
ORDER BY s.fecha_vencimiento ASC;

COMMENT ON VIEW auth.vista_suscripciones_activas IS 'Vista de suscripciones activas con métricas de negocio';

-- =====================================================
-- FUNCIONES ÚTILES
-- =====================================================

-- Función: Obtener MRR (Monthly Recurring Revenue)
CREATE OR REPLACE FUNCTION auth.calcular_mrr()
RETURNS DECIMAL(10, 2) AS $$
DECLARE
    v_mrr DECIMAL(10, 2);
BEGIN
    SELECT COALESCE(SUM(
        CASE 
            WHEN s.periodo = 'mensual' THEN s.precio_actual
            WHEN s.periodo = 'anual' THEN s.precio_actual / 12
            ELSE 0
        END
    ), 0) INTO v_mrr
    FROM auth.suscripciones s
    WHERE s.estado IN ('activa', 'periodo_prueba')
      AND s.en_periodo_prueba = FALSE;
    
    RETURN v_mrr;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION auth.calcular_mrr IS 'Calcula el MRR (Monthly Recurring Revenue) total';

-- Función: Verificar si tenant tiene acceso a módulo según su plan
CREATE OR REPLACE FUNCTION auth.tenant_tiene_acceso_modulo(
    p_nombre_bd VARCHAR(50),
    p_codigo_modulo VARCHAR(50)
) RETURNS BOOLEAN AS $$
DECLARE
    v_tiene_acceso BOOLEAN;
BEGIN
    SELECT EXISTS(
        SELECT 1
        FROM auth.suscripciones s
        INNER JOIN auth.bases_datos_mysql bd ON s.id_base_datos = bd.id
        INNER JOIN auth.modulos_plan mp ON s.id_plan = mp.id_plan
        INNER JOIN auth.modulos_sistema m ON mp.id_modulo = m.id
        WHERE bd.nombre_base_datos = p_nombre_bd
          AND m.codigo = p_codigo_modulo
          AND s.estado IN ('activa', 'periodo_prueba')
          AND mp.incluido = TRUE
          AND m.activo = TRUE
    ) INTO v_tiene_acceso;
    
    RETURN COALESCE(v_tiene_acceso, FALSE);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION auth.tenant_tiene_acceso_modulo IS 'Verifica si un tenant tiene acceso a un módulo según su plan de suscripción';

-- =====================================================
-- MIGRACIÓN DE CLIENTES EXISTENTES
-- =====================================================

-- Asignar Plan Empresarial a clientes existentes (stratex y evolve)
INSERT INTO auth.suscripciones 
(id_base_datos, id_plan, estado, periodo, fecha_inicio, 
 fecha_vencimiento, auto_renovacion, precio_actual, en_periodo_prueba)
SELECT 
    bd.id,
    p.id,
    'activa',
    'anual',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP + INTERVAL '1 year',
    TRUE,
    p.precio_anual,
    FALSE
FROM auth.bases_datos_mysql bd
CROSS JOIN auth.planes_suscripcion p
WHERE bd.nombre_base_datos IN ('stratex', 'evolve')
  AND p.codigo = 'empresarial'
  AND NOT EXISTS (
      SELECT 1 FROM auth.suscripciones s 
      WHERE s.id_base_datos = bd.id
  )
ON CONFLICT DO NOTHING;

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Trigger: Actualizar fecha_modificacion en planes
CREATE OR REPLACE FUNCTION auth.actualizar_fecha_modificacion_plan()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_modificacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_planes_fecha_modificacion
    BEFORE UPDATE ON auth.planes_suscripcion
    FOR EACH ROW
    EXECUTE FUNCTION auth.actualizar_fecha_modificacion_plan();

-- Trigger: Actualizar fecha_modificacion en suscripciones
CREATE TRIGGER trg_suscripciones_fecha_modificacion
    BEFORE UPDATE ON auth.suscripciones
    FOR EACH ROW
    EXECUTE FUNCTION auth.actualizar_fecha_modificacion_plan();

-- =====================================================
-- MIGRACIÓN COMPLETA
-- =====================================================

DO $$ 
BEGIN
    RAISE NOTICE '=================================================';
    RAISE NOTICE 'Migración 010: Sistema de Suscripciones SaaS completada';
    RAISE NOTICE '=================================================';
    RAISE NOTICE 'Tablas creadas:';
    RAISE NOTICE '  - auth.planes_suscripcion';
    RAISE NOTICE '  - auth.modulos_plan';
    RAISE NOTICE '  - auth.suscripciones';
    RAISE NOTICE '  - auth.transacciones';
    RAISE NOTICE '  - auth.metodos_pago';
    RAISE NOTICE '';
    RAISE NOTICE 'Planes creados: 4 (Gratuito, Básico, Profesional, Empresarial)';
    RAISE NOTICE 'Clientes migrados: stratex y evolve asignados a Plan Empresarial';
    RAISE NOTICE '';
    RAISE NOTICE 'MRR actual: ' || auth.calcular_mrr()::TEXT || ' CLP';
    RAISE NOTICE '=================================================';
END $$;
