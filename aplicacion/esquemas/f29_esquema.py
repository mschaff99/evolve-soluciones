"""
Esquemas de F29
==============
Esquemas Marshmallow para serialización de datos F29
"""
from marshmallow import Schema, fields


class PeriodoF29Esquema(Schema):
    """Esquema para serializar datos de períodos F29"""
    id = fields.Int(dump_only=True)
    rut_empresa = fields.Str(required=True, attribute='rut')
    anio = fields.Int(required=True)
    mes = fields.Int(required=True)
    periodo = fields.Str(dump_only=True)
    estado = fields.Str()
    fecha_proceso = fields.DateTime(dump_only=True, allow_none=True)
    
    # Campos de observaciones
    tiene_observaciones = fields.Bool(dump_only=True, missing=False)
    total_observaciones = fields.Int(dump_only=True, missing=0)
    codigos_observaciones = fields.Str(dump_only=True, allow_none=True)
