-- ==============================================================================
-- MIGRACIÓN 007: SISTEMA DE MEMORIA HISTÓRICA DE ANÁLISIS IA
-- ==============================================================================
-- Descripción: Tablas para almacenar análisis históricos realizados por IA
--              y patrones aprendidos para mejorar análisis futuros
-- Base de datos: PostgreSQL (evolve)
-- Fecha: 2025-01-20
-- ==============================================================================
-- Tabla: ia_analisis_historico
-- Almacena todos los análisis de IA realizados con su contexto completo
CREATE TABLE IF NOT EXISTS ia_analisis_historico (
    id SERIAL PRIMARY KEY,
    -- Identificación del análisis
    empresa_rut VARCHAR(20) NOT NULL,
    empresa_nombre VARCHAR(255) NOT NULL,
    periodo_inicio INTEGER NOT NULL,
    -- Formato YYYYMM
    periodo_fin INTEGER NOT NULL,
    -- Formato YYYYMM
    fecha_analisis TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Contenido del análisis
    analisis_completo TEXT NOT NULL,
    prompt_utilizado TEXT,
    -- Metadatos del balance analizado
    total_cuentas_analizadas INTEGER DEFAULT 0,
    sumas_balance_activos NUMERIC(18, 2) DEFAULT 0,
    sumas_balance_pasivos NUMERIC(18, 2) DEFAULT 0,
    resultado_ejercicio NUMERIC(18, 2) DEFAULT 0,
    -- Hallazgos estructurados (JSON)
    hallazgos_detectados JSONB,
    cuentas_problematicas JSONB,
    recomendaciones JSONB,
    -- Estado de seguimiento
    estado_seguimiento VARCHAR(50) DEFAULT 'pendiente',
    -- Estados posibles: 'pendiente', 'en_revision', 'resuelto', 'descartado'
    -- Métricas de procesamiento
    tiempo_procesamiento_segundos INTEGER DEFAULT 0,
    tokens_utilizados INTEGER DEFAULT 0,
    -- Auditoría
    contador_responsable VARCHAR(100),
    fecha_revision TIMESTAMP,
    notas_contador TEXT,
    -- Índices para búsquedas
    CONSTRAINT chk_periodo CHECK (periodo_inicio <= periodo_fin)
);
-- Índices para optimizar consultas
CREATE INDEX IF NOT EXISTS idx_ia_analisis_empresa_rut ON ia_analisis_historico(empresa_rut);
CREATE INDEX IF NOT EXISTS idx_ia_analisis_periodo ON ia_analisis_historico(periodo_inicio, periodo_fin);
CREATE INDEX IF NOT EXISTS idx_ia_analisis_fecha ON ia_analisis_historico(fecha_analisis DESC);
CREATE INDEX IF NOT EXISTS idx_ia_analisis_estado ON ia_analisis_historico(estado_seguimiento);
-- Índice GIN para búsquedas en JSON
CREATE INDEX IF NOT EXISTS idx_ia_analisis_hallazgos ON ia_analisis_historico USING GIN (hallazgos_detectados);
-- Comentarios
COMMENT ON TABLE ia_analisis_historico IS 'Almacena análisis históricos de IA realizados sobre balances de 8 columnas';
COMMENT ON COLUMN ia_analisis_historico.hallazgos_detectados IS 'JSON con hallazgos estructurados: tipo, severidad, cuenta afectada';
COMMENT ON COLUMN ia_analisis_historico.estado_seguimiento IS 'Estado del análisis: pendiente, en_revision, resuelto, descartado';
-- ==============================================================================
-- Tabla: ia_patrones_aprendidos
-- Almacena patrones detectados por la IA para mejorar análisis futuros
-- ==============================================================================
CREATE TABLE IF NOT EXISTS ia_patrones_aprendidos (
    id SERIAL PRIMARY KEY,
    -- Identificación del patrón
    patron_nombre VARCHAR(255) NOT NULL UNIQUE,
    patron_descripcion TEXT NOT NULL,
    tipo_problema VARCHAR(100) NOT NULL,
    -- Solución recomendada
    solucion_recomendada TEXT NOT NULL,
    condiciones_activacion JSONB NOT NULL,
    -- Metadatos de uso
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_ultima_aplicacion TIMESTAMP,
    veces_aplicado INTEGER DEFAULT 0,
    efectividad_porcentaje INTEGER DEFAULT 50,
    -- Efectividad medida por feedback del contador
    -- Alcance
    empresa_rut VARCHAR(20),
    -- NULL = patrón global, aplicable a todas las empresas
    -- Estado
    activo BOOLEAN DEFAULT TRUE,
    -- Auditoría
    creado_por_analisis_id INTEGER REFERENCES ia_analisis_historico(id),
    notas TEXT,
    CONSTRAINT chk_efectividad CHECK (
        efectividad_porcentaje BETWEEN 0 AND 100
    )
);
-- Índices
CREATE INDEX IF NOT EXISTS idx_ia_patrones_tipo ON ia_patrones_aprendidos(tipo_problema);
CREATE INDEX IF NOT EXISTS idx_ia_patrones_empresa ON ia_patrones_aprendidos(empresa_rut);
CREATE INDEX IF NOT EXISTS idx_ia_patrones_activo ON ia_patrones_aprendidos(activo)
WHERE activo = TRUE;
CREATE INDEX IF NOT EXISTS idx_ia_patrones_condiciones ON ia_patrones_aprendidos USING GIN (condiciones_activacion);
-- Comentarios
COMMENT ON TABLE ia_patrones_aprendidos IS 'Patrones contables aprendidos por la IA para mejorar análisis futuros';
COMMENT ON COLUMN ia_patrones_aprendidos.condiciones_activacion IS 'JSON con condiciones que activan el patrón: tipo_cuenta, rango_monto, etc.';
COMMENT ON COLUMN ia_patrones_aprendidos.empresa_rut IS 'Si es NULL, el patrón aplica globalmente a todas las empresas';
-- ==============================================================================
-- DATOS INICIALES
-- ==============================================================================
-- Insertar patrones básicos de conocimiento contable
INSERT INTO ia_patrones_aprendidos (
        patron_nombre,
        patron_descripcion,
        tipo_problema,
        solucion_recomendada,
        condiciones_activacion,
        efectividad_porcentaje
    )
VALUES (
        'IVA_RESIDUO_TRANSITORIO',
        'Detecta residuos en cuentas de IVA que deberían cerrar mensualmente',
        'CUENTA_TRANSITORIA_CON_SALDO',
        'Revisar si el residuo corresponde a ajustes pendientes o diferencias temporales. Si persiste por más de 2 períodos, reclasificar o ajustar.',
        '{"tipo_cuenta": "Activo", "nombre_contiene": ["IVA", "CREDITO FISCAL"], "umbral_residuo": 1000}',
        80
    ),
    (
        'PROVISION_F29_NO_PAGADA',
        'Detecta provisiones de impuestos mensuales (F29) que no fueron pagadas',
        'PROVISION_PENDIENTE',
        'Verificar fecha de vencimiento del F29. Si está vencido, gestionar pago urgente. Si no, mantener provisión hasta vencimiento.',
        '{"tipo_cuenta": "Pasivo", "nombre_contiene": ["IMPUESTO", "F29", "TRIBUTARIO"], "glosa_mayor_contiene": "PROVISION F29"}',
        90
    ),
    (
        'HONORARIOS_POR_PAGAR_ANTIGUOS',
        'Detecta honorarios por pagar con más de 90 días de antigüedad',
        'CUENTA_PENDIENTE_ANTIGUA',
        'Revisar estado con el proveedor. Considerar provisión por incobrabilidad si hay disputa. Gestionar pago si está pendiente.',
        '{"tipo_cuenta": "Pasivo", "nombre_contiene": ["HONORARIO"], "dias_antiguedad_mayor": 90}',
        75
    ) ON CONFLICT (patron_nombre) DO NOTHING;
-- ==============================================================================
-- PERMISOS (Ajustar según usuarios del sistema)
-- ==============================================================================
-- GRANT SELECT, INSERT, UPDATE ON ia_analisis_historico TO contador_role;
-- GRANT SELECT ON ia_patrones_aprendidos TO contador_role;
-- ==============================================================================
-- FIN DE MIGRACIÓN 007
-- ==============================================================================
-- Para aplicar esta migración:
-- psql -U postgres -d evolve -f 007_modulo_ia_memoria.sql
-- Para verificar que se aplicó correctamente:
-- SELECT table_name FROM information_schema.tables
-- WHERE table_schema = 'public' AND table_name LIKE 'ia_%';
