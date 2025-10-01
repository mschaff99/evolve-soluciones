-- =====================================================
-- Script para Crear Base de Datos PostgreSQL
-- con Codificación UTF-8 (Windows Compatible)
-- =====================================================

-- Terminar conexiones existentes a la base de datos (si existe)
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'evolve_auth'
  AND pid <> pg_backend_pid();

-- Eliminar base de datos si existe (¡CUIDADO en producción!)
-- DROP DATABASE IF EXISTS evolve_auth;

-- Crear base de datos con codificación UTF-8
CREATE DATABASE evolve_auth
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'C'
    LC_CTYPE = 'C'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    TEMPLATE template0;

-- Comentario
COMMENT ON DATABASE evolve_auth
    IS 'Base de datos de autenticación - Evolve Soluciones';

-- Conectar a la base de datos
\c evolve_auth

-- Verificar codificación
SELECT pg_encoding_to_char(encoding) as encoding 
FROM pg_database 
WHERE datname = 'evolve_auth';

-- Mensaje de confirmación
\echo 'Base de datos evolve_auth creada exitosamente con UTF-8'
