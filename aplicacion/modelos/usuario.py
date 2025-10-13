"""
Modelo de Usuario para Evolve Soluciones
========================================

Define la clase Usuario y sus métodos para interactuar con la base de datos
PostgreSQL y manejar la autenticación y autorización.
"""

from typing import Optional, Dict, Any, List, cast
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from aplicacion.modelos.base_datos import (
    ejecutar_consulta_postgres,
    ejecutar_insercion_postgres,
    ejecutar_actualizacion_postgres
)


class Usuario(UserMixin):
    """Modelo de usuario para autenticación y autorización"""

    def __init__(self, id, nombre_usuario, email, hash_contraseña, rol='usuario',
                 base_datos_mysql=None, activo=True, fecha_creacion=None, fecha_ultimo_acceso=None):
        self.id = id
        self.nombre_usuario = nombre_usuario
        self.email = email
        self.hash_contraseña = hash_contraseña
        self.rol = rol
        # IMPORTANTE: Strip para limpiar espacios de campos CHAR en MySQL
        self.base_datos_mysql = base_datos_mysql.strip() if base_datos_mysql else None
        self.activo = activo
        self.fecha_creacion = fecha_creacion
        self.fecha_ultimo_acceso = fecha_ultimo_acceso

    def verificar_contraseña(self, contraseña):
        """
        Verifica si la contraseña proporcionada coincide con el hash almacenado

        Args:
            contraseña (str): Contraseña en texto plano

        Returns:
            bool: True si la contraseña es correcta
        """
        return check_password_hash(self.hash_contraseña, contraseña)

    def es_administrador(self):
        """
        Verifica si el usuario tiene rol de administrador

        Returns:
            bool: True si es administrador
        """
        return self.rol == 'administrador'

    def es_activo(self):
        """
        Verifica si el usuario está activo (requerido por Flask-Login)

        Returns:
            bool: True si está activo
        """
        return self.activo

    def actualizar_ultimo_acceso(self):
        """Actualiza la fecha de último acceso del usuario"""
        try:
            consulta = """
                UPDATE auth.usuarios
                SET fecha_ultimo_acceso = %s
                WHERE id = %s
            """
            ejecutar_actualizacion_postgres(consulta, (datetime.now(), self.id))
            self.fecha_ultimo_acceso = datetime.now()
        except Exception as e:
            print(f"Error actualizando ultimo acceso para usuario {self.id}: {e}")

    def cambiar_contraseña(self, nueva_contraseña):
        """
        Cambia la contraseña del usuario

        Args:
            nueva_contraseña (str): Nueva contraseña en texto plano
        """
        try:
            hash_nueva = generate_password_hash(nueva_contraseña)
            consulta = """
                UPDATE auth.usuarios
                SET hash_contraseña = %s
                WHERE id = %s
            """
            ejecutar_actualizacion_postgres(consulta, (hash_nueva, self.id))
            self.hash_contraseña = hash_nueva
        except Exception as e:
            print(f"Error cambiando contraseña para usuario {self.id}: {e}")
            raise

    def to_dict(self):
        """
        Convierte el usuario a diccionario (sin información sensible)

        Returns:
            dict: Datos del usuario
        """
        return {
            'id': self.id,
            'nombre_usuario': self.nombre_usuario,
            'email': self.email,
            'rol': self.rol,
            'base_datos_mysql': self.base_datos_mysql,
            'activo': self.activo,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_ultimo_acceso': self.fecha_ultimo_acceso.isoformat() if self.fecha_ultimo_acceso else None
        }

    @staticmethod
    def obtener_por_id(id_usuario):
        """
        Obtiene un usuario por su ID

        Args:
            id_usuario (int): ID del usuario

        Returns:
            Usuario|None: Instancia del usuario o None si no existe
        """
        try:
            consulta = """
                SELECT id, nombre_usuario, email, hash_contraseña, rol, base_datos_mysql, activo,
                       fecha_creacion, fecha_ultimo_acceso
                FROM auth.usuarios
                WHERE id = %s AND activo = TRUE
            """
            resultado = cast(Optional[Dict[str, Any]], ejecutar_consulta_postgres(consulta, (id_usuario,), obtener_uno=True))

            if resultado:
                return Usuario(
                    id=resultado['id'],
                    nombre_usuario=resultado['nombre_usuario'],
                    email=resultado['email'],
                    hash_contraseña=resultado['hash_contraseña'],
                    rol=resultado['rol'],
                    base_datos_mysql=resultado.get('base_datos_mysql'),
                    activo=resultado['activo'],
                    fecha_creacion=resultado['fecha_creacion'],
                    fecha_ultimo_acceso=resultado['fecha_ultimo_acceso']
                )
            return None
        except Exception as e:
            print(f"Error obteniendo usuario por ID {id_usuario}: {e}")
            return None

    @staticmethod
    def obtener_por_nombre_usuario(nombre_usuario):
        """
        Obtiene un usuario por su nombre de usuario

        Args:
            nombre_usuario (str): Nombre de usuario

        Returns:
            Usuario|None: Instancia del usuario o None si no existe
        """
        try:
            consulta = """
                SELECT id, nombre_usuario, email, hash_contraseña, rol, base_datos_mysql, activo,
                       fecha_creacion, fecha_ultimo_acceso
                FROM auth.usuarios
                WHERE nombre_usuario = %s
            """
            resultado = cast(Optional[Dict[str, Any]], ejecutar_consulta_postgres(consulta, (nombre_usuario,), obtener_uno=True))

            if resultado:
                return Usuario(
                    id=resultado['id'],
                    nombre_usuario=resultado['nombre_usuario'],
                    email=resultado['email'],
                    hash_contraseña=resultado['hash_contraseña'],
                    rol=resultado['rol'],
                    base_datos_mysql=resultado.get('base_datos_mysql'),
                    activo=resultado['activo'],
                    fecha_creacion=resultado['fecha_creacion'],
                    fecha_ultimo_acceso=resultado['fecha_ultimo_acceso']
                )
            return None
        except Exception as e:
            print(f"Error obteniendo usuario por nombre {nombre_usuario}: {e}")
            return None

    @staticmethod
    def obtener_por_email(email):
        """
        Obtiene un usuario por su email

        Args:
            email (str): Email del usuario

        Returns:
            Usuario|None: Instancia del usuario o None si no existe
        """
        try:
            consulta = """
                SELECT id, nombre_usuario, email, hash_contraseña, rol, base_datos_mysql, activo,
                       fecha_creacion, fecha_ultimo_acceso
                FROM auth.usuarios
                WHERE email = %s
            """
            resultado = cast(Optional[Dict[str, Any]], ejecutar_consulta_postgres(consulta, (email,), obtener_uno=True))

            if resultado:
                return Usuario(
                    id=resultado['id'],
                    nombre_usuario=resultado['nombre_usuario'],
                    email=resultado['email'],
                    hash_contraseña=resultado['hash_contraseña'],
                    rol=resultado['rol'],
                    base_datos_mysql=resultado.get('base_datos_mysql'),
                    activo=resultado['activo'],
                    fecha_creacion=resultado['fecha_creacion'],
                    fecha_ultimo_acceso=resultado['fecha_ultimo_acceso']
                )
            return None
        except Exception as e:
            print(f"Error obteniendo usuario por email {email}: {e}")
            return None

    @staticmethod
    def crear_usuario(nombre_usuario, email, contraseña, rol='usuario', base_datos_mysql='stratex'):
        """
        Crea un nuevo usuario en la base de datos

        Args:
            nombre_usuario (str): Nombre de usuario
            email (str): Email del usuario
            contraseña (str): Contraseña en texto plano
            rol (str): Rol del usuario ('usuario' o 'administrador')
            base_datos_mysql (str): Nombre de la base de datos MySQL asignada (default: 'stratex')

        Returns:
            Usuario|None: Instancia del usuario creado o None si hubo error
        """
        try:
            # Verificar que no exista el usuario o email
            if Usuario.obtener_por_nombre_usuario(nombre_usuario):
                raise ValueError(f"Ya existe un usuario con el nombre '{nombre_usuario}'")

            if Usuario.obtener_por_email(email):
                raise ValueError(f"Ya existe un usuario con el email '{email}'")

            # Generar hash de la contraseña
            hash_contraseña = generate_password_hash(contraseña)

            # Insertar usuario (PostgreSQL usa RETURNING para obtener el ID)
            consulta = """
                INSERT INTO auth.usuarios
                (nombre_usuario, email, hash_contraseña, rol, base_datos_mysql, activo, fecha_creacion)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            id_usuario = ejecutar_insercion_postgres(
                consulta,
                (nombre_usuario, email, hash_contraseña, rol, base_datos_mysql, True, datetime.now())
            )

            # Retornar instancia del usuario creado
            return Usuario.obtener_por_id(id_usuario)

        except Exception as e:
            print(f"Error creando usuario: {e}")
            raise

    @staticmethod
    def obtener_todos_usuarios():
        """
        Obtiene todos los usuarios activos

        Returns:
            list: Lista de instancias de Usuario
        """
        try:
            consulta = """
                SELECT id, nombre_usuario, email, hash_contraseña, rol, base_datos_mysql, activo,
                       fecha_creacion, fecha_ultimo_acceso
                FROM auth.usuarios
                WHERE activo = TRUE
                ORDER BY nombre_usuario
            """
            resultados = cast(List[Dict[str, Any]], ejecutar_consulta_postgres(consulta))

            usuarios = []
            if resultados:
                for resultado in resultados:
                    usuario = Usuario(
                        id=resultado['id'],
                        nombre_usuario=resultado['nombre_usuario'],
                        email=resultado['email'],
                        hash_contraseña=resultado['hash_contraseña'],
                        rol=resultado['rol'],
                        base_datos_mysql=resultado.get('base_datos_mysql'),
                        activo=resultado['activo'],
                        fecha_creacion=resultado['fecha_creacion'],
                        fecha_ultimo_acceso=resultado['fecha_ultimo_acceso']
                    )
                    usuarios.append(usuario)

            return usuarios
        except Exception as e:
            print(f"Error obteniendo todos los usuarios: {e}")
            return []

    @staticmethod
    def desactivar_usuario(id_usuario):
        """
        Desactiva un usuario (soft delete)

        Args:
            id_usuario (int): ID del usuario a desactivar

        Returns:
            bool: True si se desactivó correctamente
        """
        try:
            consulta = """
                UPDATE auth.usuarios
                SET activo = FALSE
                WHERE id = %s
            """
            filas_afectadas = ejecutar_actualizacion_postgres(consulta, (id_usuario,))
            return filas_afectadas > 0
        except Exception as e:
            print(f"Error desactivando usuario {id_usuario}: {e}")
            return False
