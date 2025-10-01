"""
Modelo de Sesión de Usuario para Evolve Soluciones
==================================================

Maneja las sesiones de usuarios en PostgreSQL, incluyendo creación, 
actualización y limpieza de sesiones expiradas.
"""

import secrets
from datetime import datetime, timedelta
from aplicacion.modelos.base_datos import (
    ejecutar_consulta_postgres, 
    ejecutar_insercion_postgres, 
    ejecutar_actualizacion_postgres
)


class SesionUsuario:
    """Modelo para manejar sesiones de usuarios"""
    
    def __init__(self, id, token_sesion, id_usuario, direccion_ip, user_agent, 
                 fecha_creacion, fecha_ultima_actividad, activa=True):
        self.id = id
        self.token_sesion = token_sesion
        self.id_usuario = id_usuario
        self.direccion_ip = direccion_ip
        self.user_agent = user_agent
        self.fecha_creacion = fecha_creacion
        self.fecha_ultima_actividad = fecha_ultima_actividad
        self.activa = activa
    
    def actualizar_actividad(self):
        """Actualiza la fecha de última actividad de la sesión"""
        try:
            consulta = """
                UPDATE auth.sesiones_usuario 
                SET fecha_ultima_actividad = %s 
                WHERE token_sesion = %s
            """
            ejecutar_actualizacion_postgres(consulta, (datetime.now(), self.token_sesion))
            self.fecha_ultima_actividad = datetime.now()
        except Exception as e:
            print(f"Error actualizando actividad de sesion {self.token_sesion}: {e}")
    
    def cerrar_sesion(self):
        """Marca la sesión como inactiva"""
        try:
            consulta = """
                UPDATE auth.sesiones_usuario 
                SET activa = FALSE 
                WHERE token_sesion = %s
            """
            ejecutar_actualizacion_postgres(consulta, (self.token_sesion,))
            self.activa = False
        except Exception as e:
            print(f"Error cerrando sesion {self.token_sesion}: {e}")
    
    def esta_expirada(self, minutos_expiracion=1440):  # 24 horas por defecto
        """
        Verifica si la sesión ha expirado
        
        Args:
            minutos_expiracion (int): Minutos después de los cuales la sesión expira
            
        Returns:
            bool: True si la sesión ha expirado
        """
        if not self.fecha_ultima_actividad:
            return True
        
        tiempo_expiracion = datetime.now() - timedelta(minutes=minutos_expiracion)
        return self.fecha_ultima_actividad < tiempo_expiracion
    
    def to_dict(self):
        """
        Convierte la sesión a diccionario
        
        Returns:
            dict: Datos de la sesión
        """
        return {
            'id': self.id,
            'token_sesion': self.token_sesion,
            'id_usuario': self.id_usuario,
            'direccion_ip': self.direccion_ip,
            'user_agent': self.user_agent,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_ultima_actividad': self.fecha_ultima_actividad.isoformat() if self.fecha_ultima_actividad else None,
            'activa': self.activa
        }
    
    @staticmethod
    def crear_sesion(id_usuario, direccion_ip, user_agent):
        """
        Crea una nueva sesión para un usuario
        
        Args:
            id_usuario (int): ID del usuario
            direccion_ip (str): Dirección IP del usuario
            user_agent (str): User agent del navegador
            
        Returns:
            SesionUsuario: Nueva instancia de sesión
        """
        try:
            # Generar token único para la sesión
            token_sesion = secrets.token_urlsafe(32)
            
            # Insertar nueva sesión (PostgreSQL usa RETURNING)
            consulta = """
                INSERT INTO auth.sesiones_usuario 
                (token_sesion, id_usuario, direccion_ip, user_agent, fecha_creacion, fecha_ultima_actividad, activa)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            fecha_actual = datetime.now()
            id_sesion = ejecutar_insercion_postgres(
                consulta,
                (token_sesion, id_usuario, direccion_ip, user_agent, fecha_actual, fecha_actual, True)
            )
            
            # Retornar instancia de la sesión creada
            return SesionUsuario(
                id=id_sesion,
                token_sesion=token_sesion,
                id_usuario=id_usuario,
                direccion_ip=direccion_ip,
                user_agent=user_agent,
                fecha_creacion=fecha_actual,
                fecha_ultima_actividad=fecha_actual,
                activa=True
            )
            
        except Exception as e:
            print(f"Error creando sesion para usuario {id_usuario}: {e}")
            raise
    
    @staticmethod
    def obtener_por_token(token_sesion):
        """
        Obtiene una sesión por su token
        
        Args:
            token_sesion (str): Token de la sesión
            
        Returns:
            SesionUsuario|None: Instancia de la sesión o None si no existe
        """
        try:
            consulta = """
                SELECT id, token_sesion, id_usuario, direccion_ip, user_agent,
                       fecha_creacion, fecha_ultima_actividad, activa
                FROM auth.sesiones_usuario 
                WHERE token_sesion = %s AND activa = TRUE
            """
            resultado = ejecutar_consulta_postgres(consulta, (token_sesion,), obtener_uno=True)
            
            if resultado:
                return SesionUsuario(
                    id=resultado['id'],
                    token_sesion=resultado['token_sesion'],
                    id_usuario=resultado['id_usuario'],
                    direccion_ip=resultado['direccion_ip'],
                    user_agent=resultado['user_agent'],
                    fecha_creacion=resultado['fecha_creacion'],
                    fecha_ultima_actividad=resultado['fecha_ultima_actividad'],
                    activa=resultado['activa']
                )
            return None
        except Exception as e:
            print(f"Error obteniendo sesion por token {token_sesion}: {e}")
            return None
    
    @staticmethod
    def obtener_sesiones_usuario(id_usuario, solo_activas=True):
        """
        Obtiene todas las sesiones de un usuario
        
        Args:
            id_usuario (int): ID del usuario
            solo_activas (bool): Si obtener solo sesiones activas
            
        Returns:
            list: Lista de instancias de SesionUsuario
        """
        try:
            consulta = """
                SELECT id, token_sesion, id_usuario, direccion_ip, user_agent,
                       fecha_creacion, fecha_ultima_actividad, activa
                FROM auth.sesiones_usuario 
                WHERE id_usuario = %s
            """
            
            if solo_activas:
                consulta += " AND activa = TRUE"
            
            consulta += " ORDER BY fecha_ultima_actividad DESC"
            
            resultados = ejecutar_consulta_postgres(consulta, (id_usuario,))
            
            sesiones = []
            for resultado in resultados:
                sesion = SesionUsuario(
                    id=resultado['id'],
                    token_sesion=resultado['token_sesion'],
                    id_usuario=resultado['id_usuario'],
                    direccion_ip=resultado['direccion_ip'],
                    user_agent=resultado['user_agent'],
                    fecha_creacion=resultado['fecha_creacion'],
                    fecha_ultima_actividad=resultado['fecha_ultima_actividad'],
                    activa=resultado['activa']
                )
                sesiones.append(sesion)
            
            return sesiones
        except Exception as e:
            print(f"Error obteniendo sesiones del usuario {id_usuario}: {e}")
            return []
    
    @staticmethod
    def actualizar_sesion(token_sesion):
        """
        Actualiza la fecha de última actividad de una sesión
        
        Args:
            token_sesion (str): Token de la sesión
        """
        try:
            consulta = """
                UPDATE auth.sesiones_usuario 
                SET fecha_ultima_actividad = %s 
                WHERE token_sesion = %s AND activa = TRUE
            """
            ejecutar_actualizacion_postgres(consulta, (datetime.now(), token_sesion))
        except Exception as e:
            print(f"Error actualizando sesion {token_sesion}: {e}")
    
    @staticmethod
    def cerrar_todas_sesiones_usuario(id_usuario, excepto_token=None):
        """
        Cierra todas las sesiones de un usuario (útil al cambiar contraseña)
        
        Args:
            id_usuario (int): ID del usuario
            excepto_token (str): Token de sesión a mantener activa
        """
        try:
            consulta = """
                UPDATE auth.sesiones_usuario 
                SET activa = FALSE 
                WHERE id_usuario = %s AND activa = TRUE
            """
            parametros = [id_usuario]
            
            if excepto_token:
                consulta += " AND token_sesion != %s"
                parametros.append(excepto_token)
            
            ejecutar_actualizacion_postgres(consulta, tuple(parametros))
        except Exception as e:
            print(f"Error cerrando sesiones del usuario {id_usuario}: {e}")
    
    @staticmethod
    def limpiar_sesiones_expiradas(minutos_expiracion=1440):
        """
        Limpia sesiones expiradas de la base de datos
        
        Args:
            minutos_expiracion (int): Minutos después de los cuales una sesión expira
            
        Returns:
            int: Número de sesiones limpiadas
        """
        try:
            fecha_limite = datetime.now() - timedelta(minutes=minutos_expiracion)
            
            consulta = """
                UPDATE auth.sesiones_usuario 
                SET activa = FALSE 
                WHERE fecha_ultima_actividad < %s AND activa = TRUE
            """
            filas_afectadas = ejecutar_actualizacion_postgres(consulta, (fecha_limite,))
            
            if filas_afectadas > 0:
                print(f"Sesiones expiradas limpiadas: {filas_afectadas}")
            
            return filas_afectadas
        except Exception as e:
            print(f"Error limpiando sesiones expiradas: {e}")
            return 0
    
    @staticmethod
    def registrar_intento_login(nombre_usuario, direccion_ip, exitoso, mensaje=None):
        """
        Registra un intento de inicio de sesión para auditoría
        
        Args:
            nombre_usuario (str): Nombre de usuario que intentó iniciar sesión
            direccion_ip (str): IP desde donde se intentó
            exitoso (bool): Si el intento fue exitoso
            mensaje (str): Mensaje adicional del intento
        """
        try:
            consulta = """
                INSERT INTO auth.intentos_login 
                (nombre_usuario, direccion_ip, exitoso, fecha_intento, mensaje)
                VALUES (%s, %s, %s, %s, %s)
            """
            ejecutar_insercion_postgres(
                consulta,
                (nombre_usuario, direccion_ip, exitoso, datetime.now(), mensaje)
            )
        except Exception as e:
            print(f"Error registrando intento de login: {e}")