from typing import Optional
from app.core.database import mysql_query, mysql_execute


async def get_empresas(
    db_name: str,
    auditor: Optional[str] = None,
    grupo: Optional[str] = None,
    busqueda: Optional[str] = None,
    usuario_auditor: Optional[str] = None,
    pagina: int = 1,
    por_pagina: int = 50,
) -> dict:
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
    offset = (pagina - 1) * por_pagina

    count_sql = f"SELECT COUNT(*) as total FROM empresas e {where}"
    count_result = await mysql_query(db_name, count_sql, tuple(params), fetch_one=True)
    total = count_result["total"] if count_result else 0

    sql = f"""
        SELECT e.run_rut, e.empresa, e.auditor, e.grupo,
               CASE WHEN c.rut IS NOT NULL THEN 1 ELSE 0 END as tiene_credencial,
               c.rut as rut_credencial
        FROM empresas e
        LEFT JOIN credenciales_sii c ON e.run_rut = c.rut
        {where}
        ORDER BY e.empresa ASC
        LIMIT %s OFFSET %s
    """
    params.extend([por_pagina, offset])

    rows = await mysql_query(db_name, sql, tuple(params))

    empresas = []
    for r in rows:
        empresas.append({
            "run_rut": r["run_rut"],
            "empresa": r.get("empresa"),
            "auditor": r.get("auditor"),
            "grupo": r.get("grupo"),
            "tiene_credencial": bool(r.get("tiene_credencial")),
            "rut_credencial": r.get("rut_credencial"),
        })

    return {
        "empresas": empresas,
        "total": total,
        "pagina": pagina,
        "por_pagina": por_pagina,
        "total_paginas": (total + por_pagina - 1) // por_pagina if total else 0,
    }


async def get_empresa_by_rut(db_name: str, rut: str) -> Optional[dict]:
    row = await mysql_query(
        db_name,
        """
        SELECT e.run_rut, e.empresa, e.auditor, e.grupo,
               CASE WHEN c.rut IS NOT NULL THEN 1 ELSE 0 END as tiene_credencial,
               c.rut as rut_credencial
        FROM empresas e
        LEFT JOIN credenciales_sii c ON e.run_rut = c.rut
        WHERE e.run_rut = %s
        """,
        (rut,),
        fetch_one=True,
    )
    if not row:
        return None

    return {
        "run_rut": row["run_rut"],
        "empresa": row.get("empresa"),
        "auditor": row.get("auditor"),
        "grupo": row.get("grupo"),
        "tiene_credencial": bool(row.get("tiene_credencial")),
        "rut_credencial": row.get("rut_credencial"),
    }


async def create_empresa(db_name: str, data: dict) -> dict:
    await mysql_execute(
        db_name,
        "INSERT INTO empresas (run_rut, empresa, auditor, grupo) VALUES (%s, %s, %s, %s)",
        (data["run_rut"], data["empresa"], data.get("auditor"), data.get("grupo")),
    )
    return await get_empresa_by_rut(db_name, data["run_rut"])


async def update_empresa(db_name: str, rut: str, data: dict) -> Optional[dict]:
    sets = []
    params = []
    for field in ["empresa", "auditor", "grupo"]:
        if field in data and data[field] is not None:
            sets.append(f"{field} = %s")
            params.append(data[field])

    if not sets:
        return await get_empresa_by_rut(db_name, rut)

    params.append(rut)
    await mysql_execute(
        db_name,
        f"UPDATE empresas SET {', '.join(sets)} WHERE run_rut = %s",
        tuple(params),
    )
    return await get_empresa_by_rut(db_name, rut)


async def delete_empresa(db_name: str, rut: str) -> bool:
    await mysql_execute(db_name, "DELETE FROM empresas WHERE run_rut = %s", (rut,))
    return True


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
            COUNT(DISTINCT e.auditor) as total_auditores,
            COUNT(DISTINCT e.grupo) as total_grupos,
            SUM(CASE WHEN c.rut IS NOT NULL THEN 1 ELSE 0 END) as con_credencial,
            SUM(CASE WHEN c.rut IS NULL THEN 1 ELSE 0 END) as sin_credencial
        FROM empresas e
        LEFT JOIN credenciales_sii c ON e.run_rut = c.rut
        {auditor_filter}
        """,
        params,
        fetch_one=True,
    )
    return {
        "total_empresas": stats.get("total_empresas", 0) or 0,
        "total_auditores": stats.get("total_auditores", 0) or 0,
        "total_grupos": stats.get("total_grupos", 0) or 0,
        "con_credencial": stats.get("con_credencial", 0) or 0,
        "sin_credencial": stats.get("sin_credencial", 0) or 0,
    }


async def get_auditores(db_name: str) -> list[str]:
    rows = await mysql_query(
        db_name,
        "SELECT DISTINCT auditor FROM empresas WHERE auditor IS NOT NULL AND auditor != '' ORDER BY auditor",
    )
    return [r["auditor"] for r in rows]


async def get_grupos(db_name: str) -> list[str]:
    rows = await mysql_query(
        db_name,
        "SELECT DISTINCT grupo FROM empresas WHERE grupo IS NOT NULL AND grupo != '' ORDER BY grupo",
    )
    return [r["grupo"] for r in rows]
