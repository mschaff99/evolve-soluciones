# Reporte de Seguridad - Evolve Soluciones

**Fecha:** 2025-12-11  
**Clasificación:** Interno  
**Analista:** GitHub Copilot Security Analysis

---

## Resumen Ejecutivo

Este reporte identifica 3 vulnerabilidades de seguridad en el código de Evolve Soluciones, clasificadas por severidad. Se proporcionan ejemplos de código vulnerable y soluciones específicas para cada caso.

### Estado de Seguridad

| Categoría | Estado |
|-----------|--------|
| Vulnerabilidades Críticas | 1 🔴 |
| Vulnerabilidades Medias | 2 🟡 |
| Vulnerabilidades Bajas | 0 🟢 |
| Buenas Prácticas | Mayormente implementadas ✅ |

---

## 1. Vulnerabilidades Identificadas

### 🔴 CRÍTICO-001: SQL Injection por Interpolación de Nombre de Base de Datos

**Severidad:** CRÍTICA  
**CWE:** CWE-89 (SQL Injection)  
**CVSS Score:** 9.1 (Crítico)

#### Descripción

El código utiliza f-strings para interpolar nombres de bases de datos en consultas SQL, lo cual puede llevar a SQL injection si el valor no está correctamente validado.

#### Ubicaciones Afectadas

1. `aplicacion/servicios/servicio_consulta_integral.py`
   - Línea 250: `cursor.execute(f"SELECT COUNT(*) as total FROM {self.base_datos}.consulta_integral")`
   - Línea 254: `cursor.execute(f"SELECT COUNT(*) as total FROM {self.base_datos}.observaciones")`
   - Línea 258-260: Múltiples queries con `{self.base_datos}`

2. `aplicacion/utilidades/filtros_empresas.py`
   - Línea 96: `consulta = f"SELECT {campos} FROM empresas"`

3. `aplicacion/servicios/servicio_situacion_tributaria.py`
   - Línea 84: `sql_obs_agg = f"SELECT consulta_id, COUNT(*) as total FROM {self.base_datos}.observaciones..."`

#### Código Vulnerable

```python
# ❌ VULNERABLE
class ServicioConsultaIntegral:
    def __init__(self, base_datos='stratex'):
        self.base_datos = base_datos
    
    def obtener_estadisticas(self):
        cursor.execute(f"SELECT COUNT(*) as total FROM {self.base_datos}.consulta_integral")
        # Si base_datos = "stratex; DROP DATABASE evolve; --"
        # Query resultante: SELECT COUNT(*) FROM stratex; DROP DATABASE evolve; --.consulta_integral
```

#### Impacto Potencial

- Ejecución de comandos SQL arbitrarios
- Acceso no autorizado a datos de otras bases de datos
- Modificación o eliminación de datos
- Escalada de privilegios

#### Solución Recomendada

**Opción 1: Whitelist Estricta (RECOMENDADA)**

```python
"""
Validador de nombres de bases de datos
Agregar a: aplicacion/utilidades/validadores.py
"""

import re
from typing import List

# Lista blanca de bases de datos permitidas
BASES_DATOS_PERMITIDAS = [
    'stratex',
    'evolve',
    'audisoft',
    'gestion_contable',
    # Agregar otras bases de datos legítimas aquí
]

def validar_nombre_base_datos(nombre_bd: str) -> str:
    """
    Valida que el nombre de base de datos sea seguro y permitido
    
    Args:
        nombre_bd: Nombre de la base de datos a validar
        
    Returns:
        str: Nombre validado de base de datos
        
    Raises:
        ValueError: Si el nombre no es válido o no está permitido
    """
    # Verificar que no sea None o vacío
    if not nombre_bd:
        raise ValueError("El nombre de base de datos no puede estar vacío")
    
    # Convertir a string y limpiar espacios
    nombre_bd = str(nombre_bd).strip()
    
    # Validar que solo contenga caracteres alfanuméricos y guión bajo
    if not re.match(r'^[a-zA-Z0-9_]+$', nombre_bd):
        raise ValueError(
            f"Nombre de base de datos contiene caracteres inválidos: {nombre_bd}"
        )
    
    # Verificar que esté en la lista blanca
    if nombre_bd not in BASES_DATOS_PERMITIDAS:
        raise ValueError(
            f"Base de datos no permitida: {nombre_bd}. "
            f"Bases de datos permitidas: {', '.join(BASES_DATOS_PERMITIDAS)}"
        )
    
    return nombre_bd


def validar_nombre_tabla(nombre_tabla: str) -> str:
    """
    Valida que el nombre de tabla sea seguro
    
    Args:
        nombre_tabla: Nombre de la tabla a validar
        
    Returns:
        str: Nombre validado de tabla
        
    Raises:
        ValueError: Si el nombre no es válido
    """
    if not nombre_tabla:
        raise ValueError("El nombre de tabla no puede estar vacío")
    
    nombre_tabla = str(nombre_tabla).strip()
    
    # Validar que solo contenga caracteres alfanuméricos, guión bajo y punto
    if not re.match(r'^[a-zA-Z0-9_\.]+$', nombre_tabla):
        raise ValueError(
            f"Nombre de tabla contiene caracteres inválidos: {nombre_tabla}"
        )
    
    # No permitir múltiples puntos consecutivos ni comenzar/terminar con punto
    if '..' in nombre_tabla or nombre_tabla.startswith('.') or nombre_tabla.endswith('.'):
        raise ValueError(f"Formato de nombre de tabla inválido: {nombre_tabla}")
    
    return nombre_tabla
```

**Implementación en ServicioConsultaIntegral:**

```python
# ✅ SEGURO
from aplicacion.utilidades.validadores import validar_nombre_base_datos

class ServicioConsultaIntegral:
    def __init__(self, base_datos='stratex'):
        """
        Inicializa el servicio con validación de base de datos
        
        Args:
            base_datos: Nombre de la base de datos MySQL
            
        Raises:
            ValueError: Si el nombre de base de datos no es válido
        """
        self.config = config
        # VALIDAR antes de asignar
        self.base_datos = validar_nombre_base_datos(base_datos)
    
    def obtener_estadisticas(self):
        """
        Obtiene estadísticas generales del sistema
        
        Returns:
            dict: Estadísticas del sistema
        """
        conexion = None
        try:
            conexion = self.obtener_conexion_evolve()
            
            with conexion.cursor() as cursor:
                # La base de datos ya fue validada en __init__
                # Es seguro usarla en f-string ahora
                cursor.execute(
                    f"SELECT COUNT(*) as total FROM {self.base_datos}.consulta_integral"
                )
                total_periodos = cursor.fetchone()['total']
                
                cursor.execute(
                    f"SELECT COUNT(*) as total FROM {self.base_datos}.observaciones"
                )
                total_observaciones = cursor.fetchone()['total']
                
                return {
                    'total_periodos': total_periodos,
                    'total_observaciones': total_observaciones
                }
        
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
            raise
        finally:
            if conexion:
                conexion.close()
```

**Opción 2: Quoted Identifiers (Alternativa)**

Si no puedes usar whitelist (por ejemplo, si las bases de datos son dinámicas):

```python
import pymysql

def escapar_identificador(nombre: str) -> str:
    """
    Escapa un identificador SQL (base de datos, tabla, columna)
    usando backticks de MySQL
    
    Args:
        nombre: Nombre a escapar
        
    Returns:
        str: Identificador escapado
    """
    # Remover caracteres peligrosos
    nombre_limpio = ''.join(c for c in nombre if c.isalnum() or c == '_')
    
    # Envolver en backticks
    return f"`{nombre_limpio}`"

# Uso
base_datos_escapada = escapar_identificador(self.base_datos)
cursor.execute(f"SELECT COUNT(*) FROM {base_datos_escapada}.consulta_integral")
```

#### Tests de Seguridad

```python
# tests/test_seguridad_sql.py
import pytest
from aplicacion.utilidades.validadores import validar_nombre_base_datos

def test_sql_injection_base_datos():
    """Verifica que se previene SQL injection en nombres de BD"""
    
    # Casos válidos
    assert validar_nombre_base_datos('stratex') == 'stratex'
    assert validar_nombre_base_datos('evolve') == 'evolve'
    
    # Casos maliciosos deben lanzar ValueError
    with pytest.raises(ValueError):
        validar_nombre_base_datos("stratex; DROP DATABASE evolve; --")
    
    with pytest.raises(ValueError):
        validar_nombre_base_datos("stratex' OR '1'='1")
    
    with pytest.raises(ValueError):
        validar_nombre_base_datos("../etc/passwd")
    
    with pytest.raises(ValueError):
        validar_nombre_base_datos("stratex--comment")
    
    with pytest.raises(ValueError):
        validar_nombre_base_datos("")
    
    with pytest.raises(ValueError):
        validar_nombre_base_datos("base_datos_no_permitida")
```

#### Verificación

```python
# Script de verificación: scripts/verificar_seguridad_sql.py
"""
Verifica que todas las interpolaciones de BD estén protegidas
"""
import re
import os

def buscar_interpolaciones_sql():
    """Busca interpolaciones potencialmente inseguras"""
    patron = re.compile(r'f["\'].*SELECT.*\{.*\}.*FROM', re.IGNORECASE)
    
    vulnerables = []
    for root, dirs, files in os.walk('aplicacion'):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f, 1):
                        if patron.search(line):
                            vulnerables.append((path, i, line.strip()))
    
    return vulnerables

if __name__ == '__main__':
    resultados = buscar_interpolaciones_sql()
    if resultados:
        print("⚠️  Interpolaciones SQL potencialmente inseguras encontradas:")
        for path, line, code in resultados:
            print(f"\n{path}:{line}")
            print(f"  {code}")
    else:
        print("✅ No se encontraron interpolaciones SQL inseguras")
```

#### Timeline de Implementación

- **Día 1:** Agregar función `validar_nombre_base_datos()` a validadores.py
- **Día 2:** Actualizar `ServicioConsultaIntegral.__init__()`
- **Día 3:** Actualizar otros servicios afectados
- **Día 4:** Crear y ejecutar tests de seguridad
- **Día 5:** Code review y validación final

---

### 🟡 MEDIO-001: Uso de Subprocess con Validación Incompleta

**Severidad:** MEDIA  
**CWE:** CWE-78 (OS Command Injection)  
**CVSS Score:** 6.3 (Medio)

#### Descripción

El código utiliza `subprocess.Popen` sin validación exhaustiva de entrada, lo cual puede llevar a command injection.

#### Ubicación

`aplicacion/servicios/servicio_integracion_gci.py:179-185`

#### Código Actual

```python
proceso = subprocess.Popen(
    comando,  # ¿Comando validado?
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
)
```

#### Solución Recomendada

```python
import subprocess
import shlex
from typing import List

COMANDOS_PERMITIDOS = {
    'gci_tool': '/usr/bin/gci_tool',
    'data_processor': '/usr/bin/data_processor'
}

def ejecutar_comando_seguro(comando: str, argumentos: List[str]) -> subprocess.CompletedProcess:
    """
    Ejecuta un comando de forma segura con validación
    
    Args:
        comando: Nombre del comando (debe estar en COMANDOS_PERMITIDOS)
        argumentos: Lista de argumentos para el comando
        
    Returns:
        subprocess.CompletedProcess: Resultado de la ejecución
        
    Raises:
        ValueError: Si el comando no está permitido
        RuntimeError: Si la ejecución falla
    """
    # Validar que el comando esté permitido
    if comando not in COMANDOS_PERMITIDOS:
        raise ValueError(f"Comando no permitido: {comando}")
    
    # Obtener path completo del comando
    comando_path = COMANDOS_PERMITIDOS[comando]
    
    # Validar que el ejecutable existe
    if not os.path.isfile(comando_path):
        raise RuntimeError(f"Ejecutable no encontrado: {comando_path}")
    
    # Construir comando con lista (NO string) para prevenir shell injection
    cmd_lista = [comando_path] + argumentos
    
    try:
        # Ejecutar SIN shell=True para seguridad
        resultado = subprocess.run(
            cmd_lista,
            capture_output=True,
            text=True,
            timeout=30,  # Timeout para prevenir procesos colgados
            check=True   # Lanza excepción si exit code != 0
        )
        return resultado
    
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Comando excedió timeout de 30 segundos: {comando}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Comando falló con código {e.returncode}: {e.stderr}")
```

#### Verificación

```python
# Test
def test_comando_seguro():
    # Válido
    resultado = ejecutar_comando_seguro('gci_tool', ['--input', 'data.txt'])
    
    # Inválido - debe fallar
    with pytest.raises(ValueError):
        ejecutar_comando_seguro('rm -rf /', [])
```

---

### 🟡 MEDIO-002: Emojis en Código Productivo

**Severidad:** BAJA-MEDIA  
**CWE:** N/A (Violación de estándares)  
**Impacto:** Mantenibilidad, Compatibilidad

#### Descripción

Según los estándares del proyecto, no deben usarse emojis en código productivo, pero se encontraron en archivos de prompts.

#### Ubicaciones

1. `aplicacion/prompts/proveedores_prompts.py:240` - `⚠️`
2. `aplicacion/prompts/balance_prompts.py:24` - `⚠️`

#### Solución

```python
# ❌ Antes
prompt = "- Marca claramente los hallazgos críticos con ⚠️"

# ✅ Después
prompt = "- Marca claramente los hallazgos críticos con [ADVERTENCIA]"
```

o

```python
# Alternativa: Constantes
MARCADOR_ADVERTENCIA = "[ADVERTENCIA]"
MARCADOR_CRITICO = "[CRÍTICO]"
MARCADOR_INFO = "[INFO]"

prompt = f"- Marca claramente los hallazgos críticos con {MARCADOR_CRITICO}"
```

---

## 2. Buenas Prácticas Implementadas

### ✅ Consultas Parametrizadas

La mayoría del código usa correctamente placeholders:

```python
# ✅ SEGURO
consulta = "SELECT * FROM usuarios WHERE email = %s AND activo = %s"
resultado = ejecutar_consulta(consulta, (email, True))
```

### ✅ Hashing de Contraseñas

```python
# ✅ SEGURO - Bcrypt implementado
from flask_bcrypt import Bcrypt
bcrypt = Bcrypt()

# Al crear usuario
hash_contraseña = bcrypt.generate_password_hash(contraseña).decode('utf-8')

# Al verificar
bcrypt.check_password_hash(usuario.contraseña, contraseña_input)
```

### ✅ Protección CSRF

```python
# ✅ SEGURO
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)

# En templates
<form method="POST">
    {{ csrf_token() }}
    <!-- campos del formulario -->
</form>
```

### ✅ Decoradores de Autorización

```python
# ✅ SEGURO
@login_required
@solo_administradores
def vista_admin():
    # Solo accesible por admins autenticados
    pass
```

---

## 3. Checklist de Seguridad

### Autenticación y Autorización
- [x] Hashing de contraseñas con Bcrypt
- [x] Flask-Login implementado
- [x] Decoradores de autorización
- [x] Logging de intentos fallidos
- [ ] Rate limiting en login
- [ ] 2FA (Two-Factor Authentication)

### SQL Injection
- [x] Consultas parametrizadas en mayoría del código
- [ ] Validación de nombres de BD dinámicos ⚠️ PENDIENTE
- [x] No concatenación de strings SQL con datos de usuario

### XSS (Cross-Site Scripting)
- [x] Jinja2 auto-escape habilitado
- [x] Sanitización de salida
- [ ] Content Security Policy headers

### CSRF (Cross-Site Request Forgery)
- [x] CSRF tokens en formularios
- [x] Flask-WTF CSRFProtect habilitado
- [x] Validación en servidor

### Inyección de Comandos
- [ ] Validación exhaustiva de subprocess ⚠️ PENDIENTE
- [x] No uso de eval() o exec()
- [x] No shell=True en subprocess

### Gestión de Sesiones
- [x] Tokens únicos por sesión
- [x] Sesiones en BD
- [x] Timeout de sesión configurado
- [ ] Rotación de tokens de sesión

### Secrets y Configuración
- [x] Variables de entorno para secrets
- [x] .env no en repositorio
- [x] env.ejemplo como plantilla
- [ ] Encriptación de secrets en BD

### Headers de Seguridad
- [ ] X-Content-Type-Options
- [ ] X-Frame-Options
- [ ] X-XSS-Protection
- [ ] Strict-Transport-Security (HSTS)
- [ ] Content-Security-Policy

---

## 4. Recomendaciones Adicionales

### 4.1 Headers de Seguridad

Agregar a `aplicacion.py`:

```python
@app.after_request
def agregar_headers_seguridad(response):
    """Agrega headers de seguridad a todas las respuestas"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    if app.config['ENV'] == 'produccion':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    return response
```

### 4.2 Rate Limiting

```bash
pip install Flask-Limiter
```

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@autenticacion_bp.route('/iniciar-sesion', methods=['POST'])
@limiter.limit("5 per minute")
def iniciar_sesion():
    # Máximo 5 intentos por minuto
    pass
```

### 4.3 Auditoría de Dependencias

```bash
# Agregar a CI/CD
pip install safety
safety check --file requirements.txt --json
```

### 4.4 Secrets Scanning

```bash
# Pre-commit hook
pip install detect-secrets
detect-secrets scan --baseline .secrets.baseline
```

---

## 5. Plan de Remediación

### Fase 1: Crítico (1-2 semanas)
- [ ] Implementar validación de nombres de BD
- [ ] Actualizar todos los servicios afectados
- [ ] Crear tests de seguridad SQL
- [ ] Validación exhaustiva de subprocess

### Fase 2: Importante (2-3 semanas)
- [ ] Agregar headers de seguridad
- [ ] Implementar rate limiting
- [ ] Remover emojis de código productivo
- [ ] Auditoría de dependencias

### Fase 3: Mejora Continua (1-2 meses)
- [ ] Implementar 2FA
- [ ] Content Security Policy
- [ ] Encriptación de secrets en BD
- [ ] Rotación automática de tokens

---

## 6. Contacto y Escalación

Para reportar vulnerabilidades de seguridad:

- **Email:** security@evolve-soluciones.com
- **Proceso:** Responsible Disclosure (90 días)
- **PGP Key:** [Agregar si está disponible]

---

**Documento generado por:** GitHub Copilot Security Analysis  
**Fecha:** 2025-12-11  
**Próxima revisión:** 2025-12-18
