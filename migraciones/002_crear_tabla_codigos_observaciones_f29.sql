-- =============================================================================
-- Migración 002: Tabla de Códigos de Observaciones F29
-- =============================================================================
-- Base de datos: evolve (PostgreSQL)
-- Propósito: Almacenar catálogo de códigos de observaciones del Formulario 29
-- Fecha: 2025-10-06
-- =============================================================================
-- Verificar si estamos en la base de datos correcta
SELECT current_database();
-- Crear tabla de códigos de observaciones F29
CREATE TABLE IF NOT EXISTS codigos_observaciones_f29 (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL UNIQUE,
    descripcion TEXT NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Constraints
    CONSTRAINT chk_codigo_no_vacio CHECK (codigo <> ''),
    CONSTRAINT chk_descripcion_no_vacia CHECK (descripcion <> '')
);
-- Crear índices para mejorar performance
CREATE INDEX IF NOT EXISTS idx_codigos_obs_codigo ON codigos_observaciones_f29(codigo);
CREATE INDEX IF NOT EXISTS idx_codigos_obs_activo ON codigos_observaciones_f29(activo);
-- Comentarios en la tabla
COMMENT ON TABLE codigos_observaciones_f29 IS 'Catálogo de códigos de observaciones del Formulario 29 (F29) del SII';
COMMENT ON COLUMN codigos_observaciones_f29.codigo IS 'Código único de la observación (ej: W39, FM01, PPM01)';
COMMENT ON COLUMN codigos_observaciones_f29.descripcion IS 'Descripción detallada del código de observación';
COMMENT ON COLUMN codigos_observaciones_f29.activo IS 'Indica si el código está activo y debe mostrarse en el sistema';
-- =============================================================================
-- Insertar datos iniciales
-- =============================================================================
INSERT INTO codigos_observaciones_f29 (codigo, descripcion)
VALUES ('W39', 'Control Precautorio Proveedores'),
    ('FM01', 'Remanente CF'),
    ('PPM01', 'PPM'),
    ('W08', 'Crédito Fiscal'),
    ('W38', 'Nota de Crédito Emitidas fuera de plazo'),
    ('W40', 'Nota de Crédito Emitidas fuera de plazo'),
    ('W01', 'Débito Fiscal'),
    ('W22', 'Exportaciones'),
    ('W10', 'NC Compras'),
    ('PPM08', 'Honorarios'),
    ('W19', 'Impuesto Especifico (Crédito)'),
    ('W14', 'IVA Retenido a Terceros'),
    ('W12', 'Importaciones'),
    ('PPM10', 'Retencion impuesto tasa 10%'),
    ('W01LF', 'Debito Fiscal'),
    ('W16', 'Iva Retenido por NC emitidas') ON CONFLICT (codigo) DO NOTHING;
-- =============================================================================
-- Función trigger para actualizar fecha_actualizacion automáticamente
-- =============================================================================
CREATE OR REPLACE FUNCTION actualizar_fecha_modificacion() RETURNS TRIGGER AS $$ BEGIN NEW.fecha_actualizacion = CURRENT_TIMESTAMP;
RETURN NEW;
END;
$$ LANGUAGE plpgsql;
-- Crear trigger
DROP TRIGGER IF EXISTS trg_actualizar_fecha_codigos_obs ON codigos_observaciones_f29;
CREATE TRIGGER trg_actualizar_fecha_codigos_obs BEFORE
UPDATE ON codigos_observaciones_f29 FOR EACH ROW EXECUTE FUNCTION actualizar_fecha_modificacion();
-- =============================================================================
-- Verificación de instalación
-- =============================================================================
-- Mostrar todos los códigos insertados
SELECT codigo,
    descripcion
FROM codigos_observaciones_f29
WHERE activo = TRUE
ORDER BY codigo;
-- Mensaje de éxito
DO $$ BEGIN RAISE NOTICE '✓ Tabla codigos_observaciones_f29 creada exitosamente';
RAISE NOTICE '✓ % códigos insertados',
(
    SELECT COUNT(*)
    FROM codigos_observaciones_f29
);
RAISE NOTICE '✓ Trigger de actualización configurado';
END $$;
