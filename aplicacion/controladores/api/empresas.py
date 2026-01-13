"""
Controlador de Empresas API
===========================
Endpoints de empresas para frontend React
"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from aplicacion.controladores.api import api_v1
from aplicacion.esquemas.empresa_esquema import EmpresaEsquema
from aplicacion.servicios.servicio_empresas import ServicioEmpresas
from aplicacion.modelos.usuario import Usuario


@api_v1.route('/empresas', methods=['GET'])
@jwt_required()
def listar_empresas():
    """
    Lista todas las empresas
    
    GET /api/v1/empresas?base_datos=stratex&buscar=texto
    Headers: Authorization: Bearer <token>
    
    Query params:
        - base_datos: Base de datos a consultar (default: stratex)
        - buscar: Texto de búsqueda (opcional)
        - usuario_filtro: Filtrar por auditor (opcional)
        - grupo_filtro: Filtrar por grupo (opcional)
    
    Returns:
        JSON con lista de empresas
    """
    try:
        # Obtener parámetros de consulta
        base_datos = request.args.get('base_datos', 'stratex')
        buscar = request.args.get('buscar')
        usuario_filtro = request.args.get('usuario_filtro')
        grupo_filtro = request.args.get('grupo_filtro')
        
        # Crear servicio
        servicio = ServicioEmpresas(base_datos=base_datos)
        
        # Preparar filtros
        filtros = {}
        if buscar:
            filtros['buscar'] = buscar
        if usuario_filtro:
            filtros['usuario_filtro'] = usuario_filtro
        if grupo_filtro:
            filtros['grupo_filtro'] = grupo_filtro
        
        # Obtener empresas
        empresas = servicio.obtener_todas_empresas_con_credenciales(filtros)
        
        # Agregar campo calculado de tiene_credencial_sii
        for empresa in empresas:
            empresa['tiene_credencial_sii'] = empresa.get('clave_sii') is not None
        
        # Serializar
        esquema = EmpresaEsquema(many=True)
        
        return jsonify({
            "empresas": esquema.dump(empresas),
            "total": len(empresas)
        }), 200
        
    except Exception as e:
        print(f"Error listando empresas: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Error interno del servidor"}), 500


@api_v1.route('/empresas/<rut>', methods=['GET'])
@jwt_required()
def obtener_empresa(rut):
    """
    Obtiene una empresa por RUT
    
    GET /api/v1/empresas/<rut>?base_datos=stratex
    Headers: Authorization: Bearer <token>
    
    Returns:
        JSON con datos de la empresa
    """
    try:
        base_datos = request.args.get('base_datos', 'stratex')
        
        servicio = ServicioEmpresas(base_datos=base_datos)
        empresa = servicio.obtener_empresa_por_rut(rut)
        
        if not empresa:
            return jsonify({"error": "Empresa no encontrada"}), 404
        
        # Agregar campo calculado
        empresa['tiene_credencial_sii'] = empresa.get('clave_sii') is not None
        
        esquema = EmpresaEsquema()
        return jsonify(esquema.dump(empresa)), 200
        
    except Exception as e:
        print(f"Error obteniendo empresa {rut}: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500


@api_v1.route('/empresas/estadisticas', methods=['GET'])
@jwt_required()
def obtener_estadisticas_empresas():
    """
    Obtiene estadísticas de empresas
    
    GET /api/v1/empresas/estadisticas?base_datos=stratex
    Headers: Authorization: Bearer <token>
    
    Returns:
        JSON con estadísticas
    """
    try:
        base_datos = request.args.get('base_datos', 'stratex')
        servicio = ServicioEmpresas(base_datos=base_datos)
        
        estadisticas = servicio.obtener_estadisticas()
        
        return jsonify(estadisticas), 200
        
    except Exception as e:
        print(f"Error obteniendo estadísticas: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500
