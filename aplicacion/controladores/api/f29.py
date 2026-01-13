"""
Controlador de F29 API
=====================
Endpoints de consulta integral F29 para frontend React
"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from aplicacion.controladores.api import api_v1
from aplicacion.servicios.servicio_consulta_integral import ServicioConsultaIntegral
from aplicacion.modelos.usuario import Usuario


@api_v1.route('/f29', methods=['GET'])
@jwt_required()
def listar_empresas_f29():
    """
    Lista empresas con sus datos F29
    
    GET /api/v1/f29?base_datos=stratex&anio=2024
    Headers: Authorization: Bearer <token>
    
    Query params:
        - base_datos: Base de datos a consultar (default: stratex)
        - anio: Año a consultar (default: año actual)
    
    Returns:
        JSON con lista de empresas y sus períodos F29
    """
    try:
        # Obtener parámetros
        base_datos = request.args.get('base_datos', 'stratex')
        anio = request.args.get('anio', datetime.now().year, type=int)
        
        # Crear servicio
        servicio = ServicioConsultaIntegral(base_datos=base_datos)
        
        # Obtener datos
        # Nota: Este método debe implementarse en ServicioConsultaIntegral
        # Por ahora, retornamos estructura básica
        try:
            resultado = servicio.obtener_datos_empresas_con_periodos({
                'anio': anio
            })
        except AttributeError:
            # Si el método no existe, usar estructura alternativa
            print("Advertencia: Método obtener_datos_empresas_con_periodos no implementado")
            resultado = []
        
        return jsonify({
            "empresas": resultado,
            "anio": anio,
            "base_datos": base_datos
        }), 200
        
    except Exception as e:
        print(f"Error listando F29: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Error interno del servidor"}), 500


@api_v1.route('/f29/<rut>', methods=['GET'])
@jwt_required()
def obtener_f29_empresa(rut):
    """
    Obtiene datos F29 de una empresa específica
    
    GET /api/v1/f29/<rut>?base_datos=stratex&anio=2024
    Headers: Authorization: Bearer <token>
    
    Returns:
        JSON con datos F29 de la empresa
    """
    try:
        base_datos = request.args.get('base_datos', 'stratex')
        anio = request.args.get('anio', datetime.now().year, type=int)
        
        servicio = ServicioConsultaIntegral(base_datos=base_datos)
        
        # Obtener datos de la empresa
        datos = servicio.obtener_datos_empresas_con_periodos({
            'rut_filtro': rut,
            'anio': anio
        })
        
        if not datos:
            return jsonify({"error": "Empresa no encontrada"}), 404
        
        return jsonify({
            "rut": rut,
            "anio": anio,
            "datos": datos[0] if datos else {}
        }), 200
        
    except Exception as e:
        print(f"Error obteniendo F29 de empresa {rut}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Error interno del servidor"}), 500


@api_v1.route('/f29/<rut>/periodos', methods=['GET'])
@jwt_required()
def obtener_periodos_f29(rut):
    """
    Obtiene períodos F29 de una empresa
    
    GET /api/v1/f29/<rut>/periodos?base_datos=stratex&anio=2024
    Headers: Authorization: Bearer <token>
    
    Returns:
        JSON con períodos F29 de la empresa
    """
    try:
        base_datos = request.args.get('base_datos', 'stratex')
        anio = request.args.get('anio', datetime.now().year, type=int)
        
        servicio = ServicioConsultaIntegral(base_datos=base_datos)
        
        # Obtener períodos
        # Este es un placeholder - debe implementarse en el servicio
        periodos = []
        
        return jsonify({
            "rut": rut,
            "anio": anio,
            "periodos": periodos
        }), 200
        
    except Exception as e:
        print(f"Error obteniendo períodos F29: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500
