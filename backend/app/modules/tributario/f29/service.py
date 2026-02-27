from typing import Optional
from app.core.database import mysql_query


def limpiar_rut(rut: str) -> str:
    return rut.replace(".", "").replace("-", "").strip()


async def get_empresas_con_periodos(
    db_name: str,
    auditor: Optional[str] = None,
    grupo: Optional[str] = None,
    busqueda: Optional[str] = None,
    usuario_auditor: Optional[str] = None,
) -> list[dict]:
    conditions = []
    params = []

    if auditor:
        conditions.append("e.auditor = %s")
        params.append(auditor)
    if grupo:
        conditions.append("e.grupo = %s")
        params.append(grupo)
    if busqueda:
        conditions.append("(e.run_rut LIKE %s OR e.empresa LIKE %s)")
        params.extend([f"%{busqueda}%", f"%{busqueda}%"])
    if usuario_auditor:
        conditions.append("e.auditor = %s")
        params.append(usuario_auditor)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    rows = await mysql_query(
        db_name,
        f"""
        SELECT e.run_rut, e.empresa, e.auditor, e.grupo,
               GROUP_CONCAT(DISTINCT ci.periodo ORDER BY ci.periodo DESC) as periodos,
               COUNT(DISTINCT ci.periodo) as total_periodos
        FROM empresas e
        LEFT JOIN consulta_integral ci ON e.run_rut = ci.rut
        {where}
        GROUP BY e.run_rut, e.empresa, e.auditor, e.grupo
        ORDER BY e.empresa
        """,
        tuple(params),
    )

    result = []
    for r in rows:
        periodos_str = r.get("periodos") or ""
        periodos = periodos_str.split(",") if periodos_str else []
        result.append({
            "run_rut": r["run_rut"],
            "empresa": r.get("empresa"),
            "auditor": r.get("auditor"),
            "grupo": r.get("grupo"),
            "periodos": periodos,
            "ultimo_periodo": periodos[0] if periodos else None,
            "total_periodos": r.get("total_periodos", 0),
        })
    return result


async def get_datos_f29(db_name: str, rut: str, periodo: str) -> Optional[dict]:
    row = await mysql_query(
        db_name,
        "SELECT rut, periodo, tabla_resultados FROM consulta_integral WHERE rut = %s AND periodo = %s",
        (limpiar_rut(rut), periodo),
        fetch_one=True,
    )
    if not row:
        return None

    import json
    datos = {}
    tabla = row.get("tabla_resultados")
    if tabla:
        try:
            datos = json.loads(tabla) if isinstance(tabla, str) else tabla
        except (json.JSONDecodeError, TypeError):
            datos = {"raw": str(tabla)}

    return {
        "rut": row["rut"],
        "periodo": row["periodo"],
        "datos": datos,
        "tabla_resultados": row.get("tabla_resultados"),
    }


async def get_observaciones(db_name: str, rut: str, periodo: str) -> list[dict]:
    rows = await mysql_query(
        db_name,
        """
        SELECT id, rut, periodo, observacion, estado, fecha
        FROM observaciones_f29
        WHERE rut = %s AND periodo = %s
        ORDER BY fecha DESC
        """,
        (limpiar_rut(rut), periodo),
    )
    return [dict(r) for r in rows]


async def get_estadisticas(db_name: str, usuario_auditor: Optional[str] = None) -> dict:
    auditor_filter = ""
    params = ()
    if usuario_auditor:
        auditor_filter = "WHERE e.auditor = %s"
        params = (usuario_auditor,)

    stats = await mysql_query(
        db_name,
        f"""
        SELECT
            COUNT(DISTINCT e.run_rut) as total_empresas,
            COUNT(DISTINCT ci.periodo) as total_periodos,
            SUM(CASE WHEN ci.tabla_resultados IS NOT NULL THEN 1 ELSE 0 END) as con_datos,
            SUM(CASE WHEN ci.tabla_resultados IS NULL THEN 1 ELSE 0 END) as sin_datos
        FROM empresas e
        LEFT JOIN consulta_integral ci ON e.run_rut = ci.rut
        {auditor_filter}
        """,
        params,
        fetch_one=True,
    )
    return {
        "total_empresas": stats.get("total_empresas", 0) or 0,
        "total_periodos": stats.get("total_periodos", 0) or 0,
        "con_observaciones": stats.get("con_datos", 0) or 0,
        "sin_observaciones": stats.get("sin_datos", 0) or 0,
    }


async def get_periodos_disponibles(db_name: str) -> list[str]:
    rows = await mysql_query(
        db_name,
        "SELECT DISTINCT periodo FROM consulta_integral ORDER BY periodo DESC",
    )
    return [r["periodo"] for r in rows]
