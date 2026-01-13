"""
Esquemas de Empresa
==================
Esquemas Marshmallow para serialización de empresas
"""
from marshmallow import Schema, fields


class EmpresaEsquema(Schema):
    """Esquema para serializar datos de empresa"""
    id = fields.Int(dump_only=True)
    rut = fields.Str(required=True, attribute='run_rut')
    nombre = fields.Str(required=True, attribute='empresa')
    razon_social = fields.Str(allow_none=True)
    giro = fields.Str(allow_none=True)
    auditor = fields.Str(allow_none=True)
    grupo = fields.Str(allow_none=True)
    activo = fields.Bool()
    
    # Campos calculados
    tiene_credencial_sii = fields.Bool(dump_only=True)
    estado_credencial = fields.Str(dump_only=True, allow_none=True)
