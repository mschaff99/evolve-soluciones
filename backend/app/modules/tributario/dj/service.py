from typing import Optional
from app.core.database import mysql_query


async def get_empresas_con_dj(
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
               COUNT(dj.id) as total_dj
        FROM empresas e
        LEFT JOIN declaraciones_juradas dj ON e.run_rut = dj.rut
        {where}
        GROUP BY e.run_rut, e.empresa, e.auditor, e.grupo
        ORDER BY e.empresa
        """,
        tuple(params),
    )

    return [{
        "run_rut": r["run_rut"],
        "empresa": r.get("empresa"),
        "auditor": r.get("auditor"),
        "grupo": r.get("grupo"),
        "total_dj": r.get("total_dj", 0),
    } for r in rows]


async def get_dj_por_rut(db_name: str, rut: str) -> list[dict]:
    rows = await mysql_query(
        db_name,
        """
        SELECT dj.*, e.empresa
        FROM declaraciones_juradas dj
        LEFT JOIN empresas e ON dj.rut = e.run_rut
        WHERE dj.rut = %s
        ORDER BY dj.periodo DESC
        """,
        (rut,),
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
            COUNT(dj.id) as total_declaraciones
        FROM empresas e
        LEFT JOIN declaraciones_juradas dj ON e.run_rut = dj.rut
        {auditor_filter}
        """,
        params,
        fetch_one=True,
    )
    return {
        "total_empresas": stats.get("total_empresas", 0) or 0,
        "total_declaraciones": stats.get("total_declaraciones", 0) or 0,
        "presentadas": 0,
        "pendientes": 0,
    }
