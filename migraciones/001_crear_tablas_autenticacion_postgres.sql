-- =====================================================
-- Script de Migración - Sistema de Autenticación
-- Base de Datos: PostgreSQL
-- Versión: 1.0.0
-- Descripción: Crea las tablas necesarias para el 
--              sistema de autenticación de usuarios
-- =====================================================

-- Crear esquema si no existe
CREATE SCHEMA IF NOT EXISTS auth;

-- =====================================================
-- TABLA: usuarios
-- Descripción: Almacena la información de los usuarios
--              del sistema
-- =====================================================

CREATE TABLE IF NOT EXISTS auth.usuarios (
    id SERIAL PRIMARY KEY,
    nombre_usuario VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hash_contraseña VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL DEFAULT 'usuario',
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_ultimo_acceso TIMESTAMP,
    
    -- Constraints (rol flexible para permitir roles personalizados)
    CONSTRAINT chk_nombre_usuario_length CHECK (LENGTH(nombre_usuario) >= 3),
    CONSTRAINT chk_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Índices para usuarios
CREATE INDEX idx_usuarios_nombre_usuario ON auth.usuarios(nombre_usuario);
CREATE INDEX idx_usuarios_email ON auth.usuarios(email);
CREATE INDEX idx_usuarios_activo ON auth.usuarios(activo);

-- =====================================================
-- TABLA: sesiones_usuario
-- Descripción: Almacena las sesiones activas de los
--              usuarios para control de acceso
-- =====================================================

CREATE TABLE IF NOT EXISTS auth.sesiones_usuario (
    id SERIAL PRIMARY KEY,
    token_sesion VARCHAR(255) UNIQUE NOT NULL,
    id_usuario INTEGER NOT NULL,
    direccion_ip VARCHAR(45),
    user_agent TEXT,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_ultima_actividad TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Foreign Keys
    CONSTRAINT fk_sesion_usuario FOREIGN KEY (id_usuario) 
        REFERENCES auth.usuarios(id) ON DELETE CASCADE
);

-- Índices para sesiones
CREATE INDEX idx_sesiones_token ON auth.sesiones_usuario(token_sesion);
CREATE INDEX idx_sesiones_usuario ON auth.sesiones_usuario(id_usuario);
CREATE INDEX idx_sesiones_activa ON auth.sesiones_usuario(activa);
CREATE INDEX idx_sesiones_fecha_actividad ON auth.sesiones_usuario(fecha_ultima_actividad);

-- =====================================================
-- TABLA: intentos_login
-- Descripción: Registra intentos de login para 
--              seguridad y auditoría
-- =====================================================

CREATE TABLE IF NOT EXISTS auth.intentos_login (
    id SERIAL PRIMARY KEY,
    nombre_usuario VARCHAR(50),
    direccion_ip VARCHAR(45),
    exitoso BOOLEAN NOT NULL,
    fecha_intento TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    mensaje TEXT
);

-- Índices para intentos_login
CREATE INDEX idx_intentos_usuario ON auth.intentos_login(nombre_usuario);
CREATE INDEX idx_intentos_ip ON auth.intentos_login(direccion_ip);
CREATE INDEX idx_intentos_fecha ON auth.intentos_login(fecha_intento);

-- =====================================================
-- COMENTARIOS EN TABLAS
-- =====================================================

COMMENT ON TABLE auth.usuarios IS 'Usuarios del sistema Evolve Soluciones';
COMMENT ON TABLE auth.sesiones_usuario IS 'Sesiones activas de usuarios';
COMMENT ON TABLE auth.intentos_login IS 'Registro de intentos de inicio de sesión';

COMMENT ON COLUMN auth.usuarios.id IS 'Identificador único del usuario';
COMMENT ON COLUMN auth.usuarios.nombre_usuario IS 'Nombre de usuario para login (coincide con columna auditor en MySQL)';
COMMENT ON COLUMN auth.usuarios.email IS 'Correo electrónico del usuario';
COMMENT ON COLUMN auth.usuarios.hash_contraseña IS 'Hash de la contraseña (bcrypt)';
COMMENT ON COLUMN auth.usuarios.rol IS 'Rol del usuario: usuario o administrador';
COMMENT ON COLUMN auth.usuarios.activo IS 'Estado del usuario (activo/inactivo)';

COMMENT ON COLUMN auth.sesiones_usuario.token_sesion IS 'Token único de la sesión';
COMMENT ON COLUMN auth.sesiones_usuario.direccion_ip IS 'IP desde donde se inició sesión';
COMMENT ON COLUMN auth.sesiones_usuario.user_agent IS 'Navegador/cliente utilizado';

-- =====================================================
-- FUNCIONES Y TRIGGERS
-- =====================================================

-- Función para actualizar fecha_ultima_actividad automáticamente
CREATE OR REPLACE FUNCTION auth.actualizar_ultima_actividad()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_ultima_actividad = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para actualizar automáticamente la última actividad
CREATE TRIGGER trigger_actualizar_actividad
    BEFORE UPDATE ON auth.sesiones_usuario
    FOR EACH ROW
    EXECUTE FUNCTION auth.actualizar_ultima_actividad();

-- =====================================================
-- PROCEDIMIENTOS ALMACENADOS
-- =====================================================

-- Procedimiento para limpiar sesiones expiradas
CREATE OR REPLACE FUNCTION auth.limpiar_sesiones_expiradas(minutos_expiracion INTEGER DEFAULT 1440)
RETURNS INTEGER AS $$
DECLARE
    filas_afectadas INTEGER;
BEGIN
    UPDATE auth.sesiones_usuario
    SET activa = FALSE
    WHERE fecha_ultima_actividad < (CURRENT_TIMESTAMP - INTERVAL '1 minute' * minutos_expiracion)
    AND activa = TRUE;
    
    GET DIAGNOSTICS filas_afectadas = ROW_COUNT;
    RETURN filas_afectadas;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION auth.limpiar_sesiones_expiradas IS 'Desactiva sesiones que han expirado por inactividad';

-- =====================================================
-- DATOS INICIALES
-- =====================================================

-- Nota: El usuario administrador se creará mediante script Python
-- para poder hashear la contraseña correctamente con bcrypt

-- =====================================================
-- PERMISOS (OPCIONAL - Ajustar según necesidad)
-- =====================================================

-- Ejemplo de permisos para un usuario de aplicación
-- GRANT USAGE ON SCHEMA auth TO evolve_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA auth TO evolve_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA auth TO evolve_app;

-- =====================================================
-- VERIFICACIÓN
-- =====================================================

-- Verificar que las tablas se crearon correctamente
DO $$
BEGIN
    RAISE NOTICE 'Verificando creación de tablas...';
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'auth' AND table_name = 'usuarios') THEN
        RAISE NOTICE '✓ Tabla auth.usuarios creada correctamente';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'auth' AND table_name = 'sesiones_usuario') THEN
        RAISE NOTICE '✓ Tabla auth.sesiones_usuario creada correctamente';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'auth' AND table_name = 'intentos_login') THEN
        RAISE NOTICE '✓ Tabla auth.intentos_login creada correctamente';
    END IF;
END $$;
