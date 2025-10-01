"""
Herramientas de IP para Evolve Soluciones
=========================================

Utilidades para obtener y manejar direcciones IP de clientes,
considerando proxies, load balancers y redes privadas.
"""

from flask import request


def obtener_ip_real_cliente():
    """
    Obtiene la IP real del cliente considerando headers de proxy
    
    Returns:
        str: Dirección IP del cliente
    """
    # Lista de headers que pueden contener la IP real del cliente
    headers_ip = [
        'HTTP_X_FORWARDED_FOR',
        'HTTP_X_REAL_IP',
        'HTTP_X_FORWARDED',
        'HTTP_X_CLUSTER_CLIENT_IP',
        'HTTP_FORWARDED_FOR',
        'HTTP_FORWARDED',
        'HTTP_CLIENT_IP'
    ]
    
    # Intentar obtener IP desde headers de proxy
    for header in headers_ip:
        ip = request.environ.get(header)
        if ip:
            # X-Forwarded-For puede contener múltiples IPs separadas por coma
            if ',' in ip:
                # Tomar la primera IP (cliente original)
                ip = ip.split(',')[0].strip()
            
            # Validar que la IP sea válida
            if es_ip_valida(ip) and not es_ip_privada(ip):
                return ip
    
    # Si no se encuentra en headers, usar remote_addr
    return request.remote_addr or 'desconocida'


def es_ip_valida(ip):
    """
    Valida si una cadena representa una dirección IP válida
    
    Args:
        ip (str): Cadena a validar
        
    Returns:
        bool: True si es una IP válida
    """
    if not ip or not isinstance(ip, str):
        return False
    
    try:
        import ipaddress
        ipaddress.ip_address(ip.strip())
        return True
    except ValueError:
        return False


def es_ip_privada(ip):
    """
    Verifica si una IP pertenece a un rango privado
    
    Args:
        ip (str): Dirección IP a verificar
        
    Returns:
        bool: True si es una IP privada
    """
    if not es_ip_valida(ip):
        return False
    
    try:
        import ipaddress
        ip_obj = ipaddress.ip_address(ip.strip())
        return ip_obj.is_private
    except ValueError:
        return False


def es_ip_local(ip):
    """
    Verifica si una IP es localhost o loopback
    
    Args:
        ip (str): Dirección IP a verificar
        
    Returns:
        bool: True si es una IP local
    """
    if not es_ip_valida(ip):
        return False
    
    try:
        import ipaddress
        ip_obj = ipaddress.ip_address(ip.strip())
        return ip_obj.is_loopback
    except ValueError:
        return False


def obtener_informacion_cliente():
    """
    Obtiene información completa del cliente
    
    Returns:
        dict: Información del cliente
    """
    ip_real = obtener_ip_real_cliente()
    
    return {
        'ip_real': ip_real,
        'ip_remote': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'desconocido'),
        'referer': request.headers.get('Referer', ''),
        'accept_language': request.headers.get('Accept-Language', ''),
        'x_forwarded_for': request.headers.get('X-Forwarded-For', ''),
        'x_real_ip': request.headers.get('X-Real-IP', ''),
        'es_ip_privada': es_ip_privada(ip_real),
        'es_ip_local': es_ip_local(ip_real),
        'metodo_conexion': determinar_metodo_conexion(ip_real)
    }


def determinar_metodo_conexion(ip):
    """
    Determina el método de conexión basado en la IP
    
    Args:
        ip (str): Dirección IP del cliente
        
    Returns:
        str: Tipo de conexión
    """
    if not ip or ip == 'desconocida':
        return 'desconocida'
    
    if es_ip_local(ip):
        return 'local'
    
    if ip.startswith('192.168.'):
        return 'red_local'
    
    if ip.startswith('172.25.'):
        return 'zerotier'
    
    if ip.startswith('10.'):
        return 'vpn_corporativa'
    
    if es_ip_privada(ip):
        return 'red_privada'
    
    return 'internet'


def obtener_pais_por_ip(ip):
    """
    Obtiene el país asociado a una IP (requiere servicio externo)
    
    Args:
        ip (str): Dirección IP
        
    Returns:
        str: Código de país o 'desconocido'
    """
    # Esta función requeriría un servicio de geolocalización
    # Como GeoIP2, ipapi.co, etc.
    # Por ahora retorna 'desconocido'
    return 'desconocido'


def es_ip_bloqueada(ip, lista_bloqueadas=None):
    """
    Verifica si una IP está en la lista de IPs bloqueadas
    
    Args:
        ip (str): Dirección IP a verificar
        lista_bloqueadas (list): Lista de IPs bloqueadas
        
    Returns:
        bool: True si la IP está bloqueada
    """
    if not lista_bloqueadas:
        lista_bloqueadas = []
    
    if not es_ip_valida(ip):
        return False
    
    return ip.strip() in lista_bloqueadas


def formatear_ip_para_log(ip):
    """
    Formatea una IP para logging (puede ocultar parte por privacidad)
    
    Args:
        ip (str): Dirección IP
        
    Returns:
        str: IP formateada para log
    """
    if not es_ip_valida(ip):
        return 'ip_invalida'
    
    # Para IPs públicas, ocultar el último octeto por privacidad
    if not es_ip_privada(ip) and not es_ip_local(ip):
        partes = ip.split('.')
        if len(partes) == 4:
            return f"{partes[0]}.{partes[1]}.{partes[2]}.xxx"
    
    return ip


def obtener_estadisticas_ip():
    """
    Obtiene estadísticas de IPs que acceden al sistema
    
    Returns:
        dict: Estadísticas de acceso por IP
    """
    # Esta función requeriría acceso a logs o base de datos
    # para generar estadísticas reales
    return {
        'total_ips_unicas': 0,
        'ips_mas_frecuentes': [],
        'paises_mas_frecuentes': [],
        'tipos_conexion': {
            'local': 0,
            'red_local': 0,
            'zerotier': 0,
            'internet': 0
        }
    }


def validar_ip_permitida(ip, lista_permitidas=None):
    """
    Valida si una IP está en la lista de IPs permitidas
    
    Args:
        ip (str): Dirección IP a validar
        lista_permitidas (list): Lista de IPs o rangos permitidos
        
    Returns:
        bool: True si la IP está permitida
    """
    if not lista_permitidas:
        # Si no hay lista de permitidas, permitir todas las IPs válidas
        return es_ip_valida(ip)
    
    if not es_ip_valida(ip):
        return False
    
    try:
        import ipaddress
        ip_obj = ipaddress.ip_address(ip.strip())
        
        for permitida in lista_permitidas:
            try:
                # Verificar si es una IP individual
                if '/' not in permitida:
                    if ip_obj == ipaddress.ip_address(permitida):
                        return True
                else:
                    # Verificar si está en el rango de red
                    red = ipaddress.ip_network(permitida, strict=False)
                    if ip_obj in red:
                        return True
            except ValueError:
                continue
        
        return False
    except ValueError:
        return False
