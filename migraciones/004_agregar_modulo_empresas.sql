-- =====================================================
-- Script de Migración - Agregar Módulo de Empresas
-- Base de Datos: PostgreSQL (auth schema)
-- Versión: 1.1.0
-- Fecha: 14 de octubre de 2025
-- Descripción: Agrega el módulo de Gestión de Empresas
-- =====================================================
-- Agregar módulo de empresas
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
        'empresas',
        'Gestión de Empresas',
        'Administración de empresas y credenciales SII',
        'building',
        10,
        '/empresas',
        FALSE
    ) ON CONFLICT (codigo) DO
UPDATE
SET nombre = EXCLUDED.nombre,
    descripcion = EXCLUDED.descripcion,
    icono = EXCLUDED.icono,
    orden_menu = EXCLUDED.orden_menu,
    url_base = EXCLUDED.url_base,
    requiere_licencia = EXCLUDED.requiere_licencia;
-- Habilitar módulo para stratex
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
    AND m.codigo = 'empresas'
    AND m.activo = TRUE ON CONFLICT (id_base_datos, id_modulo) DO
UPDATE
SET habilitado = TRUE,
    fecha_habilitacion = CURRENT_TIMESTAMP,
    usuario_habilitacion = 'admin';
-- Habilitar módulo para evolve
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
    AND m.codigo = 'empresas'
    AND m.activo = TRUE ON CONFLICT (id_base_datos, id_modulo) DO
UPDATE
SET habilitado = TRUE,
    fecha_habilitacion = CURRENT_TIMESTAMP,
    usuario_habilitacion = 'admin';
-- Mensaje de confirmación
DO $$ BEGIN RAISE NOTICE '=================================================';
RAISE NOTICE 'Módulo de Empresas agregado exitosamente';
RAISE NOTICE '=================================================';
RAISE NOTICE 'Código: empresas';
RAISE NOTICE 'URL: /<base_datos>/empresas';
RAISE NOTICE 'Habilitado para: stratex, evolve';
RAISE NOTICE '=================================================';
END $$;
