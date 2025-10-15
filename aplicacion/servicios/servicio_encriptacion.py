"""
Servicio de Encriptación para Credenciales SII
==============================================

Proporciona encriptación reversible usando Fernet (AES-128)
para permitir que scripts externos puedan desencriptar las contraseñas.
"""

import os
from cryptography.fernet import Fernet
from pathlib import Path


class ServicioEncriptacion:
    """Servicio para encriptar/desencriptar credenciales de forma reversible"""

    def __init__(self):
        """Inicializa el servicio con la clave de encriptación"""
        self.clave = self._obtener_o_crear_clave()
        self.cipher = Fernet(self.clave)

    def _obtener_o_crear_clave(self) -> bytes:
        """
        Obtiene la clave de encriptación desde archivo o la crea

        La clave se guarda en el directorio raíz del proyecto

        Returns:
            bytes: Clave de encriptación Fernet
        """
        # Ruta al archivo de clave (raíz del proyecto)
        ruta_proyecto = Path(__file__).parent.parent.parent
        archivo_clave = ruta_proyecto / '.encryption_key'

        # Si existe, leer la clave
        if archivo_clave.exists():
            with open(archivo_clave, 'rb') as f:
                return f.read()

        # Si no existe, crear nueva clave
        nueva_clave = Fernet.generate_key()

        # Guardar la clave
        with open(archivo_clave, 'wb') as f:
            f.write(nueva_clave)

        print(f" Clave de encriptación creada en: {archivo_clave}")
        print("⚠️  IMPORTANTE: Guarda este archivo de forma segura (backup)")
        print("⚠️  Añade '.encryption_key' a tu .gitignore")

        return nueva_clave

    def encriptar(self, texto_plano: str) -> str:
        """
        Encripta un texto usando Fernet

        Args:
            texto_plano (str): Texto a encriptar

        Returns:
            str: Texto encriptado en base64
        """
        if not texto_plano:
            raise ValueError("El texto a encriptar no puede estar vacío")

        # Encriptar
        texto_bytes = texto_plano.encode('utf-8')
        encriptado_bytes = self.cipher.encrypt(texto_bytes)

        # Convertir a string base64
        return encriptado_bytes.decode('utf-8')

    def desencriptar(self, texto_encriptado: str) -> str:
        """
        Desencripta un texto encriptado con Fernet

        Args:
            texto_encriptado (str): Texto encriptado en base64

        Returns:
            str: Texto desencriptado

        Raises:
            Exception: Si no se puede desencriptar (clave incorrecta o dato corrupto)
        """
        if not texto_encriptado:
            raise ValueError("El texto encriptado no puede estar vacío")

        try:
            # Convertir de string a bytes
            encriptado_bytes = texto_encriptado.encode('utf-8')

            # Desencriptar
            texto_bytes = self.cipher.decrypt(encriptado_bytes)

            # Convertir a string
            return texto_bytes.decode('utf-8')

        except Exception as e:
            raise Exception(f"Error al desencriptar: {e}")

    def es_texto_encriptado_fernet(self, texto: str) -> bool:
        """
        Verifica si un texto parece estar encriptado con Fernet

        Args:
            texto (str): Texto a verificar

        Returns:
            bool: True si parece ser Fernet, False si no
        """
        if not texto:
            return False

        # Los tokens Fernet empiezan con 'gAAAAA' después de base64
        try:
            # Intentar decodificar como Fernet
            return texto.startswith('gAAAAA') and len(texto) > 100
        except:
            return False

    def es_hash_bcrypt(self, texto: str) -> bool:
        """
        Verifica si un texto es un hash bcrypt

        Args:
            texto (str): Texto a verificar

        Returns:
            bool: True si es bcrypt, False si no
        """
        if not texto:
            return False

        return texto.startswith('$2a$') or texto.startswith('$2b$') or texto.startswith('$2y$')


# Instancia global del servicio
servicio_encriptacion = ServicioEncriptacion()
