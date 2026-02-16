from typing import Optional
from app.core.database import mysql_query
import json


async def get_situacion_tributaria(
    db_name: str,
    rut: str,
) -> Optional[dict]:
    row = await mysql_query(
        db_name,
        """
        SELECT * FROM situacion_tributaria WHERE rut = %s
        ORDER BY fecha_consulta DESC LIMIT 1
        """,
        (rut,),
        fetch_one=True,
    )
    if not row:
        return None

    datos_adicionales = {}
    for key, value in row.items():
        if key not in ("rut", "razon_social", "inicio_actividades", "estado_contribuyente"):
            if isinstance(value, str):
                try:
                    datos_adicionales[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    datos_adicionales[key] = value
            else:
                datos_adicionales[key] = value

    return {
        "rut": row.get("rut", rut),
        "razon_social": row.get("razon_social"),
        "inicio_actividades": str(row.get("inicio_actividades", "")),
        "estado_contribuyente": row.get("estado_contribuyente"),
        "actividades": [],
        "datos_adicionales": datos_adicionales,
    }


async def get_empresas_con_situacion(
    db_name: str,
    usuario_auditor: Optional[str] = None,
    busqueda: Optional[str] = None,
) -> list[dict]:
    conditions = []
    params = []

    if usuario_auditor:
        conditions.append("e.auditor = %s")
        params.append(usuario_auditor)
    if busqueda:
        conditions.append("(e.run_rut LIKE %s OR e.empresa LIKE %s)")
        params.extend([f"%{busqueda}%", f"%{busqueda}%"])

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    rows = await mysql_query(
        db_name,
        f"""
        SELECT e.run_rut, e.empresa, e.auditor, e.grupo,
               CASE WHEN st.rut IS NOT NULL THEN 1 ELSE 0 END as tiene_situacion
        FROM empresas e
        LEFT JOIN situacion_tributaria st ON e.run_rut = st.rut
        {where}
        GROUP BY e.run_rut, e.empresa, e.auditor, e.grupo, st.rut
        ORDER BY e.empresa
        """,
        tuple(params),
    )

    return [{
        "run_rut": r["run_rut"],
        "empresa": r.get("empresa"),
        "auditor": r.get("auditor"),
        "grupo": r.get("grupo"),
        "tiene_situacion": bool(r.get("tiene_situacion")),
    } for r in rows]
