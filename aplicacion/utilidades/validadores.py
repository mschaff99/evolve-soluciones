"""
Validadores para Evolve Soluciones
==================================

Contiene funciones de validación para diferentes tipos de datos
utilizados en la aplicación.
"""

import re
from email.utils import parseaddr


def validar_email(email):
    """
    Valida el formato de un email
    
    Args:
        email (str): Email a validar
        
    Returns:
        bool: True si el email es válido
    """
    if not email or not isinstance(email, str):
        return False
    
    # Usar parseaddr para una validación básica
    parsed = parseaddr(email)
    if not parsed[1]:
        return False
    
    # Validación adicional con regex
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(patron, email))


def validar_contraseña(contraseña):
    """
    Valida que una contraseña cumpla con los requisitos de seguridad
    
    Args:
        contraseña (str): Contraseña a validar
        
    Returns:
        bool: True si la contraseña es válida
    """
    if not contraseña or not isinstance(contraseña, str):
        return False
    
    # Mínimo 8 caracteres
    if len(contraseña) < 8:
        return False
    
    # Al menos una mayúscula
    if not re.search(r'[A-Z]', contraseña):
        return False
    
    # Al menos una minúscula
    if not re.search(r'[a-z]', contraseña):
        return False
    
    # Al menos un número
    if not re.search(r'\d', contraseña):
        return False
    
    return True


def validar_rut_chileno(rut):
    """
    Valida un RUT chileno
    
    Args:
        rut (str): RUT a validar (puede incluir puntos y guión)
        
    Returns:
        bool: True si el RUT es válido
    """
    if not rut or not isinstance(rut, str):
        return False
    
    # Limpiar RUT (remover puntos y guiones)
    rut_limpio = re.sub(r'[.\-]', '', rut.strip().upper())
    
    # Verificar formato básico
    if not re.match(r'^\d{7,8}[0-9K]$', rut_limpio):
        return False
    
    # Separar número y dígito verificador
    numero = rut_limpio[:-1]
    dv = rut_limpio[-1]
    
    # Calcular dígito verificador
    suma = 0
    multiplicador = 2
    
    for digito in reversed(numero):
        suma += int(digito) * multiplicador
        multiplicador += 1
        if multiplicador > 7:
            multiplicador = 2
    
    resto = suma % 11
    dv_calculado = 11 - resto
    
    if dv_calculado == 11:
        dv_calculado = '0'
    elif dv_calculado == 10:
        dv_calculado = 'K'
    else:
        dv_calculado = str(dv_calculado)
    
    return dv == dv_calculado


def validar_nombre_usuario(nombre_usuario):
    """
    Valida un nombre de usuario
    
    Args:
        nombre_usuario (str): Nombre de usuario a validar
        
    Returns:
        bool: True si el nombre de usuario es válido
    """
    if not nombre_usuario or not isinstance(nombre_usuario, str):
        return False
    
    # Entre 3 y 30 caracteres
    if len(nombre_usuario) < 3 or len(nombre_usuario) > 30:
        return False
    
    # Solo letras, números y guiones bajos
    patron = r'^[a-zA-Z0-9_]+$'
    return bool(re.match(patron, nombre_usuario))


def validar_telefono(telefono):
    """
    Valida un número de teléfono chileno
    
    Args:
        telefono (str): Teléfono a validar
        
    Returns:
        bool: True si el teléfono es válido
    """
    if not telefono or not isinstance(telefono, str):
        return False
    
    # Limpiar teléfono (remover espacios, guiones, paréntesis)
    telefono_limpio = re.sub(r'[\s\-\(\)]', '', telefono.strip())
    
    # Patrones válidos para Chile
    patrones = [
        r'^(\+56)?9\d{8}$',  # Móvil: +56 9 XXXX XXXX o 9 XXXX XXXX
        r'^(\+56)?(2|32|33|34|35|41|42|43|45|51|52|53|55|57|58|61|63|64|65|67|71|72|73|75)\d{7,8}$'  # Fijo
    ]
    
    return any(re.match(patron, telefono_limpio) for patron in patrones)


def validar_url(url):
    """
    Valida una URL
    
    Args:
        url (str): URL a validar
        
    Returns:
        bool: True si la URL es válida
    """
    if not url or not isinstance(url, str):
        return False
    
    patron = r'^https?:\/\/(?:[-\w.])+(?:\:[0-9]+)?(?:\/(?:[\w\/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
    return bool(re.match(patron, url))


def validar_entero_positivo(valor):
    """
    Valida que un valor sea un entero positivo
    
    Args:
        valor: Valor a validar
        
    Returns:
        bool: True si es un entero positivo
    """
    try:
        numero = int(valor)
        return numero > 0
    except (ValueError, TypeError):
        return False


def validar_decimal_positivo(valor):
    """
    Valida que un valor sea un decimal positivo
    
    Args:
        valor: Valor a validar
        
    Returns:
        bool: True si es un decimal positivo
    """
    try:
        numero = float(valor)
        return numero > 0
    except (ValueError, TypeError):
        return False


def validar_fecha(fecha_str, formato='%Y-%m-%d'):
    """
    Valida que una cadena represente una fecha válida
    
    Args:
        fecha_str (str): Cadena de fecha a validar
        formato (str): Formato esperado de la fecha
        
    Returns:
        bool: True si la fecha es válida
    """
    if not fecha_str or not isinstance(fecha_str, str):
        return False
    
    try:
        from datetime import datetime
        datetime.strptime(fecha_str, formato)
        return True
    except ValueError:
        return False


def limpiar_rut(rut):
    """
    Limpia un RUT removiendo puntos y guiones
    
    Args:
        rut (str): RUT a limpiar
        
    Returns:
        str: RUT limpio
    """
    if not rut:
        return ""
    
    return re.sub(r'[.\-]', '', str(rut).strip().upper())


def formatear_rut(rut):
    """
    Formatea un RUT agregando puntos y guión
    
    Args:
        rut (str): RUT sin formato
        
    Returns:
        str: RUT formateado
    """
    if not rut:
        return ""
    
    rut_limpio = limpiar_rut(rut)
    
    if len(rut_limpio) < 2:
        return rut_limpio
    
    numero = rut_limpio[:-1]
    dv = rut_limpio[-1]
    
    # Agregar puntos cada 3 dígitos desde la derecha
    numero_formateado = ""
    for i, digito in enumerate(reversed(numero)):
        if i > 0 and i % 3 == 0:
            numero_formateado = "." + numero_formateado
        numero_formateado = digito + numero_formateado
    
    return f"{numero_formateado}-{dv}"


def validar_longitud(texto, min_longitud=1, max_longitud=255):
    """
    Valida la longitud de un texto
    
    Args:
        texto (str): Texto a validar
        min_longitud (int): Longitud mínima
        max_longitud (int): Longitud máxima
        
    Returns:
        bool: True si la longitud es válida
    """
    if not isinstance(texto, str):
        return False
    
    longitud = len(texto.strip())
    return min_longitud <= longitud <= max_longitud
