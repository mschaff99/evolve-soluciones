"""
Queries SQL para el sistema de balances contables
"""


class BalanceQueries:
    """Consultas SQL para generación de balances de 8 columnas"""
    
    @staticmethod
    def get_balance_8_columnas_query():
        """

        """
        return """
                SELECT *
                FROM (
                  /* ================== 1) DETALLE POR CUENTA (con Nombre) ================== */
                  SELECT
                      d.cuenta,
                      cta.Nombre AS nombre,
                      CASE COALESCE(d.tipocuenta,'')
                        WHEN 'AC' THEN 'Activo'
                        WHEN 'PA' THEN 'Pasivo'
                        WHEN 'PR' THEN 'Patrimonio'
                        WHEN 'PE' THEN 'Gasto'
                        WHEN 'GA' THEN 'Ingreso'
                        ELSE d.tipocuenta
                      END AS tipo_cuenta,

                      d.saldo_inicial_deudor   AS saldos_iniciales_deudor,
                      d.saldo_inicial_acreedor AS saldos_iniciales_acreedor,
                      d.movimiento_debe        AS debitos,
                      d.movimiento_haber       AS creditos,

                      /* Balance final en columnas Activo/Pasivo */
                      (CASE WHEN d.tipocuenta='AC'           THEN d.saldo_final_deudor   ELSE 0 END) +
                      (CASE WHEN d.tipocuenta IN ('PA','PR') THEN d.saldo_final_deudor   ELSE 0 END) AS activos,

                      (CASE WHEN d.tipocuenta IN ('PA','PR') THEN d.saldo_final_acreedor ELSE 0 END) +
                      (CASE WHEN d.tipocuenta='AC'           THEN d.saldo_final_acreedor ELSE 0 END) AS pasivos,

                      /* Pérdida/Ganancia (solo resultados) */
                      /* PE (Gasto): si debe > haber = pérdida (deudor), si haber > debe = 0 (se va a ganancia) */
                      /* GA (Ingreso): si haber > debe = 0 (se va a ganancia), si debe > haber = 0 (no aplica) */
                      CASE 
                        WHEN d.tipocuenta='PE' THEN d.saldo_final_deudor
                        WHEN d.tipocuenta='GA' THEN d.saldo_final_deudor
                        ELSE 0 
                      END AS perdida,
                      
                      /* GA (Ingreso): si haber > debe = ganancia (acreedor) */
                      /* PE (Gasto): si haber > debe = ganancia (acreedor negativo) */
                      CASE 
                        WHEN d.tipocuenta='GA' THEN d.saldo_final_acreedor
                        WHEN d.tipocuenta='PE' THEN d.saldo_final_acreedor
                        ELSE 0 
                      END AS ganancia,

                      0 AS ord
                  FROM (
                      /* ===== base por cuenta: INI (ajustada), MOV y FIN (usando INI_ajustada) ===== */
                      SELECT
                          c.cuenta,
                          COALESCE(i.tipocuenta, m.tipocuenta) AS tipocuenta,

                          /* saldo inicial AJUSTADO: 0 para PE y GA */
                          CASE
                            WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0
                            ELSE COALESCE(i.saldo_ini,0)
                          END AS saldo_ini_ajustada,

                          /* Inicial (D/A) con AJUSTE aplicado */
                          CASE
                            WHEN (CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END) > 0
                              THEN (CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END)
                            ELSE 0
                          END AS saldo_inicial_deudor,
                          CASE
                            WHEN (CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END) < 0
                              THEN -((CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END))
                            ELSE 0
                          END AS saldo_inicial_acreedor,

                          /* Movimientos del período */
                          COALESCE(m.mov_debe,0)  AS movimiento_debe,
                          COALESCE(m.mov_haber,0) AS movimiento_haber,

                          /* Saldo final (con INI AJUSTADA) */
                          CASE
                            WHEN (CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END)
                                 + COALESCE(m.mov_debe,0) - COALESCE(m.mov_haber,0) > 0
                              THEN (CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END)
                                   + COALESCE(m.mov_debe,0) - COALESCE(m.mov_haber,0)
                            ELSE 0
                          END AS saldo_final_deudor,
                          CASE
                            WHEN (CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END)
                                 + COALESCE(m.mov_debe,0) - COALESCE(m.mov_haber,0) < 0
                              THEN -((CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END)
                                    + COALESCE(m.mov_debe,0) - COALESCE(m.mov_haber,0))
                            ELSE 0
                          END AS saldo_final_acreedor
                      FROM (
                          SELECT DISTINCT cuenta FROM co_tgsaldos_mes WHERE mes < %s
                          UNION
                          SELECT DISTINCT cuenta FROM co_tgsaldos_mes WHERE mes BETWEEN %s AND %s
                      ) c
                      LEFT JOIN (
                          SELECT
                              cuenta,
                              MAX(tipocuenta) AS tipocuenta,
                              SUM(COALESCE(debe,0)-COALESCE(haber,0)) AS saldo_ini
                          FROM co_tgsaldos_mes
                          WHERE mes < %s
                          GROUP BY cuenta
                      ) i ON i.cuenta = c.cuenta
                      LEFT JOIN (
                          SELECT
                              cuenta,
                              MAX(tipocuenta) AS tipocuenta,
                              SUM(COALESCE(debe,0))  AS mov_debe,
                              SUM(COALESCE(haber,0)) AS mov_haber
                          FROM co_tgsaldos_mes
                          WHERE mes BETWEEN %s AND %s
                          GROUP BY cuenta
                      ) m ON m.cuenta = c.cuenta
                  ) AS d
                  LEFT JOIN co_tgcuentas cta
                         ON cta.Codigo = d.cuenta
                  /* <<< FILTRO NUEVO - Solo cuentas con actividad >>>  */
                  WHERE (d.saldo_inicial_deudor <> 0
                      OR d.saldo_inicial_acreedor <> 0
                      OR d.movimiento_debe <> 0
                      OR d.movimiento_haber <> 0)

                  UNION ALL

                  /* ================== 2) SUMAS (usando INI AJUSTADA) ================== */
                  SELECT
                      'Sumas' AS cuenta,
                      ''      AS nombre,
                      ''      AS tipo_cuenta,
                      t.ini_deb  AS saldos_iniciales_deudor,
                      t.ini_acr  AS saldos_iniciales_acreedor,
                      t.mov_deb  AS debitos,
                      t.mov_hab  AS creditos,
                      t.fin_ac_deb + t.fin_papr_deb AS activos,
                      t.fin_papr_acr + t.fin_ac_acr AS pasivos,
                      t.perd_sum AS perdida,
                      t.gan_sum  AS ganancia,
                      1 AS ord
                  FROM (
                      SELECT
                          SUM(base.saldo_inicial_deudor)   AS ini_deb,
                          SUM(base.saldo_inicial_acreedor) AS ini_acr,
                          SUM(base.movimiento_debe)        AS mov_deb,
                          SUM(base.movimiento_haber)       AS mov_hab,
                          SUM(CASE WHEN base.tipocuenta='AC'          THEN base.saldo_final_deudor   ELSE 0 END) AS fin_ac_deb,
                          SUM(CASE WHEN base.tipocuenta='AC'          THEN base.saldo_final_acreedor ELSE 0 END) AS fin_ac_acr,
                          SUM(CASE WHEN base.tipocuenta IN('PA','PR') THEN base.saldo_final_deudor   ELSE 0 END) AS fin_papr_deb,
                          SUM(CASE WHEN base.tipocuenta IN('PA','PR') THEN base.saldo_final_acreedor ELSE 0 END) AS fin_papr_acr,
                          /* CORREGIDO: Pérdida incluye PE y GA con saldo deudor */
                          SUM(CASE WHEN base.tipocuenta IN('PE','GA') THEN base.saldo_final_deudor   ELSE 0 END) AS perd_sum,
                          /* CORREGIDO: Ganancia incluye GA y PE con saldo acreedor */
                          SUM(CASE WHEN base.tipocuenta IN('PE','GA') THEN base.saldo_final_acreedor ELSE 0 END) AS gan_sum
                      FROM (
                          /* misma base pero con INI AJUSTADA para PE/GA */
                          SELECT
                              COALESCE(i.tipocuenta, m.tipocuenta) AS tipocuenta,
                              CASE
                                WHEN (CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END) > 0
                                  THEN (CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END)
                                ELSE 0
                              END AS saldo_inicial_deudor,
                              CASE
                                WHEN (CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END) < 0
                                  THEN -(CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END)
                                ELSE 0
                              END AS saldo_inicial_acreedor,
                              COALESCE(m.mov_debe,0)  AS movimiento_debe,
                              COALESCE(m.mov_haber,0) AS movimiento_haber,
                              CASE
                                WHEN (CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END)
                                     + COALESCE(m.mov_debe,0) - COALESCE(m.mov_haber,0) > 0
                                  THEN (CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END)
                                       + COALESCE(m.mov_debe,0) - COALESCE(m.mov_haber,0)
                                ELSE 0
                              END AS saldo_final_deudor,
                              CASE
                                WHEN (CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END)
                                     + COALESCE(m.mov_debe,0) - COALESCE(m.mov_haber,0) < 0
                                  THEN -((CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END)
                                        + COALESCE(m.mov_debe,0) - COALESCE(m.mov_haber,0))
                                ELSE 0
                              END AS saldo_final_acreedor
                          FROM (
                              SELECT DISTINCT cuenta FROM co_tgsaldos_mes WHERE mes < %s
                              UNION
                              SELECT DISTINCT cuenta FROM co_tgsaldos_mes WHERE mes BETWEEN %s AND %s
                          ) c
                          LEFT JOIN (
                              SELECT cuenta, MAX(tipocuenta) AS tipocuenta,
                                     SUM(COALESCE(debe,0)-COALESCE(haber,0)) AS saldo_ini
                              FROM co_tgsaldos_mes
                              WHERE mes < %s
                              GROUP BY cuenta
                          ) i ON i.cuenta = c.cuenta
                          LEFT JOIN (
                              SELECT cuenta, MAX(tipocuenta) AS tipocuenta,
                                     SUM(COALESCE(debe,0))  AS mov_debe,
                                     SUM(COALESCE(haber,0)) AS mov_haber
                              FROM co_tgsaldos_mes
                              WHERE mes BETWEEN %s AND %s
                              GROUP BY cuenta
                          ) m ON m.cuenta = c.cuenta
                      ) base
                  ) t

                  UNION ALL
                  /* ======= 3) RESULTADO EJERCICIO ======= */
                  SELECT
                      'Resultado Ejercicio', '', '', 0,0,0,0,
                      GREATEST( (tb.fin_papr_acr + tb.fin_ac_acr) - (tb.fin_ac_deb + tb.fin_papr_deb), 0 ),
                      GREATEST( (tb.fin_ac_deb + tb.fin_papr_deb) - (tb.fin_papr_acr + tb.fin_ac_acr), 0 ),
                      GREATEST( tp.gan_sum - tp.perd_sum, 0 ),
                      GREATEST( tp.perd_sum - tp.gan_sum, 0 ),
                      2
                  FROM (
                      SELECT
                          SUM(CASE WHEN base.tipocuenta='AC'          THEN base.saldo_final_deudor   ELSE 0 END) AS fin_ac_deb,
                          SUM(CASE WHEN base.tipocuenta='AC'          THEN base.saldo_final_acreedor ELSE 0 END) AS fin_ac_acr,
                          SUM(CASE WHEN base.tipocuenta IN('PA','PR') THEN base.saldo_final_deudor   ELSE 0 END) AS fin_papr_deb,
                          SUM(CASE WHEN base.tipocuenta IN('PA','PR') THEN base.saldo_final_acreedor ELSE 0 END) AS fin_papr_acr
                      FROM (
                          SELECT
                              COALESCE(i.tipocuenta, m.tipocuenta) AS tipocuenta,
                              CASE
                                WHEN (CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END)
                                     + COALESCE(m.mov_debe,0) - COALESCE(m.mov_haber,0) > 0
                                  THEN (CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END)
                                       + COALESCE(m.mov_debe,0) - COALESCE(m.mov_haber,0)
                                ELSE 0
                              END AS saldo_final_deudor,
                              CASE
                                WHEN (CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END)
                                     + COALESCE(m.mov_debe,0) - COALESCE(m.mov_haber,0) < 0
                                  THEN -((CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END)
                                        + COALESCE(m.mov_debe,0) - COALESCE(m.mov_haber,0))
                                ELSE 0
                              END AS saldo_final_acreedor
                          FROM (
                              SELECT DISTINCT cuenta FROM co_tgsaldos_mes WHERE mes < %s
                              UNION
                              SELECT DISTINCT cuenta FROM co_tgsaldos_mes WHERE mes BETWEEN %s AND %s
                          ) c
                          LEFT JOIN (
                              SELECT cuenta, MAX(tipocuenta) AS tipocuenta,
                                     SUM(COALESCE(debe,0)-COALESCE(haber,0)) AS saldo_ini
                              FROM co_tgsaldos_mes
                              WHERE mes < %s
                              GROUP BY cuenta
                          ) i ON i.cuenta = c.cuenta
                          LEFT JOIN (
                              SELECT cuenta, MAX(tipocuenta) AS tipocuenta,
                                     SUM(COALESCE(debe,0))  AS mov_debe,
                                     SUM(COALESCE(haber,0)) AS mov_haber
                              FROM co_tgsaldos_mes
                              WHERE mes BETWEEN %s AND %s
                              GROUP BY cuenta
                          ) m ON m.cuenta = c.cuenta
                      ) base
                  ) tb
                  CROSS JOIN (
                      SELECT
                          /* CORREGIDO: Pérdida incluye PE y GA con saldo deudor */
                          SUM(CASE WHEN base.tipocuenta IN('PE','GA') THEN base.saldo_final_deudor   ELSE 0 END) AS perd_sum,
                          /* CORREGIDO: Ganancia incluye GA y PE con saldo acreedor */
                          SUM(CASE WHEN base.tipocuenta IN('PE','GA') THEN base.saldo_final_acreedor ELSE 0 END) AS gan_sum
                      FROM (
                          SELECT
                              COALESCE(i.tipocuenta, m.tipocuenta) AS tipocuenta,
                              CASE
                                WHEN (CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END)
                                     + COALESCE(m.mov_debe,0) - COALESCE(m.mov_haber,0) > 0
                                  THEN (CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END)
                                       + COALESCE(m.mov_debe,0) - COALESCE(m.mov_haber,0)
                                ELSE 0
                              END AS saldo_final_deudor,
                              CASE
                                WHEN (CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END)
                                     + COALESCE(m.mov_debe,0) - COALESCE(m.mov_haber,0) < 0
                                  THEN -((CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END)
                                        + COALESCE(m.mov_debe,0) - COALESCE(m.mov_haber,0))
                                ELSE 0
                              END AS saldo_final_acreedor
                          FROM (
                              SELECT DISTINCT cuenta FROM co_tgsaldos_mes WHERE mes < %s
                              UNION
                              SELECT DISTINCT cuenta FROM co_tgsaldos_mes WHERE mes BETWEEN %s AND %s
                          ) c
                          LEFT JOIN (
                              SELECT cuenta, MAX(tipocuenta) AS tipocuenta,
                                     SUM(COALESCE(debe,0)-COALESCE(haber,0)) AS saldo_ini
                              FROM co_tgsaldos_mes
                              WHERE mes < %s
                              GROUP BY cuenta
                          ) i ON i.cuenta = c.cuenta
                          LEFT JOIN (
                              SELECT cuenta, MAX(tipocuenta) AS tipocuenta,
                                     SUM(COALESCE(debe,0))  AS mov_debe,
                                     SUM(COALESCE(haber,0)) AS mov_haber
                              FROM co_tgsaldos_mes
                              WHERE mes BETWEEN %s AND %s
                              GROUP BY cuenta
                          ) m ON m.cuenta = c.cuenta
                      ) base
                  ) tp

                  UNION ALL

                  /* ======= 4) SUMAS IGUALES ======= */
                  SELECT
                      'Sumas Iguales' AS cuenta,
                      '' AS nombre,
                      '' AS tipo_cuenta,
                      t.ini_deb  AS saldos_iniciales_deudor,
                      t.ini_acr  AS saldos_iniciales_acreedor,
                      t.mov_deb  AS debitos,
                      t.mov_hab  AS creditos,
                      (t.fin_ac_deb + t.fin_papr_deb)
                        + GREATEST( (t.fin_papr_acr + t.fin_ac_acr) - (t.fin_ac_deb + t.fin_papr_deb), 0 ) AS activos,
                      (t.fin_papr_acr + t.fin_ac_acr)
                        + GREATEST( (t.fin_ac_deb + t.fin_papr_deb) - (t.fin_papr_acr + t.fin_ac_acr), 0 ) AS pasivos,
                      t.perd_sum + GREATEST( t.gan_sum - t.perd_sum, 0 ) AS perdida,
                      t.gan_sum  + GREATEST( t.perd_sum - t.gan_sum, 0 ) AS ganancia,
                      3 AS ord
                  FROM (
                      SELECT
                          SUM(base.saldo_inicial_deudor)   AS ini_deb,
                          SUM(base.saldo_inicial_acreedor) AS ini_acr,
                          SUM(base.movimiento_debe)        AS mov_deb,
                          SUM(base.movimiento_haber)       AS mov_hab,
                          SUM(CASE WHEN base.tipocuenta='AC'          THEN base.saldo_final_deudor   ELSE 0 END) AS fin_ac_deb,
                          SUM(CASE WHEN base.tipocuenta='AC'          THEN base.saldo_final_acreedor ELSE 0 END) AS fin_ac_acr,
                          SUM(CASE WHEN base.tipocuenta IN('PA','PR') THEN base.saldo_final_deudor   ELSE 0 END) AS fin_papr_deb,
                          SUM(CASE WHEN base.tipocuenta IN('PA','PR') THEN base.saldo_final_acreedor ELSE 0 END) AS fin_papr_acr,
                          /* CORREGIDO: Pérdida incluye PE y GA con saldo deudor */
                          SUM(CASE WHEN base.tipocuenta IN('PE','GA') THEN base.saldo_final_deudor   ELSE 0 END) AS perd_sum,
                          /* CORREGIDO: Ganancia incluye GA y PE con saldo acreedor */
                          SUM(CASE WHEN base.tipocuenta IN('PE','GA') THEN base.saldo_final_acreedor ELSE 0 END) AS gan_sum
                      FROM (
                          SELECT
                              COALESCE(i.tipocuenta, m.tipocuenta) AS tipocuenta,
                              CASE
                                WHEN (CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END) > 0
                                  THEN (CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END)
                                ELSE 0
                              END AS saldo_inicial_deudor,
                              CASE
                                WHEN (CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END) < 0
                                  THEN -(CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END)
                                ELSE 0
                              END AS saldo_inicial_acreedor,
                              COALESCE(m.mov_debe,0)  AS movimiento_debe,
                              COALESCE(m.mov_haber,0) AS movimiento_haber,
                              CASE
                                WHEN (CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END)
                                     + COALESCE(m.mov_debe,0) - COALESCE(m.mov_haber,0) > 0
                                  THEN (CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END)
                                       + COALESCE(m.mov_debe,0) - COALESCE(m.mov_haber,0)
                                ELSE 0
                              END AS saldo_final_deudor,
                              CASE
                                WHEN (CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END)
                                     + COALESCE(m.mov_debe,0) - COALESCE(m.mov_haber,0) < 0
                                  THEN -((CASE WHEN COALESCE(i.tipocuenta, m.tipocuenta) IN ('PE','GA') THEN 0 ELSE COALESCE(i.saldo_ini,0) END)
                                        + COALESCE(m.mov_debe,0) - COALESCE(m.mov_haber,0))
                                ELSE 0
                              END AS saldo_final_acreedor
                          FROM (
                              SELECT DISTINCT cuenta FROM co_tgsaldos_mes WHERE mes < %s
                              UNION
                              SELECT DISTINCT cuenta FROM co_tgsaldos_mes WHERE mes BETWEEN %s AND %s
                          ) c
                          LEFT JOIN (
                              SELECT cuenta, MAX(tipocuenta) AS tipocuenta,
                                     SUM(COALESCE(debe,0)-COALESCE(haber,0)) AS saldo_ini
                              FROM co_tgsaldos_mes
                              WHERE mes < %s
                              GROUP BY cuenta
                          ) i ON i.cuenta = c.cuenta
                          LEFT JOIN (
                              SELECT cuenta, MAX(tipocuenta) AS tipocuenta,
                                     SUM(COALESCE(debe,0))  AS mov_debe,
                                     SUM(COALESCE(haber,0)) AS mov_haber
                              FROM co_tgsaldos_mes
                              WHERE mes BETWEEN %s AND %s
                              GROUP BY cuenta
                          ) m ON m.cuenta = c.cuenta
                      ) base
                  ) t
                ) z
                ORDER BY 
                    z.ord,
                    CASE z.tipo_cuenta
                        WHEN 'Activo' THEN 1
                        WHEN 'Pasivo' THEN 2
                        WHEN 'Patrimonio' THEN 3
                        WHEN 'Ingreso' THEN 4
                        WHEN 'Gasto' THEN 5
                        ELSE 6
                    END,
                    z.cuenta
                """
    
    @staticmethod
    def get_balance_parameters_count():
        """
        Retorna la cantidad de parámetros que necesita la consulta de balance de 8 columnas
        
        Returns:
            int: Número total de parámetros necesarios
        """
        return 30
    
    @staticmethod 
    def build_balance_parameters(periodo_inicio, periodo_fin):
        """
        Construye la lista de parámetros necesarios para la consulta de balance de 8 columnas
        
        Args:
            periodo_inicio (int): Período inicial en formato YYYYMM
            periodo_fin (int): Período final en formato YYYYMM
            
        Returns:
            list: Lista de parámetros en el orden correcto para la consulta SQL
        """
        return [
            # 1) DETALLE POR CUENTA
            periodo_inicio,  # SELECT DISTINCT cuenta FROM co_tgsaldos_mes WHERE mes < %s
            periodo_inicio, periodo_fin,  # SELECT DISTINCT cuenta FROM co_tgsaldos_mes WHERE mes BETWEEN %s AND %s
            periodo_inicio,  # WHERE mes < %s (subconsulta i)
            periodo_inicio, periodo_fin,  # WHERE mes BETWEEN %s AND %s (subconsulta m)
            
            # 2) SUMAS
            periodo_inicio,  # SELECT DISTINCT cuenta FROM co_tgsaldos_mes WHERE mes < %s
            periodo_inicio, periodo_fin,  # SELECT DISTINCT cuenta FROM co_tgsaldos_mes WHERE mes BETWEEN %s AND %s
            periodo_inicio,  # WHERE mes < %s (subconsulta i)
            periodo_inicio, periodo_fin,  # WHERE mes BETWEEN %s AND %s (subconsulta m)
            
            # 3) RESULTADO EJERCICIO - subconsulta tb (totales balance)
            periodo_inicio,  # SELECT DISTINCT cuenta FROM co_tgsaldos_mes WHERE mes < %s
            periodo_inicio, periodo_fin,  # SELECT DISTINCT cuenta FROM co_tgsaldos_mes WHERE mes BETWEEN %s AND %s
            periodo_inicio,  # WHERE mes < %s (subconsulta i)
            periodo_inicio, periodo_fin,  # WHERE mes BETWEEN %s AND %s (subconsulta m)
            
            # 3) RESULTADO EJERCICIO - subconsulta tp (totales PyG)
            periodo_inicio,  # SELECT DISTINCT cuenta FROM co_tgsaldos_mes WHERE mes < %s
            periodo_inicio, periodo_fin,  # SELECT DISTINCT cuenta FROM co_tgsaldos_mes WHERE mes BETWEEN %s AND %s
            periodo_inicio,  # WHERE mes < %s (subconsulta i)
            periodo_inicio, periodo_fin,  # WHERE mes BETWEEN %s AND %s (subconsulta m)
            
            # 4) SUMAS IGUALES
            periodo_inicio,  # SELECT DISTINCT cuenta FROM co_tgsaldos_mes WHERE mes < %s
            periodo_inicio, periodo_fin,  # SELECT DISTINCT cuenta FROM co_tgsaldos_mes WHERE mes BETWEEN %s AND %s
            periodo_inicio,  # WHERE mes < %s (subconsulta i)
            periodo_inicio, periodo_fin,  # WHERE mes BETWEEN %s AND %s (subconsulta m)
        ]


# Instancia global
balance_queries = BalanceQueries()