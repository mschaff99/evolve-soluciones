"""
Consultas SQL especializadas para análisis de proveedores y honorarios
"""

class ProveedoresQueries:
    """Consultas para análisis de proveedores, honorarios y anticipos"""
    
    @staticmethod
    def get_saldos_proveedores_honorarios(cuenta, periodo_hasta):
        """
        Obtiene saldos de proveedores/honorarios con información del proveedor
        CORREGIDO: Usa te_tgmovimientos para cuentas corrientes de proveedores
        
        Args:
            cuenta (str): Código de cuenta (ej: '000000210702' para proveedores)
            periodo_hasta (str): Período máximo a considerar (YYYYMM)
            
        Returns:
            str: Query SQL para obtener saldos con datos del proveedor
        """
        return f"""
        SELECT  
            a.TipoAfectado,
            a.numeroafectado,
            a.Auxiliar,
            b.nom_provee, 
            SUM(a.Debe - a.Haber) AS saldo,
            a.Fecha AS Fecha_Emision,
            a.fecvencimiento AS Fecha_Venc,
            b.rut_provee,
            CASE 
                WHEN b.rut_provee IS NOT NULL THEN 'CON_RUT'
                WHEN a.Auxiliar IS NOT NULL AND a.Auxiliar != '' THEN 'SIN_NOMBRE_PROVEEDOR'
                ELSE 'SIN_DATOS'
            END AS estado_identificacion
        FROM 
            te_tgmovimientos a
        LEFT JOIN 
            pm_tproveedor b
            ON REPLACE(TRIM(CAST(a.Auxiliar AS CHAR)), '-', '')=b.rut_provee
        WHERE 
            a.Cuenta = '{cuenta}'
            AND a.Periodo <= {periodo_hasta}
        GROUP BY
            a.TipoAfectado,
            a.numeroafectado,
            a.Auxiliar,
            b.nom_provee,
            a.Fecha,
            a.fecvencimiento,
            b.rut_provee
        HAVING 
            SUM(a.Debe - a.Haber) <> 0
        ORDER BY
            ABS(SUM(a.Debe - a.Haber)) DESC
        """
    
    @staticmethod
    def get_saldos_anticipos_con_rut_glosa(cuenta, periodo_hasta):
        """
        Obtiene saldos de anticipos extrayendo RUT de las glosas cuando RutTesoreria está vacío
        ESPECÍFICO para cuentas de anticipos (116xxx)
        
        Args:
            cuenta (str): Código de cuenta de anticipos (ej: '000000116002')
            periodo_hasta (str): Período máximo a considerar (YYYYMM)
            
        Returns:
            str: Query SQL para obtener saldos agrupados por RUT extraído de glosa
        """
        return f"""
        SELECT  
            a.Tipo as TipoAfectado,
            a.Numero as numeroafectado,
            a.RutTesoreria as Auxiliar,
            LEFT(b.Glosa, 50) as nom_provee,
            SUM(COALESCE(a.debe, 0) - COALESCE(a.haber, 0)) AS saldo,
            MIN(a.Fecha) AS Fecha_Emision,
            MAX(a.Fecha) AS Fecha_Ultimo_Mov,
            a.RutTesoreria as rut_provee,
            b.Glosa as glosa_completa,
            -- Análisis de antigüedad
            CASE 
                WHEN MIN(a.Fecha) < 20200101 THEN 'MUY_ANTIGUO'
                WHEN MIN(a.Fecha) < 20220101 THEN 'ANTIGUO'
                WHEN MIN(a.Fecha) < 20240101 THEN 'RECIENTE'
                ELSE 'ACTUAL'
            END AS categoria_antiguedad,
            -- Días desde el primer movimiento
            DATEDIFF(CURDATE(), STR_TO_DATE(CAST(MIN(a.Fecha) AS CHAR), '%Y%m%d')) AS dias_antiguedad,
            -- Análisis de estado
            CASE 
                WHEN a.RutTesoreria IS NOT NULL AND a.RutTesoreria != '' AND a.RutTesoreria != '-' THEN 'CON_RUT'
                WHEN b.Glosa LIKE '%-%' AND (b.Glosa LIKE '%ANTICIPO%' OR b.Glosa LIKE '%PAGO%') THEN 'RUT_EN_GLOSA'
                WHEN b.Glosa LIKE '%AJUSTE%' OR b.Glosa LIKE '%REGULARIZA%' THEN 'AJUSTE_MANUAL'
                WHEN b.Glosa LIKE '%CIERRE%' THEN 'AJUSTE_CIERRE'
                ELSE 'SIN_DATOS'
            END AS estado_identificacion,
            -- Clasificación de problemas
            CASE 
                WHEN SUM(COALESCE(a.debe, 0) - COALESCE(a.haber, 0)) < 0 THEN 'SALDO_NEGATIVO'
                WHEN MIN(a.Fecha) < 20200101 THEN 'MUY_ANTIGUO'
                WHEN (a.RutTesoreria IS NULL OR a.RutTesoreria = '' OR a.RutTesoreria = '-') 
                     AND (b.Glosa NOT LIKE '%-%' OR b.Glosa NOT LIKE '%ANTICIPO%') THEN 'SIN_IDENTIFICACION'
                ELSE 'NORMAL'
            END AS categoria_problema,
            -- Contador de movimientos
            COUNT(*) as cantidad_movimientos
        FROM 
            co_tdvouchers a
        LEFT JOIN 
            co_tcvouchers b ON a.Tipo=b.Tipo AND a.Numero=b.Numero
        WHERE 
            a.ind_estado = 'V'
            AND a.Cuenta = '{cuenta}'
            AND a.periodo <= {periodo_hasta}
        GROUP BY
            a.Tipo,
            a.Numero,
            a.RutTesoreria,
            b.Glosa
        HAVING 
            SUM(COALESCE(a.debe, 0) - COALESCE(a.haber, 0)) <> 0
        ORDER BY
            dias_antiguedad DESC,
            ABS(SUM(COALESCE(a.debe, 0) - COALESCE(a.haber, 0))) DESC
        """
    
    @staticmethod
    def get_mayor_con_rutesoria(cuenta, periodo_inicio=None, periodo_fin=None):
        """
        Obtiene el mayor de una cuenta con RutTesoreria para análisis de relaciones
        
        Args:
            cuenta (str): Código de cuenta
            periodo_inicio (str): Período inicio (opcional, se autodetecta si es None)
            periodo_fin (str): Período fin (opcional, se autodetecta si es None)
            
        Returns:
            str: Query SQL completa con parámetros y mayor ordenado
        """
        # Generar valores correctos para SQL
        inicio_sql = f"'{periodo_inicio}'" if periodo_inicio else "NULL"
        fin_sql = f"'{periodo_fin}'" if periodo_fin else "NULL"
        
        return f"""
        /* ===================== PARÁMETROS ===================== */
        /* Cuenta a revisar */
        SET @p_cuenta := '{cuenta}';

        /* Rangos de período */
        SET @p_inicio := {inicio_sql};
        SET @p_fin    := {fin_sql};

        /* ===== Autodetección de rango ===== */
        SET @p_inicio := COALESCE(
          @p_inicio,
          (SELECT MIN(periodo) FROM co_tdvouchers WHERE ind_estado='V' AND Cuenta=@p_cuenta)
        );
        SET @p_fin := COALESCE(
          @p_fin,
          (SELECT MAX(periodo) FROM co_tdvouchers WHERE ind_estado='V' AND Cuenta=@p_cuenta)
        );

        /* ===== Saldo inicial (antes del rango) ===== */
        SET @saldo_ini := COALESCE((
          SELECT SUM(COALESCE(debe,0) - COALESCE(haber,0))
          FROM co_tdvouchers
          WHERE ind_estado='V'
            AND Cuenta = @p_cuenta
            AND periodo < @p_inicio
        ), 0);

        /* ===== Acumuladores ===== */
        SET @saldo := @saldo_ini;
        SET @row   := 0;

        /* ===== Mayor ordenado por fecha con RutTesoreria ===== */
        SELECT
          t.Tipo,
          t.Numero,
          t.Fecha,              -- entero YYYYMMDD original
          t.periodo,
          t.Glosa,
          t.debe,
          t.haber,
          t.RutTesoreria,
          (@saldo := @saldo + (t.debe - t.haber)) AS saldo_acumulado,
          CASE WHEN (@row := @row + 1) = 1 THEN 'SI' ELSE '' END AS marca_inicio,
          @saldo_ini AS saldo_inicial,
          /* Campos adicionales para análisis */
          CASE 
            WHEN t.RutTesoreria IS NOT NULL AND t.RutTesoreria != '' THEN 'CON_RUT'
            WHEN t.Glosa LIKE '%ANTICIPO%' OR t.Glosa LIKE '%ADELANTO%' THEN 'POSIBLE_ANTICIPO'
            WHEN t.Glosa LIKE '%HONORARIO%' OR t.Glosa LIKE '%SERVICIO%' THEN 'POSIBLE_HONORARIO'
            ELSE 'SIN_CLASIFICAR'
          END AS tipo_movimiento,
          ABS(t.debe - t.haber) AS monto_absoluto
        FROM (
          SELECT
            a.Tipo,
            a.Numero,
            a.Fecha,
            a.periodo,
            b.Glosa,
            a.RutTesoreria,
            COALESCE(a.debe,  0) AS debe,
            COALESCE(a.haber, 0) AS haber,
            /* fecha DATE derivada para ordenar con precisión */
            STR_TO_DATE(CAST(a.Fecha AS CHAR), '%Y%m%d') AS fecha_ord
          FROM co_tdvouchers a
          LEFT JOIN co_tcvouchers b
            ON a.Tipo=b.Tipo AND a.Numero=b.Numero
          WHERE a.ind_estado='V'
            AND a.Cuenta = @p_cuenta
            AND a.periodo BETWEEN @p_inicio AND @p_fin
        ) AS t
        ORDER BY t.fecha_ord, t.Tipo, t.Numero;
        """
    
    @staticmethod
    def get_anticipos_por_rut(periodo_hasta, cuenta_anticipos=None):
        """
        Obtiene anticipos agrupados por RUT para facilitar el análisis de relaciones
        
        Args:
            periodo_hasta (str): Período máximo a considerar
            cuenta_anticipos (str): Cuenta específica de anticipos (opcional)
            
        Returns:
            str: Query SQL para obtener anticipos por RUT
        """
        filtro_cuenta = f"AND Cuenta = '{cuenta_anticipos}'" if cuenta_anticipos else ""
        
        return f"""
        SELECT 
            RutTesoreria,
            Cuenta,
            COUNT(*) as cantidad_movimientos,
            SUM(CASE WHEN debe > haber THEN debe - haber ELSE 0 END) as total_anticipos,
            SUM(CASE WHEN haber > debe THEN haber - debe ELSE 0 END) as total_aplicaciones,
            SUM(debe - haber) as saldo_neto,
            MIN(Fecha) as fecha_primer_movimiento,
            MAX(Fecha) as fecha_ultimo_movimiento,
            GROUP_CONCAT(DISTINCT LEFT(Glosa, 50) SEPARATOR ' | ') as glosas_resumen
        FROM co_tdvouchers a
        LEFT JOIN co_tcvouchers b ON a.Tipo=b.Tipo AND a.Numero=b.Numero
        WHERE a.ind_estado='V'
            AND a.periodo <= {periodo_hasta}
            AND a.RutTesoreria IS NOT NULL 
            AND a.RutTesoreria != ''
            {filtro_cuenta}
            AND (a.debe != 0 OR a.haber != 0)
        GROUP BY 
            RutTesoreria,
            Cuenta
        HAVING 
            ABS(SUM(debe - haber)) > 1000  -- Solo saldos significativos
        ORDER BY 
            ABS(SUM(debe - haber)) DESC;
        """
    
    @staticmethod
    def get_relaciones_rut_monto(rut_tesoreria, monto_objetivo, tolerancia_porcentaje=5):
        """
        Busca documentos relacionados por RUT y monto similar
        
        Args:
            rut_tesoreria (str): RUT a buscar
            monto_objetivo (float): Monto objetivo a buscar
            tolerancia_porcentaje (int): Tolerancia en porcentaje para el monto
            
        Returns:
            str: Query SQL para buscar relaciones
        """
        monto_min = monto_objetivo * (1 - tolerancia_porcentaje/100)
        monto_max = monto_objetivo * (1 + tolerancia_porcentaje/100)
        
        return f"""
        SELECT 
            a.Cuenta,
            a.Tipo,
            a.Numero,
            a.Fecha,
            a.periodo,
            b.Glosa,
            a.RutTesoreria,
            a.debe,
            a.haber,
            (a.debe - a.haber) as saldo_documento,
            ABS(a.debe - a.haber) as monto_absoluto,
            CASE 
                WHEN a.Cuenta LIKE '%1160%' THEN 'ANTICIPO_PROVEEDORES'
                WHEN a.Cuenta LIKE '%1161%' THEN 'ANTICIPO_HONORARIOS'
                WHEN a.Cuenta LIKE '%2107%' THEN 'PROVEEDORES_POR_PAGAR'
                WHEN a.Cuenta LIKE '%2108%' THEN 'HONORARIOS_POR_PAGAR'
                ELSE 'OTRA_CUENTA'
            END as tipo_cuenta,
            /* Cálculo de coincidencia de monto */
            CASE 
                WHEN ABS(ABS(a.debe - a.haber) - {monto_objetivo}) <= ({monto_objetivo} * 0.01) THEN 'EXACTO'
                WHEN ABS(ABS(a.debe - a.haber) - {monto_objetivo}) <= ({monto_objetivo} * 0.05) THEN 'MUY_CERCANO'
                WHEN ABS(ABS(a.debe - a.haber) - {monto_objetivo}) <= ({monto_objetivo} * 0.10) THEN 'CERCANO'
                ELSE 'DISTANTE'
            END as coincidencia_monto
        FROM co_tdvouchers a
        LEFT JOIN co_tcvouchers b ON a.Tipo=b.Tipo AND a.Numero=b.Numero
        WHERE a.ind_estado='V'
            AND a.RutTesoreria = '{rut_tesoreria}'
            AND ABS(a.debe - a.haber) BETWEEN {monto_min} AND {monto_max}
            AND (a.debe != 0 OR a.haber != 0)
        ORDER BY 
            ABS(ABS(a.debe - a.haber) - {monto_objetivo}) ASC,
            a.Fecha DESC;
        """
    
    @staticmethod
    def get_cuadratura_sin_rut(glosa_buscar, nombre_proveedor, monto_objetivo, tolerancia_porcentaje=10):
        """
        Busca documentos relacionados cuando no hay RUT, usando glosa y nombre de proveedor
        
        Args:
            glosa_buscar (str): Texto a buscar en la glosa
            nombre_proveedor (str): Nombre del proveedor a buscar
            monto_objetivo (float): Monto objetivo
            tolerancia_porcentaje (int): Tolerancia en porcentaje
            
        Returns:
            str: Query SQL para cuadratura sin RUT
        """
        monto_min = monto_objetivo * (1 - tolerancia_porcentaje/100)
        monto_max = monto_objetivo * (1 + tolerancia_porcentaje/100)
        
        return f"""
        SELECT 
            a.Cuenta,
            a.Tipo,
            a.Numero,
            a.Fecha,
            a.periodo,
            b.Glosa,
            a.RutTesoreria,
            a.debe,
            a.haber,
            (a.debe - a.haber) as saldo_documento,
            ABS(a.debe - a.haber) as monto_absoluto,
            /* Análisis de similitud */
            CASE 
                WHEN b.Glosa LIKE '%{glosa_buscar}%' THEN 'COINCIDE_GLOSA'
                WHEN b.Glosa LIKE '%{nombre_proveedor}%' THEN 'COINCIDE_PROVEEDOR'
                ELSE 'SIN_COINCIDENCIA_TEXTO'
            END as tipo_coincidencia,
            /* Scoring de coincidencia */
            (
                CASE WHEN b.Glosa LIKE '%{glosa_buscar}%' THEN 40 ELSE 0 END +
                CASE WHEN b.Glosa LIKE '%{nombre_proveedor}%' THEN 30 ELSE 0 END +
                CASE WHEN ABS(ABS(a.debe - a.haber) - {monto_objetivo}) <= ({monto_objetivo} * 0.05) THEN 30 ELSE 0 END
            ) as score_coincidencia
        FROM co_tdvouchers a
        LEFT JOIN co_tcvouchers b ON a.Tipo=b.Tipo AND a.Numero=b.Numero
        WHERE a.ind_estado='V'
            AND ABS(a.debe - a.haber) BETWEEN {monto_min} AND {monto_max}
            AND (
                b.Glosa LIKE '%{glosa_buscar}%' 
                OR b.Glosa LIKE '%{nombre_proveedor}%'
            )
            AND (a.debe != 0 OR a.haber != 0)
        ORDER BY 
            score_coincidencia DESC,
            ABS(ABS(a.debe - a.haber) - {monto_objetivo}) ASC;
        """
    
    @staticmethod
    def get_matching_cruzado_anticipos_proveedores(cuenta_anticipos, periodo_hasta):
        """
        Busca matching cruzado entre mayor de anticipos y cuentas corrientes de proveedores
        Extrae RUTs de glosas y los cruza con saldos de te_tgmovimientos
        
        Args:
            cuenta_anticipos (str): Código de cuenta de anticipos (ej: '000000116002')
            periodo_hasta (str): Período máximo a considerar (YYYYMM)
            
        Returns:
            str: Query SQL que encuentra relaciones cruzadas
        """
        return f"""
        -- CTE 1: Extraer RUTs de glosas del mayor de anticipos
        WITH RUTsDelMayor AS (
            SELECT DISTINCT
                -- Extraer RUT usando SUBSTRING y posiciones
                CASE 
                    WHEN b.Glosa LIKE '%-%' AND LENGTH(b.Glosa) > 10 THEN
                        TRIM(SUBSTRING_INDEX(b.Glosa, ' ', 1))
                    ELSE NULL
                END AS RutExtraido,
                b.Glosa,
                SUM(COALESCE(a.debe, 0) - COALESCE(a.haber, 0)) AS SaldoAnticipo
            FROM co_tdvouchers a
            LEFT JOIN co_tcvouchers b ON a.Tipo=b.Tipo AND a.Numero=b.Numero
            WHERE a.ind_estado = 'V'
                AND a.Cuenta = '{cuenta_anticipos}'
                AND a.periodo <= {periodo_hasta}
                AND b.Glosa IS NOT NULL
                AND (b.Glosa LIKE '%ANTICIPO%' OR b.Glosa LIKE '%PAGO%')
                AND b.Glosa LIKE '%-%'
            GROUP BY RutExtraido, b.Glosa
            HAVING RutExtraido IS NOT NULL 
                AND LENGTH(RutExtraido) >= 9
                AND RutExtraido REGEXP '^[0-9]{{7,8}}-[0-9kK]$'
        ),
        -- CTE 2: Saldos de cuentas corrientes de proveedores
        SaldosProveedores AS (
            SELECT 
                a.Auxiliar,
                b.nom_provee,
                SUM(a.Debe - a.Haber) AS SaldoProveedor,
                a.Cuenta as CuentaProveedor
            FROM te_tgmovimientos a
            LEFT JOIN pm_tproveedor b ON REPLACE(TRIM(CAST(a.Auxiliar AS CHAR)), '-', '')=b.rut_provee
            WHERE a.Periodo <= {periodo_hasta}
                AND a.Cuenta LIKE '000000210%'  -- Cuentas de proveedores
                AND a.Auxiliar IS NOT NULL
            GROUP BY a.Auxiliar, b.nom_provee, a.Cuenta
            HAVING SUM(a.Debe - a.Haber) <> 0
        )
        -- JOIN: Matching por RUT
        SELECT 
            r.RutExtraido,
            r.Glosa as GlosaAnticipo,
            r.SaldoAnticipo,
            s.nom_provee,
            s.SaldoProveedor,
            s.CuentaProveedor,
            ABS(r.SaldoAnticipo + s.SaldoProveedor) AS DiferenciaAbsoluta,
            CASE 
                WHEN ABS(r.SaldoAnticipo + s.SaldoProveedor) < 1000 THEN 'CUADRATURA_EXACTA'
                WHEN ABS(r.SaldoAnticipo + s.SaldoProveedor) / GREATEST(ABS(r.SaldoAnticipo), ABS(s.SaldoProveedor)) < 0.05 THEN 'CUADRATURA_APROXIMADA'
                ELSE 'DIFERENCIA_SIGNIFICATIVA'
            END AS TipoRelacion,
            -- Calcular score de matching
            CASE 
                WHEN ABS(r.SaldoAnticipo + s.SaldoProveedor) < 1000 THEN 100
                WHEN ABS(r.SaldoAnticipo + s.SaldoProveedor) / GREATEST(ABS(r.SaldoAnticipo), ABS(s.SaldoProveedor)) < 0.05 THEN 90
                WHEN ABS(r.SaldoAnticipo + s.SaldoProveedor) / GREATEST(ABS(r.SaldoAnticipo), ABS(s.SaldoProveedor)) < 0.15 THEN 70
                ELSE 50
            END AS ScoreMatching
        FROM RUTsDelMayor r
        INNER JOIN SaldosProveedores s ON r.RutExtraido = s.Auxiliar
        ORDER BY ScoreMatching DESC, DiferenciaAbsoluta ASC
        """
    
# Instancia global
proveedores_queries = ProveedoresQueries()
