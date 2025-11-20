-- =====================================================
-- Script de Migración - Habilitar Módulo IA con Permisos
-- Base de Datos: PostgreSQL (auth schema)
-- Versión: 1.0.0
-- Fecha: 20 de noviembre de 2025
-- Descripción: Asegura que el módulo IA esté registrado y
--              configura permisos por base de datos
-- =====================================================
-- =====================================================
-- 1. VERIFICAR Y REGISTRAR MÓDULO IA
-- =====================================================
-- Asegurar que el módulo IA existe en el catálogo
INSERT INTO auth.modulos_sistema (
        codigo,
        nombre,
        descripcion,
        icono,
        orden_menu,
        url_base,
        requiere_licencia,
        activo
    )
VALUES (
        'ia',
        'Asistente IA',
        'Análisis inteligente de balances contables con IA usando Gemini. Genera análisis profesionales, detecta anomalías y proporciona recomendaciones.',
        'brain',
        8,
        '/ia',
        TRUE,
        TRUE
    ) ON CONFLICT (codigo) DO
UPDATE
SET nombre = EXCLUDED.nombre,
    descripcion = EXCLUDED.descripcion,
    icono = EXCLUDED.icono,
    orden_menu = EXCLUDED.orden_menu,
    url_base = EXCLUDED.url_base,
    requiere_licencia = EXCLUDED.requiere_licencia,
    activo = EXCLUDED.activo;
-- =====================================================
-- 2. HABILITAR MÓDULO IA PARA BASES DE DATOS EXISTENTES
-- =====================================================
-- Obtener el ID del módulo IA
DO $$
DECLARE v_modulo_ia_id INTEGER;
v_mensaje TEXT;
BEGIN -- Obtener ID del módulo IA
SELECT id INTO v_modulo_ia_id
FROM auth.modulos_sistema
WHERE codigo = 'ia';
IF v_modulo_ia_id IS NULL THEN RAISE EXCEPTION 'No se encontró el módulo IA en el catálogo';
END IF;
-- Mostrar información
RAISE NOTICE '=================================================';
RAISE NOTICE 'Configurando permisos del Módulo IA';
RAISE NOTICE 'ID del módulo: %',
v_modulo_ia_id;
RAISE NOTICE '=================================================';
END $$;
-- =====================================================
-- 3. HABILITAR PARA BASES DE DATOS ENTERPRISE/ACTIVAS
-- =====================================================
-- Habilitar IA para base de datos 'stratex' (cliente enterprise)
INSERT INTO auth.modulos_habilitados_bd (
        id_base_datos,
        id_modulo,
        habilitado,
        usuario_habilitacion,
        notas
    )
SELECT bd.id,
    m.id,
    TRUE,
    'admin',
    'Módulo IA habilitado automáticamente - Plan Enterprise'
FROM auth.bases_datos_mysql bd
    CROSS JOIN auth.modulos_sistema m
WHERE bd.nombre_base_datos = 'stratex'
    AND m.codigo = 'ia'
    AND bd.activo = TRUE ON CONFLICT (id_base_datos, id_modulo) DO
UPDATE
SET habilitado = TRUE,
    notas = 'Módulo IA habilitado - Plan Enterprise';
-- Habilitar IA para base de datos 'evolve' (base principal)
INSERT INTO auth.modulos_habilitados_bd (
        id_base_datos,
        id_modulo,
        habilitado,
        usuario_habilitacion,
        notas
    )
SELECT bd.id,
    m.id,
    TRUE,
    'admin',
    'Módulo IA habilitado automáticamente - Base Principal'
FROM auth.bases_datos_mysql bd
    CROSS JOIN auth.modulos_sistema m
WHERE bd.nombre_base_datos = 'evolve'
    AND m.codigo = 'ia'
    AND bd.activo = TRUE ON CONFLICT (id_base_datos, id_modulo) DO
UPDATE
SET habilitado = TRUE,
    notas = 'Módulo IA habilitado - Base Principal';
-- =====================================================
-- 4. SCRIPT OPCIONAL: HABILITAR PARA TODAS LAS BDs ACTIVAS
-- =====================================================
-- Descomentar las siguientes líneas si deseas habilitar IA
-- para TODAS las bases de datos activas:
/*
 INSERT INTO auth.modulos_habilitados_bd (
 id_base_datos,
 id_modulo,
 habilitado,
 usuario_habilitacion,
 notas
 )
 SELECT
 bd.id,
 m.id,
 TRUE,
 'admin',
 'Módulo IA habilitado masivamente'
 FROM auth.bases_datos_mysql bd
 CROSS JOIN auth.modulos_sistema m
 WHERE m.codigo = 'ia'
 AND bd.activo = TRUE
 AND bd.estado IN ('activo', 'prueba')
 ON CONFLICT (id_base_datos, id_modulo)
 DO UPDATE SET
 habilitado = TRUE;
 */
-- =====================================================
-- 5. VERIFICACIÓN DE RESULTADOS
-- =====================================================
-- Mostrar resumen de bases de datos con módulo IA habilitado
DO $$
DECLARE v_total_bds INTEGER;
v_bds_con_ia INTEGER;
rec RECORD;
BEGIN -- Contar totales
SELECT COUNT(*) INTO v_total_bds
FROM auth.bases_datos_mysql
WHERE activo = TRUE;
SELECT COUNT(DISTINCT mh.id_base_datos) INTO v_bds_con_ia
FROM auth.modulos_habilitados_bd mh
    INNER JOIN auth.modulos_sistema m ON mh.id_modulo = m.id
    INNER JOIN auth.bases_datos_mysql bd ON mh.id_base_datos = bd.id
WHERE m.codigo = 'ia'
    AND mh.habilitado = TRUE
    AND bd.activo = TRUE;
-- Mostrar resumen
RAISE NOTICE '';
RAISE NOTICE '=================================================';
RAISE NOTICE 'RESUMEN DE CONFIGURACIÓN';
RAISE NOTICE '=================================================';
RAISE NOTICE 'Total de bases de datos activas: %',
v_total_bds;
RAISE NOTICE 'Bases de datos con módulo IA habilitado: %',
v_bds_con_ia;
RAISE NOTICE '';
RAISE NOTICE 'Detalle de bases de datos con módulo IA:';
RAISE NOTICE '-------------------------------------------------';
-- Mostrar detalle
FOR rec IN (
    SELECT bd.nombre_base_datos,
        bd.nombre_cliente,
        bd.plan,
        bd.estado,
        mh.fecha_habilitacion::DATE as fecha_habilitacion
    FROM auth.modulos_habilitados_bd mh
        INNER JOIN auth.bases_datos_mysql bd ON mh.id_base_datos = bd.id
        INNER JOIN auth.modulos_sistema m ON mh.id_modulo = m.id
    WHERE m.codigo = 'ia'
        AND mh.habilitado = TRUE
        AND bd.activo = TRUE
    ORDER BY bd.nombre_base_datos
) LOOP RAISE NOTICE '  - % (%) - Plan: % | Estado: % | Habilitado: %',
rec.nombre_base_datos,
rec.nombre_cliente,
rec.plan,
rec.estado,
rec.fecha_habilitacion;
END LOOP;
RAISE NOTICE '=================================================';
RAISE NOTICE '';
END $$;
-- =====================================================
-- 6. CONSULTAS ÚTILES PARA GESTIÓN
-- =====================================================
-- Crear función para habilitar/deshabilitar módulo IA fácilmente
CREATE OR REPLACE FUNCTION auth.toggle_modulo_ia(
        p_nombre_bd VARCHAR(50),
        p_habilitar BOOLEAN DEFAULT TRUE
    ) RETURNS TEXT AS $$
DECLARE v_mensaje TEXT;
v_bd_id INTEGER;
v_modulo_id INTEGER;
BEGIN -- Obtener IDs
SELECT id INTO v_bd_id
FROM auth.bases_datos_mysql
WHERE nombre_base_datos = p_nombre_bd
    AND activo = TRUE;
SELECT id INTO v_modulo_id
FROM auth.modulos_sistema
WHERE codigo = 'ia';
-- Validar
IF v_bd_id IS NULL THEN RETURN 'ERROR: Base de datos no encontrada o inactiva';
END IF;
IF v_modulo_id IS NULL THEN RETURN 'ERROR: Módulo IA no encontrado';
END IF;
-- Actualizar o insertar
INSERT INTO auth.modulos_habilitados_bd (
        id_base_datos,
        id_modulo,
        habilitado,
        usuario_habilitacion
    )
VALUES (v_bd_id, v_modulo_id, p_habilitar, current_user) ON CONFLICT (id_base_datos, id_modulo) DO
UPDATE
SET habilitado = p_habilitar,
    fecha_habilitacion = CASE
        WHEN p_habilitar = TRUE THEN CURRENT_TIMESTAMP
        ELSE modulos_habilitados_bd.fecha_habilitacion
    END,
    fecha_deshabilitacion = CASE
        WHEN p_habilitar = FALSE THEN CURRENT_TIMESTAMP
        ELSE NULL
    END;
IF p_habilitar THEN v_mensaje := 'Módulo IA HABILITADO para ' || p_nombre_bd;
ELSE v_mensaje := 'Módulo IA DESHABILITADO para ' || p_nombre_bd;
END IF;
RETURN v_mensaje;
END;
$$ LANGUAGE plpgsql;
COMMENT ON FUNCTION auth.toggle_modulo_ia IS 'Habilita o deshabilita el módulo IA para una base de datos específica';
-- =====================================================
-- EJEMPLOS DE USO
-- =====================================================
/*
 -- Habilitar módulo IA para una base de datos específica:
 SELECT auth.toggle_modulo_ia('nombre_base_datos', TRUE);
 
 -- Deshabilitar módulo IA:
 SELECT auth.toggle_modulo_ia('nombre_base_datos', FALSE);
 
 -- Ver todas las BDs con acceso a IA:
 SELECT * FROM auth.vista_modulos_habilitados
 WHERE codigo_modulo = 'ia'
 AND habilitado = TRUE;
 
 -- Ver qué usuarios tienen acceso a IA:
 SELECT DISTINCT
 u.nombre_usuario,
 u.email,
 u.rol,
 u.base_datos_mysql,
 bd.nombre_cliente
 FROM auth.usuarios u
 INNER JOIN auth.bases_datos_mysql bd ON u.base_datos_mysql = bd.nombre_base_datos
 INNER JOIN auth.modulos_habilitados_bd mh ON bd.id = mh.id_base_datos
 INNER JOIN auth.modulos_sistema m ON mh.id_modulo = m.id
 WHERE m.codigo = 'ia'
 AND mh.habilitado = TRUE
 AND u.activo = TRUE
 ORDER BY u.nombre_usuario;
 */
-- =====================================================
-- MIGRACIÓN COMPLETADA
-- =====================================================
DO $$ BEGIN RAISE NOTICE '';
RAISE NOTICE '=================================================';
RAISE NOTICE 'Migración 008: Módulo IA completada exitosamente';
RAISE NOTICE '=================================================';
RAISE NOTICE '';
RAISE NOTICE 'Próximos pasos:';
RAISE NOTICE '1. Actualizar código Python para usar @requiere_modulo("ia")';
RAISE NOTICE '2. Actualizar templates para mostrar/ocultar módulo IA';
RAISE NOTICE '3. Probar acceso con diferentes usuarios/bases de datos';
RAISE NOTICE '';
RAISE NOTICE 'Comandos útiles:';
RAISE NOTICE '  - SELECT auth.toggle_modulo_ia(''mi_bd'', TRUE);';
RAISE NOTICE '  - SELECT * FROM auth.vista_modulos_habilitados WHERE codigo_modulo = ''ia'';';
RAISE NOTICE '=================================================';
END $$;
