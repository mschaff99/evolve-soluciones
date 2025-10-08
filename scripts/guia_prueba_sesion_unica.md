"""
Guía de Prueba: Una Sola Sesión Activa por Usuario
==================================================

Esta guía te explica cómo probar que la nueva funcionalidad
de "una sola sesión activa" funciona correctamente.

FUNCIONALIDAD IMPLEMENTADA:
-  Solo puede haber una sesión activa por usuario
-  Al iniciar sesión desde un nuevo dispositivo/navegador, se cierra la sesión anterior
-  El usuario recibe un mensaje explicando que su sesión fue cerrada por otro login
-  La IP real del cliente se detecta correctamente (incluso detrás de proxies)

CAMBIOS REALIZADOS:
================

1. MODELO DE SESIÓN (aplicacion/modelos/sesion.py):
   - Nuevo método: crear_sesion_unica()
   - Nuevo método: validar_sesion_unica()
   - Mejora en cerrar_todas_sesiones_usuario()

2. CONTROLADOR DE AUTENTICACIÓN (aplicacion/controladores/autenticacion.py):
   - Cambiado crear_sesion() por crear_sesion_unica()
   - Ahora cierra automáticamente sesiones previas al hacer login

3. MIDDLEWARE (aplicacion.py):
   - Nuevo middleware validar_sesion_unica()
   - Verifica en cada request si la sesión sigue siendo válida
   - Cierra automáticamente sesiones invalidadas

4. DETECCIÓN DE IP (aplicacion/utilidades/herramientas_ip.py):
   - Mejorada para detectar IP real detrás de proxies
   - Soporta headers X-Forwarded-For, X-Real-IP, etc.
   - Configurado ProxyFix middleware

CÓMO PROBAR:
============

PRUEBA 1: SESIÓN ÚNICA BÁSICA
-----------------------------
1. Abrir navegador Chrome e iniciar sesión con tu usuario
2. Verificar que puedes navegar normalmente
3. Abrir navegador Edge (o modo incógnito) e iniciar sesión con el MISMO usuario
4.  RESULTADO ESPERADO: La sesión en Chrome se cierra automáticamente
5.  En Chrome aparece mensaje: "Tu sesión ha sido cerrada porque iniciaste sesión desde otro dispositivo"

PRUEBA 2: SESIÓN DESDE CELULAR
------------------------------
1. Iniciar sesión desde tu computadora
2. Iniciar sesión desde tu celular con el mismo usuario
3.  RESULTADO ESPERADO: La sesión en computadora se cierra
4.  Al volver a la computadora aparece el mensaje de sesión cerrada

PRUEBA 3: VERIFICAR IP REAL
---------------------------
1. Iniciar sesión desde celular
2. Ir a: http://tu-dominio/diagnostico
3.  RESULTADO ESPERADO:
   - "ip_cliente" debe mostrar tu IP real (no 127.0.0.1)
   - "metodo_conexion" debe detectar el tipo correcto

COMPORTAMIENTO DETALLADO:
========================

ESCENARIO A: Usuario inicia sesión
----------------------------------
1. Usuario ingresa credenciales
2. Sistema valida usuario/contraseña
3. Sistema llama crear_sesion_unica():
   a. Cierra TODAS las sesiones activas del usuario
   b. Crea una nueva sesión
   c. Guarda token en la sesión Flask
4. Usuario queda con UNA SOLA sesión activa

ESCENARIO B: Usuario navega (cada request)
------------------------------------------
1. Middleware validar_sesion_unica() se ejecuta
2. Si hay token de sesión:
   a. Verifica que la sesión sigue siendo la única activa
   b. Si hay otras sesiones activas → Invalida esta sesión
   c. Si la sesión fue invalidada → Logout + redirección
   d. Si la sesión es válida → Actualiza timestamp
3. Usuario continúa navegando o es desconectado

ESCENARIO C: Segundo login simultáneo
------------------------------------
1. Mismo usuario inicia sesión desde otro dispositivo
2. Sistema ejecuta crear_sesion_unica():
   a. Cierra la sesión anterior (la de primer dispositivo)
   b. Crea nueva sesión para segundo dispositivo
3. En el primer dispositivo:
   a. Próximo request ejecuta validar_sesion_unica()
   b. Detecta que su sesión ya no es la única activa
   c. Cierra sesión automáticamente
   d. Redirige al login con mensaje explicativo

MENSAJES ESPERADOS:
==================

 Al crear sesión única:
" Sesión única creada para usuario X. Token: abc123..."

 Al invalidar sesión:
"🔒 Sesión invalidada automáticamente: abc123..."

 Al usuario desconectado:
"Tu sesión ha sido cerrada porque iniciaste sesión desde otro dispositivo."

ARCHIVOS MODIFICADOS:
====================
- aplicacion/modelos/sesion.py (nuevos métodos)
- aplicacion/controladores/autenticacion.py (usar crear_sesion_unica)
- aplicacion.py (nuevo middleware)
- aplicacion/utilidades/herramientas_ip.py (mejorar detección IP)
- wsgi_waitress.py (ProxyFix middleware)

CONFIGURACIÓN REQUERIDA:
=======================

Para detectar IP real en IIS:
1. Instalar Application Request Routing (ARR)
2. Habilitar "Preserve client IP in X-Forwarded-For"
3. Configurar reverse proxy hacia Waitress

Para test local:
1. El middleware ProxyFix ya está configurado
2. Solo ejecutar la aplicación y probar

TROUBLESHOOTING:
===============

Si no funciona la sesión única:
- Verificar que PostgreSQL esté corriendo
- Verificar tabla auth.sesiones_usuario existe
- Revisar logs en consola de Python

Si IP sigue siendo 127.0.0.1:
- Verificar configuración de IIS/ARR
- Revisar que ProxyFix esté habilitado
- Probar acceso directo a Waitress (puerto 8080)

¡LISTO PARA PROBAR!
"""
