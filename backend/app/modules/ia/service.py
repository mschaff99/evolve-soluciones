import logging
from typing import Optional, Any

from app.core.config import settings

logger = logging.getLogger("evolve.ia")


async def test_gemini_connection() -> dict:
    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        response = model.generate_content("Responde solo: OK")
        return {"exito": True, "mensaje": "Conexion exitosa", "respuesta": response.text}
    except Exception as e:
        logger.error("Error en test Gemini: %s", str(e))
        return {"exito": False, "mensaje": f"Error: {str(e)}"}


async def analizar_balance(datos_balance: dict[str, Any], tipo_analisis: str = "general") -> dict:
    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)

        prompt = f"""Eres un experto contador auditor chileno.
Analiza el siguiente balance de 8 columnas y proporciona un analisis {tipo_analisis}:

Datos del balance:
{datos_balance}

Proporciona:
1. Resumen ejecutivo
2. Indicadores financieros clave
3. Observaciones importantes
4. Recomendaciones

Responde en espanol chileno profesional."""

        response = model.generate_content(prompt)

        return {
            "exito": True,
            "mensaje": "Analisis completado",
            "analisis": response.text,
        }
    except Exception as e:
        logger.error("Error en analisis: %s", str(e))
        return {"exito": False, "mensaje": f"Error en analisis: {str(e)}"}


async def generar_balance(
    db_name: str,
    empresa_rut: str,
    anio_inicio: int,
    mes_inicio: int,
    anio_fin: int,
    mes_fin: int,
) -> dict:
    from app.core.database import mysql_query

    try:
        periodo_inicio = f"{anio_inicio}{mes_inicio:02d}"
        periodo_fin = f"{anio_fin}{mes_fin:02d}"

        datos = await mysql_query(
            db_name,
            """
            SELECT * FROM consulta_integral
            WHERE rut = %s AND periodo BETWEEN %s AND %s
            ORDER BY periodo
            """,
            (empresa_rut, periodo_inicio, periodo_fin),
        )

        if not datos:
            return {"exito": False, "mensaje": "No se encontraron datos para el periodo"}

        return {
            "exito": True,
            "mensaje": "Balance generado",
            "datos": {
                "rut": empresa_rut,
                "periodo_inicio": periodo_inicio,
                "periodo_fin": periodo_fin,
                "registros": len(datos),
                "detalle": [dict(d) for d in datos],
            },
        }
    except Exception as e:
        logger.error("Error generando balance: %s", str(e))
        return {"exito": False, "mensaje": f"Error: {str(e)}"}
