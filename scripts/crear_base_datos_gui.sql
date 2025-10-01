-- =====================================================
-- Script para Crear Base de Datos PostgreSQL (GUI)
-- con Codificación UTF-8 (Windows Compatible)
-- =====================================================
-- IMPORTANTE: Ejecutar este script en la base de datos 'postgres' (no en evolve_auth)
-- =====================================================

-- Terminar conexiones existentes a la base de datos (si existe)
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'evolve_auth'
  AND pid <> pg_backend_pid();

-- Eliminar base de datos si existe (DESCOMENTAR SOLO SI QUIERES BORRAR LA BD EXISTENTE)
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

-- Verificar que se creó correctamente
SELECT 
    datname as nombre_bd,
    pg_encoding_to_char(encoding) as codificacion,
    datcollate as collation,
    datctype as ctype
FROM pg_database 
WHERE datname = 'evolve_auth';

-- =====================================================
-- SIGUIENTE PASO:
-- 1. Conectar manualmente a la base de datos 'evolve_auth'
-- 2. Ejecutar el script: migraciones/001_crear_tablas_autenticacion_postgres.sql
-- =====================================================
