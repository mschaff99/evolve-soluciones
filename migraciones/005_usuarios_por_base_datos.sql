-- =====================================================
-- Tabla de control de usuarios por base de datos
-- =====================================================
-- Esta tabla controla qué usuarios pueden acceder a cada base de datos MySQL
-- Se valida DESPUÉS de autenticar en PostgreSQL
--
-- Ejecutar en cada base de datos MySQL: stratex, evolve, etc.
-- =====================================================
CREATE TABLE IF NOT EXISTS usuarios_acceso (
    usuario VARCHAR(50) NOT NULL COMMENT 'Usuario de PostgreSQL (nombre_usuario)',
    auditor VARCHAR(100) NOT NULL COMMENT 'Auditor asignado',
    tipo_usuario ENUM('admin', 'usuario') NOT NULL DEFAULT 'usuario' COMMENT 'admin=Administrador, usuario=Usuario normal',
    estado CHAR(1) NOT NULL DEFAULT 'V' COMMENT 'V=Vigente, I=Inactivo',
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (usuario),
    INDEX idx_estado (estado),
    INDEX idx_auditor (auditor),
    INDEX idx_tipo_usuario (tipo_usuario)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'Control de acceso de usuarios por base de datos';
-- Insertar usuarios de ejemplo
INSERT INTO usuarios_acceso (usuario, auditor, tipo_usuario, estado)
VALUES ('admin-stratex', 'admin', 'admin', 'V'),
    ('mschaff', 'matias', 'usuario', 'V') ON DUPLICATE KEY
UPDATE estado =
VALUES(estado),
    auditor =
VALUES(auditor),
    tipo_usuario =
VALUES(tipo_usuario);
-- =====================================================
-- INSTRUCCIONES DE USO:
-- =====================================================
-- Este script debe ejecutarse en cada base de datos MySQL (stratex, evolve, etc.)
--
-- Ejemplo de ejecución:
-- mysql -u root -p stratex < 005_usuarios_por_base_datos.sql
-- mysql -u root -p evolve < 005_usuarios_por_base_datos.sql
--
-- Estados disponibles:
-- - 'V' (Vigente): Usuario activo
-- - 'I' (Inactivo): Usuario deshabilitado temporalmente
--
-- Tipos de usuario:
-- - 'admin': Administrador con permisos completos
-- - 'usuario': Usuario normal con permisos limitados
--
-- Ejemplos de inserción manual:
--
-- -- Agregar usuario normal:
-- INSERT INTO usuarios_acceso (usuario, auditor, tipo_usuario, estado)
-- VALUES ('juan.perez', 'auditor_juan', 'usuario', 'V');
--
-- -- Agregar administrador:
-- INSERT INTO usuarios_acceso (usuario, auditor, tipo_usuario, estado)
-- VALUES ('maria.admin', 'maria', 'admin', 'V');
--
-- -- Cambiar tipo de usuario:
-- UPDATE usuarios_acceso SET tipo_usuario = 'admin' WHERE usuario = 'mschaff';
--
-- -- Desactivar usuario:
-- UPDATE usuarios_acceso SET estado = 'I' WHERE usuario = 'juan.perez';
--
-- -- Reactivar usuario:
-- UPDATE usuarios_acceso SET estado = 'V' WHERE usuario = 'juan.perez';
-- =====================================================
