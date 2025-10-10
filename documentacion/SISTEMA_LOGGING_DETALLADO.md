# Sistema de Logging Detallado - Evolve Soluciones

## 📋 Descripción General

Sistema de logging especializado para diagnosticar problemas de autenticación, sesiones y errores CSRF. Proporciona logs detallados con toda la información necesaria para identificar por qué algunos usuarios tienen el navegador bloqueado.

## 📁 Archivos de Log Generados

Todos los archivos se generan automáticamente en la carpeta `logs/` con rotación automática (10MB por archivo, 10 backups).

### 1. `autenticacion.log`
**Propósito**: Registra todos los intentos de login (exitosos y fallidos)

**Información registrada**:
- Timestamp exacto
- Usuario que intenta iniciar sesión
- IP del cliente (considerando proxies)
- User Agent del navegador
- Referer (página de origen)
- Cookies presentes en la request
- Session ID de Flask
- Razón del fallo (si aplica)

**Ejemplo de entrada**:
```
2025-10-10 14:32:15 - autenticacion - WARNING -
================================================================================
INTENTO DE LOGIN - FALLIDO
Timestamp: 2025-10-10T14:32:15.123456
Usuario: juan.perez@empresa.cl
IP Cliente: 192.168.1.100
User Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/118.0.0.0
Referer: https://evolve.cl/auth/iniciar-sesion
Cookies presentes: session, _csrf_token
Session ID actual: abc123def456
Razón del fallo: Contraseña incorrecta
================================================================================
```

### 2. `csrf_errors.log`
**Propósito**: Registra todos los errores CSRF con contexto completo

**Información registrada**:
- Timestamp exacto
- Método HTTP (GET/POST/etc.)
- Ruta solicitada
- IP del cliente
- User Agent
- Referer y Origin headers
- Session ID de Flask
- Usuario autenticado (si aplica)
- CSRF Token en sesión vs. formulario
- **TODAS las cookies presentes** (con valores)
- **TODOS los headers HTTP**

**Ejemplo de entrada**:
```
2025-10-10 14:35:20 - csrf - ERROR -
================================================================================
ERROR CSRF DETECTADO
Timestamp: 2025-10-10T14:35:20.789012
Método: POST
Ruta: /auth/iniciar-sesion
IP Cliente: 192.168.1.100
User Agent: Mozilla/5.0...
Referer: https://evolve.cl/auth/iniciar-sesion
Origin: https://evolve.cl

SESIÓN:
Session ID: def456ghi789
Usuario autenticado: No autenticado
CSRF Token en sesión: No presente en sesión

FORMULARIO:
CSRF Token en formulario: No presente en formulario

COOKIES PRESENTES:
  - session: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
  - _ga: GA1.2.123456789.1234567890

HEADERS COMPLETOS:
  Host: evolve.cl
  Connection: keep-alive
  Content-Length: 234
  Cache-Control: max-age=0
  ...
================================================================================
```

### 3. `sesiones.log`
**Propósito**: Registra creación, invalidación y validación de sesiones

**Información registrada**:
- Creación de nuevas sesiones
- Tokens de sesión generados
- Número de sesiones cerradas (sesión única)
- Sesiones invalidadas y su razón
- Validaciones de sesión (válidas/inválidas)

**Ejemplo de entrada**:
```
2025-10-10 14:40:00 - sesiones - INFO -
================================================================================
NUEVA SESIÓN CREADA
Timestamp: 2025-10-10T14:40:00.123456
Usuario: juan.perez
Token de sesión: abc123def456ghi789
IP Cliente: 192.168.1.100
User Agent: Mozilla/5.0...
Session ID Flask: jkl012mno345
Sesiones previas cerradas: 2
================================================================================
```

### 4. `aplicacion.log`
**Propósito**: Log general de la aplicación y accesos bloqueados

**Información registrada**:
- Accesos bloqueados por permisos
- Eventos importantes de la aplicación
- Errores generales

## 🚀 Implementación

### Archivos Modificados

1. **`aplicacion/utilidades/logging_detallado.py`** (NUEVO)
   - 7 funciones especializadas de logging
   - Configuración de archivos de log con rotación
   - Formato detallado con timestamps

2. **`aplicacion.py`**
   - Importación de `configurar_logging_detallado`
   - Inicialización del sistema después de extensiones

3. **`aplicacion/controladores/autenticacion.py`**
   - `log_intento_login()` en cada intento de login
   - `log_creacion_sesion()` cuando se crea sesión
   - `log_acceso_bloqueado()` cuando cuenta está desactivada

4. **`aplicacion/utilidades/manejadores_errores.py`**
   - `log_error_csrf_detallado()` en manejador de CSRFError

## 🔍 Diagnóstico de Problemas

### Problema: Usuario con navegador bloqueado

**Pasos para diagnosticar**:

1. **Revisar `csrf_errors.log`**:
   ```bash
   cat logs/csrf_errors.log | grep "IP Cliente: 192.168.1.100"
   ```

   **Buscar**:
   - ¿Está presente el CSRF token en la sesión?
   - ¿Está presente el CSRF token en el formulario?
   - ¿Las cookies están llegando al servidor?
   - ¿El Referer/Origin son correctos?

2. **Revisar `autenticacion.log`**:
   ```bash
   cat logs/autenticacion.log | grep "juan.perez"
   ```

   **Buscar**:
   - ¿El usuario puede iniciar sesión exitosamente?
   - ¿Qué cookies tiene en cada intento?
   - ¿La IP cambia entre requests?

3. **Revisar `sesiones.log`**:
   ```bash
   cat logs/sesiones.log | grep "juan.perez"
   ```

   **Buscar**:
   - ¿Se crean múltiples sesiones rápidamente?
   - ¿Se invalidan sesiones constantemente?
   - ¿Cuántas sesiones previas se cierran al crear una nueva?

### Causas Comunes y Soluciones

#### 1. Cookies bloqueadas por el navegador
**Síntomas en logs**:
- `COOKIES PRESENTES:` vacío o solo cookies de terceros
- CSRF token no presente en sesión

**Solución**:
- Usuario debe habilitar cookies en configuración del navegador
- Verificar que no esté en modo incógnito con cookies deshabilitadas

#### 2. Extensiones del navegador bloqueando requests
**Síntomas en logs**:
- Headers faltantes (Origin, Referer)
- CSRF token presente en sesión pero no llega en formulario

**Solución**:
- Usuario debe desactivar extensiones de privacidad/seguridad
- Probar en modo incógnito sin extensiones

#### 3. Proxy corporativo manipulando headers
**Síntomas en logs**:
- IP cambia en cada request
- Headers modificados o eliminados
- Origin/Referer no coinciden con el dominio

**Solución**:
- Configurar proxy para preservar headers
- Agregar dominio a lista blanca del proxy

#### 4. Cache de navegador corrupto
**Síntomas en logs**:
- CSRF token en formulario es antiguo/inválido
- Sesión no se actualiza entre requests

**Solución**:
- Usuario debe limpiar cache y cookies del navegador
- Usar endpoint `/auth/limpiar-sesion` para forzar limpieza

## 📊 Funciones Disponibles

### `configurar_logging_detallado(app)`
Inicializa el sistema de logging. Se llama automáticamente al crear la aplicación.

### `log_intento_login(usuario, exito, razon=None, ip=None, user_agent=None, cookies=None)`
Registra intento de inicio de sesión.

**Ejemplo de uso**:
```python
log_intento_login(
    usuario="juan.perez",
    exito=False,
    razon="Contraseña incorrecta"
)
```

### `log_error_csrf_detallado(request_obj=None)`
Registra error CSRF con TODO el contexto. Si no se pasa `request_obj`, usa el request actual.

**Ejemplo de uso**:
```python
@app.errorhandler(CSRFError)
def manejar_csrf(e):
    log_error_csrf_detallado(request)
    return "Error CSRF", 400
```

### `log_sesion_invalidada(usuario, token, razon)`
Registra cuando una sesión es invalidada.

**Ejemplo de uso**:
```python
log_sesion_invalidada(
    usuario="juan.perez",
    token="abc123",
    razon="Sesión única - nueva sesión creada"
)
```

### `log_creacion_sesion(usuario, token, ip=None, sesiones_cerradas=0)`
Registra creación de nueva sesión.

**Ejemplo de uso**:
```python
log_creacion_sesion(
    usuario="juan.perez",
    token="def456",
    sesiones_cerradas=2
)
```

### `log_validacion_sesion(usuario, token, valida, razon=None)`
Registra validación de sesión.

**Ejemplo de uso**:
```python
log_validacion_sesion(
    usuario="juan.perez",
    token="abc123",
    valida=False,
    razon="Token no encontrado en BD"
)
```

### `log_acceso_bloqueado(usuario, razon, ip=None, ruta=None)`
Registra cuando se bloquea un acceso.

**Ejemplo de uso**:
```python
log_acceso_bloqueado(
    usuario="juan.perez",
    razon="Cuenta desactivada"
)
```

## 🔒 Seguridad y Privacidad

### Datos Sensibles en Logs

⚠️ **IMPORTANTE**: Los logs contienen información sensible:
- IPs de usuarios
- User agents (pueden identificar dispositivos)
- Cookies (aunque no las contraseñas)
- Tokens de sesión

### Recomendaciones de Seguridad

1. **Permisos de archivos**:
   ```bash
   chmod 600 logs/*.log  # Solo lectura/escritura para el propietario
   ```

2. **Rotación de logs**:
   - Automática cada 10MB
   - Máximo 10 backups (100MB total por tipo)
   - Archivos antiguos se eliminan automáticamente

3. **Retención de datos**:
   - Revisar normativas locales de protección de datos
   - Considerar eliminar logs después de 30-90 días
   - Implementar script de limpieza automática si es necesario

4. **Acceso restringido**:
   - Solo administradores deben tener acceso a logs
   - No exponer logs vía web
   - Usar herramientas de análisis locales

## 📈 Monitoreo y Alertas

### Comandos Útiles para Análisis

**Ver últimos errores CSRF**:
```bash
tail -100 logs/csrf_errors.log
```

**Contar intentos fallidos de login por usuario**:
```bash
grep "FALLIDO" logs/autenticacion.log | grep -o "Usuario: [^@]*" | sort | uniq -c
```

**Ver todas las IPs con errores CSRF**:
```bash
grep "IP Cliente:" logs/csrf_errors.log | sort | uniq -c
```

**Sesiones creadas en la última hora**:
```bash
grep "NUEVA SESIÓN CREADA" logs/sesiones.log | tail -50
```

### Integración con Herramientas

El formato de logs es compatible con:
- **Logstash/Elasticsearch**: Para análisis centralizado
- **Grafana**: Para visualización de métricas
- **Fail2Ban**: Para bloqueo automático de IPs sospechosas
- **Custom scripts**: Para alertas por email/Slack

## 🧪 Testing

Para verificar que el sistema funciona:

1. Iniciar la aplicación en desarrollo
2. Intentar login con credenciales incorrectas
3. Verificar que se genera `logs/autenticacion.log`
4. Intentar login sin CSRF token
5. Verificar que se genera `logs/csrf_errors.log`

## 📚 Referencias

- [Python Logging](https://docs.python.org/3/library/logging.html)
- [RotatingFileHandler](https://docs.python.org/3/library/logging.handlers.html#rotatingfilehandler)
- [Flask Request Object](https://flask.palletsprojects.com/en/3.0.x/api/#flask.Request)
- [CSRF Protection](https://flask-wtf.readthedocs.io/en/stable/csrf.html)
