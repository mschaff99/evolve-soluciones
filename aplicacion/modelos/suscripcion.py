"""
Modelo de Suscripción para Evolve Soluciones SaaS
==================================================

Gestiona las suscripciones activas de los clientes/tenants.
"""

from typing import Optional, Dict, Any, List, cast
from datetime import datetime, timedelta
from aplicacion.modelos.base_datos import (
    ejecutar_consulta_postgres,
    ejecutar_insercion_postgres,
    ejecutar_actualizacion_postgres
)


class Suscripcion:
    """Modelo de suscripción de cliente"""

    def __init__(self, id, id_base_datos, id_plan, estado='activa',
                 periodo='mensual', fecha_inicio=None, fecha_vencimiento=None,
                 fecha_proximo_cobro=None, auto_renovacion=True,
                 metodo_pago=None, precio_actual=0, moneda='CLP',
                 en_periodo_prueba=False, fecha_fin_prueba=None,
                 cancelada_en=None, motivo_cancelacion=None,
                 metadata_json=None, fecha_creacion=None):
        self.id = id
        self.id_base_datos = id_base_datos
        self.id_plan = id_plan
        self.estado = estado
        self.periodo = periodo
        self.fecha_inicio = fecha_inicio
        self.fecha_vencimiento = fecha_vencimiento
        self.fecha_proximo_cobro = fecha_proximo_cobro
        self.auto_renovacion = auto_renovacion
        self.metodo_pago = metodo_pago
        self.precio_actual = precio_actual
        self.moneda = moneda
        self.en_periodo_prueba = en_periodo_prueba
        self.fecha_fin_prueba = fecha_fin_prueba
        self.cancelada_en = cancelada_en
        self.motivo_cancelacion = motivo_cancelacion
        self.metadata_json = metadata_json
        self.fecha_creacion = fecha_creacion

    def esta_activa(self):
        """Verifica si la suscripción está activa"""
        return self.estado == 'activa' and (
            self.fecha_vencimiento is None or 
            self.fecha_vencimiento > datetime.now()
        )

    def esta_en_prueba(self):
        """Verifica si está en período de prueba"""
        return (self.en_periodo_prueba and 
                self.fecha_fin_prueba and 
                self.fecha_fin_prueba > datetime.now())

    def dias_hasta_vencimiento(self):
        """Calcula días hasta el vencimiento"""
        if not self.fecha_vencimiento:
            return None
        delta = self.fecha_vencimiento - datetime.now()
        return max(0, delta.days)

    def requiere_renovacion(self):
        """Verifica si requiere renovación próximamente (menos de 7 días)"""
        dias = self.dias_hasta_vencimiento()
        return dias is not None and dias <= 7

    def to_dict(self):
        """
        Convierte la suscripción a diccionario

        Returns:
            dict: Datos de la suscripción
        """
        return {
            'id': self.id,
            'id_base_datos': self.id_base_datos,
            'id_plan': self.id_plan,
            'estado': self.estado,
            'periodo': self.periodo,
            'fecha_inicio': self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            'fecha_vencimiento': self.fecha_vencimiento.isoformat() if self.fecha_vencimiento else None,
            'fecha_proximo_cobro': self.fecha_proximo_cobro.isoformat() if self.fecha_proximo_cobro else None,
            'auto_renovacion': self.auto_renovacion,
            'metodo_pago': self.metodo_pago,
            'precio_actual': float(self.precio_actual),
            'moneda': self.moneda,
            'en_periodo_prueba': self.en_periodo_prueba,
            'fecha_fin_prueba': self.fecha_fin_prueba.isoformat() if self.fecha_fin_prueba else None,
            'cancelada_en': self.cancelada_en.isoformat() if self.cancelada_en else None,
            'motivo_cancelacion': self.motivo_cancelacion,
            'dias_hasta_vencimiento': self.dias_hasta_vencimiento(),
            'requiere_renovacion': self.requiere_renovacion(),
            'metadata': self.metadata_json,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }

    @staticmethod
    def obtener_por_id(id_suscripcion):
        """
        Obtiene una suscripción por su ID

        Args:
            id_suscripcion (int): ID de la suscripción

        Returns:
            Suscripcion|None: Instancia de la suscripción o None
        """
        try:
            consulta = """
                SELECT id, id_base_datos, id_plan, estado, periodo,
                       fecha_inicio, fecha_vencimiento, fecha_proximo_cobro,
                       auto_renovacion, metodo_pago, precio_actual, moneda,
                       en_periodo_prueba, fecha_fin_prueba, cancelada_en,
                       motivo_cancelacion, metadata_json, fecha_creacion
                FROM auth.suscripciones
                WHERE id = %s
            """
            resultado = cast(Optional[Dict[str, Any]], 
                           ejecutar_consulta_postgres(consulta, (id_suscripcion,), obtener_uno=True))

            if resultado:
                return Suscripcion(**resultado)
            return None
        except Exception as e:
            print(f"Error obteniendo suscripción por ID {id_suscripcion}: {e}")
            return None

    @staticmethod
    def obtener_por_base_datos(nombre_bd):
        """
        Obtiene la suscripción activa de una base de datos

        Args:
            nombre_bd (str): Nombre de la base de datos

        Returns:
            Suscripcion|None: Suscripción activa o None
        """
        try:
            consulta = """
                SELECT s.id, s.id_base_datos, s.id_plan, s.estado, s.periodo,
                       s.fecha_inicio, s.fecha_vencimiento, s.fecha_proximo_cobro,
                       s.auto_renovacion, s.metodo_pago, s.precio_actual, s.moneda,
                       s.en_periodo_prueba, s.fecha_fin_prueba, s.cancelada_en,
                       s.motivo_cancelacion, s.metadata_json, s.fecha_creacion
                FROM auth.suscripciones s
                INNER JOIN auth.bases_datos_mysql bd ON s.id_base_datos = bd.id
                WHERE bd.nombre_base_datos = %s 
                  AND s.estado IN ('activa', 'periodo_prueba')
                ORDER BY s.fecha_creacion DESC
                LIMIT 1
            """
            resultado = cast(Optional[Dict[str, Any]], 
                           ejecutar_consulta_postgres(consulta, (nombre_bd,), obtener_uno=True))

            if resultado:
                return Suscripcion(**resultado)
            return None
        except Exception as e:
            print(f"Error obteniendo suscripción para BD {nombre_bd}: {e}")
            return None

    @staticmethod
    def crear_suscripcion(id_base_datos, id_plan, periodo='mensual',
                         en_periodo_prueba=False, dias_prueba=14,
                         auto_renovacion=True, metodo_pago=None,
                         metadata_json=None):
        """
        Crea una nueva suscripción

        Args:
            id_base_datos (int): ID de la base de datos
            id_plan (int): ID del plan
            periodo (str): Período de facturación (mensual, anual)
            en_periodo_prueba (bool): Si está en período de prueba
            dias_prueba (int): Días de prueba
            auto_renovacion (bool): Si se renueva automáticamente
            metodo_pago (str): Método de pago
            metadata_json (dict): Metadata adicional

        Returns:
            Suscripcion|None: Instancia de la suscripción creada
        """
        try:
            from aplicacion.modelos.plan import Plan

            # Obtener información del plan
            plan = Plan.obtener_por_id(id_plan)
            if not plan:
                raise ValueError(f"Plan con ID {id_plan} no existe")

            # Calcular fechas
            fecha_inicio = datetime.now()
            
            if en_periodo_prueba:
                fecha_fin_prueba = fecha_inicio + timedelta(days=dias_prueba)
                fecha_vencimiento = fecha_fin_prueba
                estado = 'periodo_prueba'
                precio_actual = 0
            else:
                fecha_fin_prueba = None
                if periodo == 'mensual':
                    fecha_vencimiento = fecha_inicio + timedelta(days=30)
                    precio_actual = plan.precio_mensual
                else:  # anual
                    fecha_vencimiento = fecha_inicio + timedelta(days=365)
                    precio_actual = plan.precio_anual
                estado = 'activa'

            fecha_proximo_cobro = fecha_vencimiento if auto_renovacion else None

            # Insertar suscripción
            consulta = """
                INSERT INTO auth.suscripciones
                (id_base_datos, id_plan, estado, periodo, fecha_inicio,
                 fecha_vencimiento, fecha_proximo_cobro, auto_renovacion,
                 metodo_pago, precio_actual, moneda, en_periodo_prueba,
                 fecha_fin_prueba, metadata_json, fecha_creacion)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            id_suscripcion = ejecutar_insercion_postgres(
                consulta,
                (id_base_datos, id_plan, estado, periodo, fecha_inicio,
                 fecha_vencimiento, fecha_proximo_cobro, auto_renovacion,
                 metodo_pago, precio_actual, 'CLP', en_periodo_prueba,
                 fecha_fin_prueba, metadata_json, datetime.now())
            )

            return Suscripcion.obtener_por_id(id_suscripcion)

        except Exception as e:
            print(f"Error creando suscripción: {e}")
            raise

    @staticmethod
    def cambiar_plan(id_suscripcion, nuevo_id_plan, aplicar_inmediatamente=True):
        """
        Cambia el plan de una suscripción (upgrade/downgrade)

        Args:
            id_suscripcion (int): ID de la suscripción
            nuevo_id_plan (int): ID del nuevo plan
            aplicar_inmediatamente (bool): Si aplicar el cambio de inmediato

        Returns:
            bool: True si se cambió correctamente
        """
        try:
            from aplicacion.modelos.plan import Plan

            suscripcion = Suscripcion.obtener_por_id(id_suscripcion)
            if not suscripcion:
                return False

            nuevo_plan = Plan.obtener_por_id(nuevo_id_plan)
            if not nuevo_plan:
                return False

            if aplicar_inmediatamente:
                # Calcular nuevo precio según período
                if suscripcion.periodo == 'mensual':
                    nuevo_precio = nuevo_plan.precio_mensual
                else:
                    nuevo_precio = nuevo_plan.precio_anual

                consulta = """
                    UPDATE auth.suscripciones
                    SET id_plan = %s, precio_actual = %s
                    WHERE id = %s
                """
                ejecutar_actualizacion_postgres(
                    consulta, 
                    (nuevo_id_plan, nuevo_precio, id_suscripcion)
                )
            else:
                # Programar cambio para próxima renovación
                metadata = suscripcion.metadata_json or {}
                metadata['plan_siguiente'] = nuevo_id_plan
                
                consulta = """
                    UPDATE auth.suscripciones
                    SET metadata_json = %s
                    WHERE id = %s
                """
                ejecutar_actualizacion_postgres(
                    consulta, 
                    (metadata, id_suscripcion)
                )

            return True

        except Exception as e:
            print(f"Error cambiando plan de suscripción {id_suscripcion}: {e}")
            return False

    @staticmethod
    def cancelar_suscripcion(id_suscripcion, motivo=None, cancelar_inmediatamente=False):
        """
        Cancela una suscripción

        Args:
            id_suscripcion (int): ID de la suscripción
            motivo (str): Motivo de cancelación
            cancelar_inmediatamente (bool): Si cancelar de inmediato o al final del período

        Returns:
            bool: True si se canceló correctamente
        """
        try:
            if cancelar_inmediatamente:
                # Cancelación inmediata
                consulta = """
                    UPDATE auth.suscripciones
                    SET estado = 'cancelada',
                        auto_renovacion = FALSE,
                        cancelada_en = %s,
                        motivo_cancelacion = %s,
                        fecha_vencimiento = %s
                    WHERE id = %s
                """
                parametros = (datetime.now(), motivo, datetime.now(), id_suscripcion)
            else:
                # Cancelación al final del período
                consulta = """
                    UPDATE auth.suscripciones
                    SET estado = 'pendiente_cancelacion',
                        auto_renovacion = FALSE,
                        cancelada_en = %s,
                        motivo_cancelacion = %s
                    WHERE id = %s
                """
                parametros = (datetime.now(), motivo, id_suscripcion)

            filas_afectadas = ejecutar_actualizacion_postgres(consulta, parametros)
            return filas_afectadas > 0

        except Exception as e:
            print(f"Error cancelando suscripción {id_suscripcion}: {e}")
            return False

    @staticmethod
    def renovar_suscripcion(id_suscripcion):
        """
        Renueva una suscripción (llamado después de pago exitoso)

        Args:
            id_suscripcion (int): ID de la suscripción

        Returns:
            bool: True si se renovó correctamente
        """
        try:
            suscripcion = Suscripcion.obtener_por_id(id_suscripcion)
            if not suscripcion:
                return False

            # Calcular nueva fecha de vencimiento
            if suscripcion.periodo == 'mensual':
                nueva_fecha = datetime.now() + timedelta(days=30)
            else:
                nueva_fecha = datetime.now() + timedelta(days=365)

            consulta = """
                UPDATE auth.suscripciones
                SET fecha_vencimiento = %s,
                    fecha_proximo_cobro = %s,
                    en_periodo_prueba = FALSE,
                    estado = 'activa'
                WHERE id = %s
            """
            
            filas_afectadas = ejecutar_actualizacion_postgres(
                consulta,
                (nueva_fecha, nueva_fecha, id_suscripcion)
            )
            return filas_afectadas > 0

        except Exception as e:
            print(f"Error renovando suscripción {id_suscripcion}: {e}")
            return False

    @staticmethod
    def obtener_suscripciones_por_vencer(dias=7):
        """
        Obtiene suscripciones que vencen en los próximos N días

        Args:
            dias (int): Número de días a futuro

        Returns:
            list: Lista de suscripciones por vencer
        """
        try:
            fecha_limite = datetime.now() + timedelta(days=dias)
            
            consulta = """
                SELECT s.id, s.id_base_datos, s.id_plan, s.estado, s.periodo,
                       s.fecha_inicio, s.fecha_vencimiento, s.fecha_proximo_cobro,
                       s.auto_renovacion, s.metodo_pago, s.precio_actual, s.moneda,
                       s.en_periodo_prueba, s.fecha_fin_prueba, s.cancelada_en,
                       s.motivo_cancelacion, s.metadata_json, s.fecha_creacion
                FROM auth.suscripciones s
                WHERE s.estado = 'activa'
                  AND s.fecha_vencimiento BETWEEN %s AND %s
                  AND s.auto_renovacion = TRUE
                ORDER BY s.fecha_vencimiento ASC
            """
            
            resultados = cast(List[Dict[str, Any]], 
                            ejecutar_consulta_postgres(
                                consulta, 
                                (datetime.now(), fecha_limite)
                            ))

            suscripciones = []
            if resultados:
                for resultado in resultados:
                    suscripcion = Suscripcion(**resultado)
                    suscripciones.append(suscripcion)

            return suscripciones

        except Exception as e:
            print(f"Error obteniendo suscripciones por vencer: {e}")
            return []
