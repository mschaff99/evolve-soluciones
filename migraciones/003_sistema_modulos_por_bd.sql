-- =====================================================
-- Script de Migración - Sistema de Módulos por Base de Datos
-- Base de Datos: PostgreSQL (auth schema)
-- Versión: 1.0.0
-- Fecha: 13 de octubre de 2025
-- Descripción: Implementa sistema de habilitación de módulos
--              por base de datos MySQL (multi-tenant)
-- =====================================================
-- =====================================================
-- 1. CATÁLOGO DE MÓDULOS DEL SISTEMA
-- =====================================================
CREATE TABLE IF NOT EXISTS auth.modulos_sistema (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    icono VARCHAR(50),
    orden_menu INTEGER DEFAULT 0,
    url_base VARCHAR(100),
    requiere_licencia BOOLEAN DEFAULT FALSE,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_codigo_formato CHECK (codigo ~ '^[a-z0-9_]+$')
);
-- Índices
CREATE INDEX IF NOT EXISTS idx_modulos_codigo ON auth.modulos_sistema(codigo);
CREATE INDEX IF NOT EXISTS idx_modulos_activo ON auth.modulos_sistema(activo);
CREATE INDEX IF NOT EXISTS idx_modulos_orden ON auth.modulos_sistema(orden_menu);
-- Comentarios
COMMENT ON TABLE auth.modulos_sistema IS 'Catálogo de todos los módulos/funcionalidades disponibles en el sistema';
COMMENT ON COLUMN auth.modulos_sistema.codigo IS 'Identificador único del módulo (ej: consulta_f29)';
COMMENT ON COLUMN auth.modulos_sistema.nombre IS 'Nombre descriptivo del módulo';
COMMENT ON COLUMN auth.modulos_sistema.icono IS 'Clase de icono (Bootstrap Icons, Font Awesome, etc.)';
COMMENT ON COLUMN auth.modulos_sistema.orden_menu IS 'Orden de aparición en menú (menor = primero)';
COMMENT ON COLUMN auth.modulos_sistema.url_base IS 'URL base del módulo relativa al tenant';
COMMENT ON COLUMN auth.modulos_sistema.requiere_licencia IS 'Si requiere licencia premium/pago';
-- =====================================================
-- 2. REGISTRO DE BASES DE DATOS MYSQL (TENANTS)
-- =====================================================
CREATE TABLE IF NOT EXISTS auth.bases_datos_mysql (
    id SERIAL PRIMARY KEY,
    nombre_base_datos VARCHAR(50) UNIQUE NOT NULL,
    nombre_cliente VARCHAR(200) NOT NULL,
    rut_cliente VARCHAR(20),
    estado VARCHAR(20) NOT NULL DEFAULT 'activo',
    fecha_contratacion DATE,
    fecha_vencimiento DATE,
    plan VARCHAR(50),
    notas TEXT,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP,
    CONSTRAINT chk_bd_estado CHECK (
        estado IN (
            'activo',
            'suspendido',
            'inactivo',
            'prueba',
            'demo'
        )
    ),
    CONSTRAINT chk_bd_nombre_formato CHECK (nombre_base_datos ~ '^[a-z0-9_]+$')
);
-- Índices
CREATE INDEX IF NOT EXISTS idx_bd_nombre ON auth.bases_datos_mysql(nombre_base_datos);
CREATE INDEX IF NOT EXISTS idx_bd_estado ON auth.bases_datos_mysql(estado);
CREATE INDEX IF NOT EXISTS idx_bd_activo ON auth.bases_datos_mysql(activo);
-- Comentarios
COMMENT ON TABLE auth.bases_datos_mysql IS 'Registro descriptivo de bases de datos MySQL (tenants/clientes). NO tiene FK desde usuarios porque MySQL está en servidor separado';
COMMENT ON COLUMN auth.bases_datos_mysql.nombre_base_datos IS 'Nombre exacto de la BD en MySQL';
COMMENT ON COLUMN auth.bases_datos_mysql.nombre_cliente IS 'Razón social o nombre del cliente';
COMMENT ON COLUMN auth.bases_datos_mysql.estado IS 'Estado de la cuenta del cliente';
COMMENT ON COLUMN auth.bases_datos_mysql.plan IS 'Plan contratado (básico, pro, enterprise, etc.)';
-- =====================================================
-- 3. HABILITACIÓN DE MÓDULOS POR BASE DE DATOS
-- =====================================================
CREATE TABLE IF NOT EXISTS auth.modulos_habilitados_bd (
    id SERIAL PRIMARY KEY,
    id_base_datos INTEGER NOT NULL,
    id_modulo INTEGER NOT NULL,
    habilitado BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_habilitacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_deshabilitacion TIMESTAMP,
    usuario_habilitacion VARCHAR(50),
    notas TEXT,
    -- Foreign Keys (solo a tablas dentro de PostgreSQL)
    CONSTRAINT fk_modulos_base_datos FOREIGN KEY (id_base_datos) REFERENCES auth.bases_datos_mysql(id) ON DELETE CASCADE,
    CONSTRAINT fk_modulos_catalogo FOREIGN KEY (id_modulo) REFERENCES auth.modulos_sistema(id) ON DELETE CASCADE,
    -- Constraint único: una BD no puede tener el mismo módulo habilitado dos veces
    CONSTRAINT uk_bd_modulo UNIQUE (id_base_datos, id_modulo)
);
-- Índices
CREATE INDEX IF NOT EXISTS idx_modulos_bd_base_datos ON auth.modulos_habilitados_bd(id_base_datos);
CREATE INDEX IF NOT EXISTS idx_modulos_bd_modulo ON auth.modulos_habilitados_bd(id_modulo);
CREATE INDEX IF NOT EXISTS idx_modulos_bd_habilitado ON auth.modulos_habilitados_bd(habilitado);
-- Comentarios
COMMENT ON TABLE auth.modulos_habilitados_bd IS 'Define qué módulos están habilitados para cada base de datos MySQL. Permite configuración por cliente/tenant';
COMMENT ON COLUMN auth.modulos_habilitados_bd.habilitado IS 'Si está habilitado actualmente (permite deshabilitar sin eliminar registro histórico)';
-- =====================================================
-- DATOS INICIALES - CATÁLOGO DE MÓDULOS
-- =====================================================
INSERT INTO auth.modulos_sistema (
        codigo,
        nombre,
        descripcion,
        icono,
        orden_menu,
        url_base,
        requiere_licencia
    )
VALUES (
        'inicio',
        'Inicio',
        'Dashboard principal del sistema',
        'house',
        1,
        '/',
        FALSE
    ),
    (
        'consulta_f29',
        'Consulta Integral F29',
        'Seguimiento de formularios tributarios mensuales F29',
        'file-text',
        2,
        '/consulta-integral-f29',
        TRUE
    ),
    (
        'consolidado',
        'Consolidado Empresas',
        'Vista consolidada mensual y anual de datos empresariales',
        'bar-chart',
        3,
        '/consolidado',
        TRUE
    ),
    (
        'tareas',
        'Gestión de Tareas',
        'Sistema de tareas por empresa con estados y prioridades',
        'check-square',
        4,
        '/tareas',
        TRUE
    ),
    (
        'observaciones',
        'Observaciones',
        'Registro y seguimiento de observaciones por período',
        'message-square',
        5,
        '/observaciones',
        FALSE
    ),
    (
        'proveedores',
        'Proveedores',
        'Gestión de proveedores e integraciones externas',
        'users',
        6,
        '/proveedores',
        TRUE
    ),
    (
        'email',
        'Notificaciones Email',
        'Envío de alertas y notificaciones por correo electrónico',
        'envelope',
        7,
        '/email',
        TRUE
    ),
    (
        'ia',
        'Asistente IA',
        'Análisis predictivo y asistente inteligente con IA',
        'cpu',
        8,
        '/ia',
        TRUE
    ),
    (
        'reportes',
        'Reportes Avanzados',
        'Generación de reportes personalizados y exportación',
        'file-earmark-pdf',
        9,
        '/reportes',
        TRUE
    ) ON CONFLICT (codigo) DO NOTHING;
-- =====================================================
-- DATOS INICIALES - REGISTRO DE BASES DE DATOS
-- =====================================================
-- Registrar las bases de datos MySQL existentes
INSERT INTO auth.bases_datos_mysql (
        nombre_base_datos,
        nombre_cliente,
        estado,
        plan,
        fecha_contratacion
    )
VALUES (
        'stratex',
        'Stratex Consulting',
        'activo',
        'enterprise',
        CURRENT_DATE
    ),
    (
        'evolve',
        'Evolve Soluciones (Base Principal)',
        'activo',
        'enterprise',
        CURRENT_DATE
    ) ON CONFLICT (nombre_base_datos) DO NOTHING;
-- =====================================================
-- DATOS INICIALES - HABILITAR MÓDULOS
-- =====================================================
-- Habilitar TODOS los módulos para stratex (cliente enterprise)
INSERT INTO auth.modulos_habilitados_bd (
        id_base_datos,
        id_modulo,
        habilitado,
        usuario_habilitacion
    )
SELECT bd.id,
    m.id,
    TRUE,
    'admin'
FROM auth.bases_datos_mysql bd
    CROSS JOIN auth.modulos_sistema m
WHERE bd.nombre_base_datos = 'stratex'
    AND m.activo = TRUE ON CONFLICT (id_base_datos, id_modulo) DO NOTHING;
-- Habilitar solo módulos básicos para evolve
INSERT INTO auth.modulos_habilitados_bd (
        id_base_datos,
        id_modulo,
        habilitado,
        usuario_habilitacion
    )
SELECT bd.id,
    m.id,
    TRUE,
    'admin'
FROM auth.bases_datos_mysql bd
    CROSS JOIN auth.modulos_sistema m
WHERE bd.nombre_base_datos = 'evolve'
    AND m.codigo IN ('inicio', 'consulta_f29', 'observaciones')
    AND m.activo = TRUE ON CONFLICT (id_base_datos, id_modulo) DO NOTHING;
-- =====================================================
-- VISTAS ÚTILES
-- =====================================================
-- Vista: Módulos habilitados por base de datos (para consultas rápidas)
CREATE OR REPLACE VIEW auth.vista_modulos_habilitados AS
SELECT bd.nombre_base_datos,
    bd.nombre_cliente,
    bd.estado as estado_bd,
    m.codigo as codigo_modulo,
    m.nombre as nombre_modulo,
    m.descripcion,
    m.icono,
    m.orden_menu,
    m.url_base,
    m.requiere_licencia,
    mh.habilitado,
    mh.fecha_habilitacion,
    mh.fecha_deshabilitacion
FROM auth.modulos_habilitados_bd mh
    INNER JOIN auth.bases_datos_mysql bd ON mh.id_base_datos = bd.id
    INNER JOIN auth.modulos_sistema m ON mh.id_modulo = m.id
WHERE bd.activo = TRUE
    AND m.activo = TRUE
ORDER BY bd.nombre_base_datos,
    m.orden_menu;
COMMENT ON VIEW auth.vista_modulos_habilitados IS 'Vista consolidada de módulos habilitados por base de datos';
-- =====================================================
-- FUNCIONES ÚTILES
-- =====================================================
-- Función: Verificar si un módulo está habilitado para una BD
CREATE OR REPLACE FUNCTION auth.modulo_habilitado(
        p_nombre_bd VARCHAR(50),
        p_codigo_modulo VARCHAR(50)
    ) RETURNS BOOLEAN AS $$
DECLARE v_habilitado BOOLEAN;
BEGIN
SELECT mh.habilitado INTO v_habilitado
FROM auth.modulos_habilitados_bd mh
    INNER JOIN auth.bases_datos_mysql bd ON mh.id_base_datos = bd.id
    INNER JOIN auth.modulos_sistema m ON mh.id_modulo = m.id
WHERE bd.nombre_base_datos = p_nombre_bd
    AND m.codigo = p_codigo_modulo
    AND bd.activo = TRUE
    AND m.activo = TRUE;
RETURN COALESCE(v_habilitado, FALSE);
END;
$$ LANGUAGE plpgsql;
COMMENT ON FUNCTION auth.modulo_habilitado IS 'Verifica si un módulo está habilitado para una base de datos específica';
-- =====================================================
-- MIGRACIÓN COMPLETA
-- =====================================================
-- Mensaje de confirmación
DO $$ BEGIN RAISE NOTICE '=================================================';
RAISE NOTICE 'Migración 003: Sistema de Módulos completada';
RAISE NOTICE '=================================================';
RAISE NOTICE 'Tablas creadas:';
RAISE NOTICE '  - auth.modulos_sistema';
RAISE NOTICE '  - auth.bases_datos_mysql';
RAISE NOTICE '  - auth.modulos_habilitados_bd';
RAISE NOTICE '';
RAISE NOTICE 'Módulos registrados: 9';
RAISE NOTICE 'Bases de datos registradas: 2 (stratex, evolve)';
RAISE NOTICE '';
RAISE NOTICE 'IMPORTANTE: NO se creó FK desde usuarios.base_datos_mysql';
RAISE NOTICE 'porque las BDs MySQL están en servidor separado.';
RAISE NOTICE 'La validación se hará en código Python.';
RAISE NOTICE '=================================================';
END $$;
