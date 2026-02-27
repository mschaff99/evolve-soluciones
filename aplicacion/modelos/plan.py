"""
Modelo de Plan de Suscripción para Evolve Soluciones SaaS
==========================================================

Define los planes de suscripción disponibles y sus características.
"""

from typing import Optional, Dict, Any, List, cast
from datetime import datetime
from aplicacion.modelos.base_datos import (
    ejecutar_consulta_postgres,
    ejecutar_insercion_postgres,
    ejecutar_actualizacion_postgres
)


class Plan:
    """Modelo de plan de suscripción SaaS"""

    def __init__(self, id, codigo, nombre, descripcion=None, precio_mensual=0,
                 precio_anual=0, max_usuarios=1, max_empresas=None, 
                 max_transacciones_mes=None, almacenamiento_gb=None,
                 incluye_soporte=False, nivel_soporte='basico',
                 periodo_prueba_dias=0, destacado=False, activo=True,
                 configuracion_json=None, fecha_creacion=None):
        self.id = id
        self.codigo = codigo
        self.nombre = nombre
        self.descripcion = descripcion
        self.precio_mensual = precio_mensual
        self.precio_anual = precio_anual
        self.max_usuarios = max_usuarios
        self.max_empresas = max_empresas
        self.max_transacciones_mes = max_transacciones_mes
        self.almacenamiento_gb = almacenamiento_gb
        self.incluye_soporte = incluye_soporte
        self.nivel_soporte = nivel_soporte
        self.periodo_prueba_dias = periodo_prueba_dias
        self.destacado = destacado
        self.activo = activo
        self.configuracion_json = configuracion_json
        self.fecha_creacion = fecha_creacion

    def tiene_limite_usuarios(self):
        """Verifica si el plan tiene límite de usuarios"""
        return self.max_usuarios is not None and self.max_usuarios > 0

    def tiene_limite_empresas(self):
        """Verifica si el plan tiene límite de empresas"""
        return self.max_empresas is not None

    def tiene_periodo_prueba(self):
        """Verifica si el plan incluye período de prueba"""
        return self.periodo_prueba_dias > 0

    def calcular_ahorro_anual(self):
        """Calcula el ahorro en porcentaje del plan anual vs mensual"""
        if self.precio_mensual == 0 or self.precio_anual == 0:
            return 0
        costo_mensual_anualizado = self.precio_mensual * 12
        ahorro = costo_mensual_anualizado - self.precio_anual
        return round((ahorro / costo_mensual_anualizado) * 100, 1)

    def to_dict(self):
        """
        Convierte el plan a diccionario

        Returns:
            dict: Datos del plan
        """
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'precio_mensual': float(self.precio_mensual),
            'precio_anual': float(self.precio_anual),
            'max_usuarios': self.max_usuarios,
            'max_empresas': self.max_empresas,
            'max_transacciones_mes': self.max_transacciones_mes,
            'almacenamiento_gb': self.almacenamiento_gb,
            'incluye_soporte': self.incluye_soporte,
            'nivel_soporte': self.nivel_soporte,
            'periodo_prueba_dias': self.periodo_prueba_dias,
            'destacado': self.destacado,
            'activo': self.activo,
            'ahorro_anual': self.calcular_ahorro_anual(),
            'configuracion': self.configuracion_json,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }

    @staticmethod
    def obtener_por_id(id_plan):
        """
        Obtiene un plan por su ID

        Args:
            id_plan (int): ID del plan

        Returns:
            Plan|None: Instancia del plan o None si no existe
        """
        try:
            consulta = """
                SELECT id, codigo, nombre, descripcion, precio_mensual, precio_anual,
                       max_usuarios, max_empresas, max_transacciones_mes, almacenamiento_gb,
                       incluye_soporte, nivel_soporte, periodo_prueba_dias, destacado,
                       activo, configuracion_json, fecha_creacion
                FROM auth.planes_suscripcion
                WHERE id = %s
            """
            resultado = cast(Optional[Dict[str, Any]], 
                           ejecutar_consulta_postgres(consulta, (id_plan,), obtener_uno=True))

            if resultado:
                return Plan(**resultado)
            return None
        except Exception as e:
            print(f"Error obteniendo plan por ID {id_plan}: {e}")
            return None

    @staticmethod
    def obtener_por_codigo(codigo):
        """
        Obtiene un plan por su código

        Args:
            codigo (str): Código del plan

        Returns:
            Plan|None: Instancia del plan o None si no existe
        """
        try:
            consulta = """
                SELECT id, codigo, nombre, descripcion, precio_mensual, precio_anual,
                       max_usuarios, max_empresas, max_transacciones_mes, almacenamiento_gb,
                       incluye_soporte, nivel_soporte, periodo_prueba_dias, destacado,
                       activo, configuracion_json, fecha_creacion
                FROM auth.planes_suscripcion
                WHERE codigo = %s AND activo = TRUE
            """
            resultado = cast(Optional[Dict[str, Any]], 
                           ejecutar_consulta_postgres(consulta, (codigo,), obtener_uno=True))

            if resultado:
                return Plan(**resultado)
            return None
        except Exception as e:
            print(f"Error obteniendo plan por código {codigo}: {e}")
            return None

    @staticmethod
    def obtener_planes_activos(incluir_inactivos=False):
        """
        Obtiene todos los planes activos ordenados por precio

        Args:
            incluir_inactivos (bool): Si incluir planes inactivos

        Returns:
            list: Lista de instancias de Plan
        """
        try:
            if incluir_inactivos:
                consulta = """
                    SELECT id, codigo, nombre, descripcion, precio_mensual, precio_anual,
                           max_usuarios, max_empresas, max_transacciones_mes, almacenamiento_gb,
                           incluye_soporte, nivel_soporte, periodo_prueba_dias, destacado,
                           activo, configuracion_json, fecha_creacion
                    FROM auth.planes_suscripcion
                    ORDER BY precio_mensual ASC
                """
                parametros = ()
            else:
                consulta = """
                    SELECT id, codigo, nombre, descripcion, precio_mensual, precio_anual,
                           max_usuarios, max_empresas, max_transacciones_mes, almacenamiento_gb,
                           incluye_soporte, nivel_soporte, periodo_prueba_dias, destacado,
                           activo, configuracion_json, fecha_creacion
                    FROM auth.planes_suscripcion
                    WHERE activo = TRUE
                    ORDER BY precio_mensual ASC
                """
                parametros = ()

            resultados = cast(List[Dict[str, Any]], 
                            ejecutar_consulta_postgres(consulta, parametros))

            planes = []
            if resultados:
                for resultado in resultados:
                    plan = Plan(**resultado)
                    planes.append(plan)

            return planes
        except Exception as e:
            print(f"Error obteniendo planes activos: {e}")
            return []

    @staticmethod
    def obtener_modulos_plan(id_plan):
        """
        Obtiene los módulos incluidos en un plan

        Args:
            id_plan (int): ID del plan

        Returns:
            list: Lista de códigos de módulos incluidos
        """
        try:
            consulta = """
                SELECT m.codigo, m.nombre, m.descripcion, m.icono
                FROM auth.modulos_plan mp
                INNER JOIN auth.modulos_sistema m ON mp.id_modulo = m.id
                WHERE mp.id_plan = %s AND mp.incluido = TRUE
                ORDER BY m.orden_menu
            """
            resultados = cast(List[Dict[str, Any]], 
                            ejecutar_consulta_postgres(consulta, (id_plan,)))
            return resultados if resultados else []
        except Exception as e:
            print(f"Error obteniendo módulos del plan {id_plan}: {e}")
            return []

    @staticmethod
    def crear_plan(codigo, nombre, descripcion, precio_mensual=0, precio_anual=0,
                   max_usuarios=1, max_empresas=None, max_transacciones_mes=None,
                   almacenamiento_gb=None, incluye_soporte=False, nivel_soporte='basico',
                   periodo_prueba_dias=0, destacado=False, configuracion_json=None):
        """
        Crea un nuevo plan de suscripción

        Args:
            codigo (str): Código único del plan
            nombre (str): Nombre del plan
            descripcion (str): Descripción del plan
            precio_mensual (float): Precio mensual
            precio_anual (float): Precio anual
            max_usuarios (int): Máximo de usuarios permitidos
            max_empresas (int): Máximo de empresas permitidas
            max_transacciones_mes (int): Máximo de transacciones por mes
            almacenamiento_gb (int): Almacenamiento en GB
            incluye_soporte (bool): Si incluye soporte
            nivel_soporte (str): Nivel de soporte (basico, premium, enterprise)
            periodo_prueba_dias (int): Días de período de prueba
            destacado (bool): Si es el plan destacado
            configuracion_json (dict): Configuración adicional en JSON

        Returns:
            Plan|None: Instancia del plan creado o None si hubo error
        """
        try:
            # Verificar que no exista el código
            if Plan.obtener_por_codigo(codigo):
                raise ValueError(f"Ya existe un plan con el código '{codigo}'")

            # Insertar plan
            consulta = """
                INSERT INTO auth.planes_suscripcion
                (codigo, nombre, descripcion, precio_mensual, precio_anual,
                 max_usuarios, max_empresas, max_transacciones_mes, almacenamiento_gb,
                 incluye_soporte, nivel_soporte, periodo_prueba_dias, destacado,
                 activo, configuracion_json, fecha_creacion)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            id_plan = ejecutar_insercion_postgres(
                consulta,
                (codigo, nombre, descripcion, precio_mensual, precio_anual,
                 max_usuarios, max_empresas, max_transacciones_mes, almacenamiento_gb,
                 incluye_soporte, nivel_soporte, periodo_prueba_dias, destacado,
                 True, configuracion_json, datetime.now())
            )

            return Plan.obtener_por_id(id_plan)

        except Exception as e:
            print(f"Error creando plan: {e}")
            raise

    @staticmethod
    def actualizar_plan(id_plan, **kwargs):
        """
        Actualiza un plan existente

        Args:
            id_plan (int): ID del plan a actualizar
            **kwargs: Campos a actualizar

        Returns:
            bool: True si se actualizó correctamente
        """
        try:
            campos_permitidos = [
                'nombre', 'descripcion', 'precio_mensual', 'precio_anual',
                'max_usuarios', 'max_empresas', 'max_transacciones_mes',
                'almacenamiento_gb', 'incluye_soporte', 'nivel_soporte',
                'periodo_prueba_dias', 'destacado', 'activo', 'configuracion_json'
            ]

            campos_actualizar = []
            valores = []

            for campo, valor in kwargs.items():
                if campo in campos_permitidos:
                    campos_actualizar.append(f"{campo} = %s")
                    valores.append(valor)

            if not campos_actualizar:
                return False

            valores.append(id_plan)
            consulta = f"""
                UPDATE auth.planes_suscripcion
                SET {', '.join(campos_actualizar)}
                WHERE id = %s
            """

            filas_afectadas = ejecutar_actualizacion_postgres(consulta, tuple(valores))
            return filas_afectadas > 0

        except Exception as e:
            print(f"Error actualizando plan {id_plan}: {e}")
            return False
