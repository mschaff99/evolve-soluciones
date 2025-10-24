-- =====================================================
-- Agregar columna tipo_usuario a tabla existente
-- =====================================================
-- Ejecutar este script si ya tienes la tabla usuarios_acceso
-- y solo necesitas agregar la columna tipo_usuario
-- =====================================================
-- Agregar columna tipo_usuario
ALTER TABLE usuarios_acceso
ADD COLUMN tipo_usuario ENUM('admin', 'usuario') NOT NULL DEFAULT 'usuario' COMMENT 'admin=Administrador, usuario=Usuario normal'
AFTER auditor;
-- Agregar índice
CREATE INDEX idx_tipo_usuario ON usuarios_acceso(tipo_usuario);
-- Actualizar usuarios existentes basándose en el nombre
-- Detectar admins por nombre que contenga 'admin'
UPDATE usuarios_acceso
SET tipo_usuario = 'admin'
WHERE usuario LIKE '%admin%'
    OR usuario = 'admin-stratex';
-- Marcar PILAR como admin si corresponde (ajustar según tu caso)
-- UPDATE usuarios_acceso SET tipo_usuario = 'admin' WHERE usuario = 'PILAR';
-- Verificar cambios
SELECT usuario,
    auditor,
    tipo_usuario,
    estado
FROM usuarios_acceso
ORDER BY tipo_usuario DESC,
    usuario;
-- =====================================================
-- INSTRUCCIONES:
-- =====================================================
-- 1. Ejecutar en cada base de datos donde exista usuarios_acceso:
--    mysql -u root -p stratex < 005b_agregar_tipo_usuario.sql
--    mysql -u root -p evolve < 005b_agregar_tipo_usuario.sql
--
-- 2. Verificar que los usuarios tengan el tipo correcto
-- 3. Ajustar manualmente si es necesario:
--    UPDATE usuarios_acceso SET tipo_usuario = 'admin' WHERE usuario = 'nombre_usuario';
-- =====================================================
