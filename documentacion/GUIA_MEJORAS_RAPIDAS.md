# Guía de Mejoras Rápidas - Evolve Soluciones

**Para:** Equipo de Desarrollo  
**Objetivo:** Implementar mejoras críticas y de alto impacto rápidamente  
**Tiempo estimado total:** 2-3 semanas

---

## 🎯 Prioridades (Quick Wins)

### Día 1: Seguridad Crítica (4 horas)

#### 1. Crear validador de nombres de BD

**Archivo:** `aplicacion/utilidades/validadores.py`

**Agregar al final del archivo:**

```python
# ==========================================
# VALIDACIÓN DE IDENTIFICADORES SQL
# ==========================================

import re
from typing import List

# Lista blanca de bases de datos permitidas
BASES_DATOS_PERMITIDAS = [
    'stratex',
    'evolve',
    'audisoft',
    'gestion_contable',
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
        
    Example:
        >>> validar_nombre_base_datos('stratex')
        'stratex'
        >>> validar_nombre_base_datos('malicious; DROP DATABASE')
        ValueError: Nombre de base de datos contiene caracteres inválidos
    """
    if not nombre_bd:
        raise ValueError("El nombre de base de datos no puede estar vacío")
    
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
```

#### 2. Actualizar ServicioConsultaIntegral

**Archivo:** `aplicacion/servicios/servicio_consulta_integral.py`

**Modificar línea 26-35:**

```python
# ANTES
def __init__(self, base_datos='stratex'):
    """
    Inicializa el servicio con la base de datos a usar

    Args:
        base_datos (str): Nombre de la base de datos MySQL (ej: 'stratex', 'evolve', etc.)
    """
    self.config = config
    self.base_datos = base_datos

# DESPUÉS
def __init__(self, base_datos='stratex'):
    """
    Inicializa el servicio con la base de datos a usar

    Args:
        base_datos (str): Nombre de la base de datos MySQL
        
    Raises:
        ValueError: Si el nombre de base de datos no es válido
    """
    from aplicacion.utilidades.validadores import validar_nombre_base_datos
    
    self.config = config
    # VALIDAR antes de asignar
    self.base_datos = validar_nombre_base_datos(base_datos)
```

#### 3. Actualizar otros servicios afectados

**Archivos a modificar:**
- `aplicacion/servicios/servicio_situacion_tributaria.py` (línea 20)
- `aplicacion/servicios/servicio_dj_integral.py` (línea ~30)
- `aplicacion/servicios/servicio_empresas.py` (línea ~35)

**Patrón a aplicar:** Igual que ServicioConsultaIntegral

---

### Día 2: Headers de Seguridad (2 horas)

**Archivo:** `aplicacion.py`

**Agregar después de línea 75 (antes de return aplicacion):**

```python
    # Registrar headers de seguridad
    registrar_headers_seguridad(aplicacion)
    
    return aplicacion


def registrar_headers_seguridad(aplicacion):
    """Registra headers de seguridad en todas las respuestas"""
    
    @aplicacion.after_request
    def agregar_headers_seguridad(response):
        """Agrega headers de seguridad HTTP"""
        
        # Prevenir MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Prevenir clickjacking
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        
        # Protección XSS (legacy, pero no hace daño)
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Política de referrer
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # HTTPS estricto en producción
        if aplicacion.config['ENV'] == 'produccion':
            response.headers['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains'
            )
        
        return response
```

---

### Día 3: Rate Limiting (3 horas)

#### 1. Instalar dependencia

```bash
pip install Flask-Limiter
```

#### 2. Actualizar requirements.txt

```bash
pip freeze | grep Flask-Limiter >> requirements.txt
```

#### 3. Inicializar limiter

**Archivo:** `aplicacion/utilidades/inicializadores.py`

**Agregar al final:**

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Inicializar limiter global
limiter = None

def inicializar_rate_limiter(aplicacion):
    """Inicializa rate limiting"""
    global limiter
    
    limiter = Limiter(
        app=aplicacion,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://",  # Usar Redis en producción
    )
    
    return limiter
```

**Modificar función inicializar_extensiones:**

```python
def inicializar_extensiones(aplicacion):
    """Inicializa todas las extensiones de Flask"""
    from flask_login import LoginManager
    from flask_bcrypt import Bcrypt
    from flask_wtf.csrf import CSRFProtect
    
    # ... código existente ...
    
    # Inicializar rate limiter
    inicializar_rate_limiter(aplicacion)
```

#### 4. Aplicar rate limiting a login

**Archivo:** `aplicacion/controladores/autenticacion.py`

**Agregar import:**

```python
from aplicacion.utilidades.inicializadores import limiter
```

**Modificar función iniciar_sesion (línea 29):**

```python
@autenticacion_bp.route('/iniciar-sesion', methods=['GET', 'POST'])
@limiter.limit("10 per minute")  # AGREGAR ESTA LÍNEA
def iniciar_sesion():
    """Maneja el inicio de sesión de usuarios"""
    # ... resto del código
```

---

### Día 4-5: Tests Básicos (8 horas)

#### 1. Instalar pytest

```bash
pip install pytest pytest-cov pytest-flask
pip freeze | grep pytest >> requirements.txt
```

#### 2. Crear estructura

```bash
mkdir -p pruebas
touch pruebas/__init__.py
touch pruebas/conftest.py
```

#### 3. Configurar pytest

**Archivo:** `pruebas/conftest.py`

```python
"""
Configuración de fixtures para tests
"""
import pytest
from aplicacion import crear_aplicacion
from configuracion.configuracion import ConfiguracionPruebas

@pytest.fixture
def app():
    """Fixture de aplicación Flask"""
    app = crear_aplicacion('pruebas')
    return app

@pytest.fixture
def client(app):
    """Fixture de cliente de pruebas"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Fixture de CLI runner"""
    return app.test_cli_runner()
```

#### 4. Tests de validadores

**Archivo:** `pruebas/test_validadores.py`

```python
"""
Tests para validadores de seguridad
"""
import pytest
from aplicacion.utilidades.validadores import validar_nombre_base_datos

def test_validar_base_datos_valida():
    """Test con nombres de BD válidos"""
    assert validar_nombre_base_datos('stratex') == 'stratex'
    assert validar_nombre_base_datos('evolve') == 'evolve'

def test_validar_base_datos_sql_injection():
    """Test prevención de SQL injection"""
    with pytest.raises(ValueError):
        validar_nombre_base_datos("stratex; DROP DATABASE evolve; --")
    
    with pytest.raises(ValueError):
        validar_nombre_base_datos("stratex' OR '1'='1")

def test_validar_base_datos_caracteres_invalidos():
    """Test caracteres inválidos"""
    with pytest.raises(ValueError):
        validar_nombre_base_datos("../etc/passwd")
    
    with pytest.raises(ValueError):
        validar_nombre_base_datos("base-datos")  # Guión no permitido

def test_validar_base_datos_vacia():
    """Test BD vacía"""
    with pytest.raises(ValueError):
        validar_nombre_base_datos("")

def test_validar_base_datos_no_permitida():
    """Test BD no en whitelist"""
    with pytest.raises(ValueError):
        validar_nombre_base_datos("base_datos_maliciosa")
```

#### 5. Ejecutar tests

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=aplicacion

# Con output detallado
pytest -v
```

---

### Semana 2: Mejoras de Código

#### Día 1: Context Manager para BD (4 horas)

**Archivo:** `aplicacion/modelos/base_datos.py`

**Agregar al final:**

```python
# ==========================================
# CONTEXT MANAGERS
# ==========================================

from contextlib import contextmanager

@contextmanager
def conexion_mysql(nombre_bd):
    """
    Context manager para conexiones MySQL
    
    Uso:
        with conexion_mysql('stratex') as cursor:
            cursor.execute("SELECT ...")
            
    Args:
        nombre_bd: Nombre de la base de datos
        
    Yields:
        pymysql.cursors.DictCursor: Cursor de base de datos
        
    Example:
        >>> with conexion_mysql('stratex') as cursor:
        ...     cursor.execute("SELECT * FROM empresas LIMIT 10")
        ...     empresas = cursor.fetchall()
    """
    from aplicacion.utilidades.validadores import validar_nombre_base_datos
    
    nombre_bd = validar_nombre_base_datos(nombre_bd)
    conexion = None
    
    try:
        conexion = obtener_conexion_local(nombre_bd)
        with conexion.cursor(pymysql.cursors.DictCursor) as cursor:
            yield cursor
    except Exception as e:
        print(f"Error en conexión a BD {nombre_bd}: {e}")
        raise
    finally:
        if conexion:
            conexion.close()


@contextmanager
def conexion_postgres():
    """
    Context manager para conexiones PostgreSQL
    
    Uso:
        with conexion_postgres() as cursor:
            cursor.execute("SELECT ...")
    """
    conexion = None
    
    try:
        conexion = obtener_conexion_postgres()
        with conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            yield cursor
        conexion.commit()
    except Exception as e:
        if conexion:
            conexion.rollback()
        print(f"Error en conexión a PostgreSQL: {e}")
        raise
    finally:
        if conexion:
            conexion.close()
```

#### Ejemplo de uso:

```python
# ANTES
def obtener_empresas(self):
    conexion = None
    try:
        conexion = obtener_conexion_local(self.base_datos)
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM empresas")
            return cursor.fetchall()
    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        if conexion:
            conexion.close()

# DESPUÉS
def obtener_empresas(self):
    with conexion_mysql(self.base_datos) as cursor:
        cursor.execute("SELECT * FROM empresas")
        return cursor.fetchall()
```

---

### Día 2-3: Agregar Docstrings (8 horas)

**Lista de funciones sin documentar:**

1. `aplicacion/modelos/base_datos.py:427` - `__init__`
2. `aplicacion/modelos/sesion.py:22` - `__init__`
3. `aplicacion/modelos/usuario.py:23` - `__init__`
4. `aplicacion/servicios/servicio_gemini.py:15` - `__init__`

**Template de docstring:**

```python
def __init__(self, parametro1, parametro2=None):
    """
    Inicializa [nombre de la clase]
    
    Args:
        parametro1 (tipo): Descripción del parámetro
        parametro2 (tipo, opcional): Descripción. Por defecto None.
        
    Raises:
        ValueError: Si el parámetro no es válido
        TypeError: Si el tipo no es correcto
        
    Example:
        >>> instancia = MiClase('valor1', parametro2='valor2')
    """
```

---

### Día 4-5: Resolver TODOs Críticos (8 horas)

**TODOs prioritarios:**

1. `aplicacion/controladores/ia.py:220`
   ```python
   # TODO: Aquí implementaremos la consulta SQL para obtener datos del balance
   ```
   **Acción:** Implementar o crear issue específico

2. `aplicacion/servicios/servicio_consulta_integral.py:156`
   ```python
   # FIXME: Optimizar esta consulta, tarda mucho con grandes volúmenes
   ```
   **Acción:** Agregar índices o refactorizar query

3. Eliminar comentarios DEBUG temporales

---

### Semana 3: Optimización

#### Día 1-2: Eliminar Emojis (4 horas)

**Archivos afectados:**
- `aplicacion/prompts/proveedores_prompts.py:240`
- `aplicacion/prompts/balance_prompts.py:24`

**Reemplazo:**
```python
# ANTES
"⚠️ **ADVERTENCIA:**"

# DESPUÉS
"[ADVERTENCIA]"
```

#### Día 3-5: Refactoring Inicial (12 horas)

**Objetivo:** Reducir servicio_balance_ia.py

**Plan:**
1. Identificar funciones que pueden extraerse
2. Crear módulo `aplicacion/servicios/balance/`
3. Mover 3-4 funciones más grandes
4. Actualizar imports

---

## 📋 Checklist de Implementación

### Seguridad
- [ ] Validador de nombres de BD implementado
- [ ] ServicioConsultaIntegral actualizado
- [ ] Otros servicios actualizados
- [ ] Headers de seguridad agregados
- [ ] Rate limiting implementado
- [ ] Tests de seguridad creados
- [ ] Validación de subprocess revisada

### Testing
- [ ] pytest instalado
- [ ] Estructura de tests creada
- [ ] Tests de validadores implementados
- [ ] Cobertura > 30% (objetivo inicial)

### Calidad
- [ ] Context managers implementados
- [ ] Docstrings agregados
- [ ] TODOs críticos resueltos
- [ ] Emojis removidos
- [ ] Código comentado eliminado

---

## 🚀 Comandos Útiles

```bash
# Ejecutar tests
pytest -v

# Cobertura
pytest --cov=aplicacion --cov-report=html

# Buscar TODOs
grep -rn "TODO\|FIXME" aplicacion/

# Validar código
flake8 aplicacion/ --max-line-length=120

# Buscar imports no usados
autoflake --check --recursive aplicacion/

# Ver archivos modificados
git status

# Commit de cambios
git add .
git commit -m "tipo: descripción"
git push
```

---

## 📊 Métricas de Éxito

| Métrica | Antes | Objetivo | Después |
|---------|-------|----------|---------|
| Vulnerabilidades críticas | 1 | 0 | __ |
| Cobertura tests | 0% | 30% | __% |
| TODOs pendientes | 79 | <50 | __ |
| Funciones sin docstring | 27 | 0 | __ |
| Headers seguridad | No | Sí | __ |
| Rate limiting | No | Sí | __ |

---

## 🆘 Ayuda y Recursos

### Documentación
- **Análisis completo:** `/ANALISIS_CODIGO.md`
- **Seguridad:** `/documentacion/REPORTE_SEGURIDAD.md`
- **Métricas:** `/documentacion/METRICAS_CALIDAD.md`

### Contacto
- **Dudas técnicas:** [Slack #desarrollo]
- **Revisión de código:** [GitHub PR]
- **Seguridad:** security@evolve-soluciones.com

---

## ✅ Validación Final

Antes de considerar completo:

1. **Tests pasan:** `pytest` sin errores
2. **Linter limpio:** `flake8 aplicacion/` sin errores críticos
3. **Seguridad:** Vulnerabilidades críticas resueltas
4. **Documentación:** Archivos actualizados
5. **Code review:** PR revisado y aprobado

---

**Creado:** 2025-12-11  
**Mantenido por:** Equipo de Desarrollo  
**Última actualización:** 2025-12-11
