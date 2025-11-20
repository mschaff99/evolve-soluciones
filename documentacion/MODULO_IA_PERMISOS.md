# Sistema de Permisos - Módulo IA

## 📋 Descripción General

El módulo de IA (Inteligencia Artificial) ahora cuenta con un sistema de permisos granular basado en la base de datos MySQL del usuario. Esto permite controlar qué clientes/empresas tienen acceso a las funcionalidades de análisis inteligente con Gemini AI.

## 🔐 Características

-  **Control por Base de Datos**: Cada BD MySQL puede tener el módulo IA habilitado/deshabilitado
-  **Validación en Backend**: Decorador `@requiere_modulo('ia')` protege todas las rutas
-  **UI Dinámica**: Los elementos de interfaz se muestran/ocultan según permisos
-  **Gestión Flexible**: Scripts y funciones SQL para administrar permisos
-  **Auditoría**: Registro de fechas de habilitación/deshabilitación

## 📦 Instalación

### 1. Ejecutar Migración SQL

```powershell
# Conectarse a PostgreSQL
psql -U postgres -d evolve_auth

# Ejecutar migración
\i migraciones/008_habilitar_modulo_ia.sql
```

La migración realiza:
- Registra/actualiza el módulo IA en el catálogo
- Habilita el módulo para las BDs `stratex` y `evolve`
- Crea función `auth.toggle_modulo_ia()` para gestión fácil

### 2. Verificar Instalación

```sql
-- Ver bases de datos con IA habilitado
SELECT * FROM auth.vista_modulos_habilitados
WHERE codigo_modulo = 'ia'
  AND habilitado = TRUE;
```

## 🚀 Uso

### Desde la Aplicación Web

Los usuarios verán el módulo IA en el dashboard **solo si su base de datos tiene el módulo habilitado**:

-  **Con permisos**: Botón "Agente IA" activo con badge "PRO"
- ❌ **Sin permisos**: Botón deshabilitado con badge "No disponible"

Si intentan acceder directamente a `/ia/dashboard` sin permisos:
- **Interfaz web**: Redirección a inicio con mensaje de error
- **API/AJAX**: Respuesta 403 con JSON de error

### Desde Scripts Python

```python
from aplicacion.modelos.modulo import Modulo

# Verificar si una BD tiene acceso
tiene_ia = Modulo.verificar_modulo_habilitado('nombre_bd', 'ia')

if tiene_ia:
    print("Esta BD puede usar IA")
else:
    print("Esta BD NO tiene acceso a IA")
```

### Script de Gestión

Usar el script `gestionar_modulo_ia.py`:

```powershell
# Ver todas las BDs y su estado de IA
python scripts/gestionar_modulo_ia.py listar

# Habilitar IA para una BD
python scripts/gestionar_modulo_ia.py habilitar mi_empresa

# Deshabilitar IA
python scripts/gestionar_modulo_ia.py deshabilitar mi_empresa

# Ver ayuda
python scripts/gestionar_modulo_ia.py ayuda
```

### Gestión desde SQL

```sql
-- Habilitar módulo IA para una BD
SELECT auth.toggle_modulo_ia('nombre_bd', TRUE);

-- Deshabilitar módulo IA
SELECT auth.toggle_modulo_ia('nombre_bd', FALSE);

-- Ver usuarios con acceso a IA
SELECT DISTINCT
    u.nombre_usuario,
    u.email,
    u.base_datos_mysql,
    bd.nombre_cliente
FROM auth.usuarios u
INNER JOIN auth.bases_datos_mysql bd ON u.base_datos_mysql = bd.nombre_base_datos
INNER JOIN auth.modulos_habilitados_bd mh ON bd.id = mh.id_base_datos
INNER JOIN auth.modulos_sistema m ON mh.id_modulo = m.id
WHERE m.codigo = 'ia'
  AND mh.habilitado = TRUE
  AND u.activo = TRUE;
```

## 🔧 Configuración por Plan

Se recomienda habilitar el módulo IA según el plan contratado:

### Plan Básico
❌ No incluye módulo IA

### Plan Pro
⚠️ Opcional (según negociación)

### Plan Enterprise
 Incluye módulo IA por defecto

### Ejemplo de Configuración

```sql
-- Habilitar IA para todos los clientes Enterprise
UPDATE auth.modulos_habilitados_bd mh
SET habilitado = TRUE,
    fecha_habilitacion = CURRENT_TIMESTAMP
FROM auth.bases_datos_mysql bd,
     auth.modulos_sistema m
WHERE mh.id_base_datos = bd.id
  AND mh.id_modulo = m.id
  AND m.codigo = 'ia'
  AND bd.plan = 'enterprise'
  AND bd.activo = TRUE;
```

## 📝 Arquitectura Técnica

### Flujo de Validación

```
1. Usuario intenta acceder a /ia/dashboard
2. Flask ejecuta decoradores en orden:
   - @login_required (verifica autenticación)
   - @requiere_modulo('ia') (verifica permisos)
3. El decorador consulta PostgreSQL:
   - Obtiene base_datos_mysql del usuario
   - Verifica en auth.modulos_habilitados_bd
4. Resultado:
   -  Permitido: Ejecuta la función
   - ❌ Denegado: Redirige o devuelve 403
```

### Base de Datos

**Tablas involucradas** (PostgreSQL):
- `auth.modulos_sistema`: Catálogo de módulos
- `auth.bases_datos_mysql`: Registro de bases de datos
- `auth.modulos_habilitados_bd`: Permisos por BD
- `auth.usuarios`: Usuarios con BD asignada

**Vista útil**:
- `auth.vista_modulos_habilitados`: Vista consolidada

### Decoradores en Código

```python
# aplicacion/controladores/ia.py

from flask_login import login_required
from aplicacion.utilidades.decoradores import requiere_modulo

@ia_bp.route('/dashboard')
@login_required
@requiere_modulo('ia')  # ← Valida permisos
def dashboard_ia():
    # Solo se ejecuta si el usuario tiene permisos
    return render_template('ia_dashboard.html')
```

### Context Processor

```python
# aplicacion.py

@aplicacion.context_processor
def inyectar_modulos_disponibles():
    """Inyecta módulos habilitados en todos los templates"""
    if current_user.is_authenticated:
        base_datos = current_user.base_datos_mysql
        modulos = Modulo.obtener_modulos_habilitados_bd(base_datos)
        tiene_ia = Modulo.verificar_modulo_habilitado(base_datos, 'ia')
    else:
        modulos = []
        tiene_ia = False

    return dict(
        modulos_disponibles=modulos,
        tiene_modulo_ia=tiene_ia
    )
```

### Template Condicional

```html
<!-- aplicacion/plantillas/paginas/inicio.html -->

{% if tiene_modulo_ia %}
    <a href="/ia/dashboard">Agente IA</a>
{% else %}
    <div class="disabled">Agente IA (No disponible)</div>
{% endif %}
```

## 🧪 Testing

### Prueba Manual

1. **Crear usuario de prueba sin IA**:
```sql
-- Crear BD sin IA
INSERT INTO auth.bases_datos_mysql (nombre_base_datos, nombre_cliente, estado)
VALUES ('empresa_test', 'Empresa Test S.A.', 'activo');

-- NO habilitar el módulo IA (por defecto está deshabilitado)
```

2. **Crear usuario asignado a esa BD**:
```python
python scripts/crear_admin_simple.py
# Asignar base_datos_mysql = 'empresa_test'
```

3. **Probar acceso**:
   - Inicia sesión con el usuario
   - El botón "Agente IA" debe aparecer deshabilitado
   - Intentar acceder a `/ia/dashboard` debe redirigir con error

4. **Habilitar IA y verificar**:
```powershell
python scripts/gestionar_modulo_ia.py habilitar empresa_test
```
   - Refrescar página
   - El botón ahora debe estar activo

### Prueba Automatizada

```python
# pruebas/test_permisos_ia.py

def test_sin_permisos_ia(client, usuario_sin_ia):
    """Usuario sin permisos NO puede acceder al módulo IA"""
    response = client.get('/ia/dashboard')
    assert response.status_code == 302  # Redirección

def test_con_permisos_ia(client, usuario_con_ia):
    """Usuario con permisos SÍ puede acceder al módulo IA"""
    response = client.get('/ia/dashboard')
    assert response.status_code == 200
```

## 📊 Monitoreo y Estadísticas

### Consulta: Uso del Módulo IA

```sql
SELECT
    bd.nombre_cliente,
    bd.plan,
    COUNT(DISTINCT u.id) as total_usuarios,
    mh.fecha_habilitacion::DATE as desde
FROM auth.bases_datos_mysql bd
INNER JOIN auth.modulos_habilitados_bd mh ON bd.id = mh.id_base_datos
INNER JOIN auth.modulos_sistema m ON mh.id_modulo = m.id
LEFT JOIN auth.usuarios u ON u.base_datos_mysql = bd.nombre_base_datos
WHERE m.codigo = 'ia'
  AND mh.habilitado = TRUE
  AND bd.activo = TRUE
GROUP BY bd.nombre_cliente, bd.plan, mh.fecha_habilitacion
ORDER BY bd.nombre_cliente;
```

## 🔒 Seguridad

### Validación Múltiple

1. **Decorador en Backend**: `@requiere_modulo('ia')`
2. **Consulta a PostgreSQL**: Verificación en base de datos
3. **UI Condicional**: Elementos ocultos si no hay permisos
4. **Respuestas Diferenciadas**:
   - Web: Redirect con mensaje
   - API: JSON 403

### Bypass NO es Posible

Incluso si un usuario intenta:
- Modificar HTML del cliente
- Llamar directamente a la API
- Manipular cookies o sesión

**El servidor validará los permisos** antes de ejecutar cualquier función.

## 📚 Referencias

- **Migración SQL**: `migraciones/008_habilitar_modulo_ia.sql`
- **Script de gestión**: `scripts/gestionar_modulo_ia.py`
- **Modelo Python**: `aplicacion/modelos/modulo.py`
- **Decorador**: `aplicacion/utilidades/decoradores.py::requiere_modulo`
- **Controlador IA**: `aplicacion/controladores/ia.py`
- **Sistema de módulos**: `documentacion/SISTEMA_MODULOS_POR_BD.md`

## 💡 Preguntas Frecuentes

### ¿Cómo habilito IA para un cliente nuevo?

```powershell
python scripts/gestionar_modulo_ia.py habilitar nombre_bd
```

### ¿Los cambios requieren reiniciar la aplicación?

No, los cambios son inmediatos. La validación se hace en cada request.

### ¿Puedo habilitar IA masivamente para todas las BDs?

Sí, ejecuta en PostgreSQL:
```sql
\i migraciones/008_habilitar_modulo_ia.sql
-- Descomentar la sección "HABILITAR PARA TODAS LAS BDs ACTIVAS"
```

### ¿Cómo audito quién tiene acceso a IA?

```powershell
python scripts/gestionar_modulo_ia.py listar
```

### ¿Qué pasa si deshabilito IA para un cliente que lo está usando?

- Sus sesiones activas continuarán hasta que refresquen
- Al refrescar o hacer un nuevo request, serán bloqueados
- Los análisis guardados permanecen en la BD (no se eliminan)

## 🆘 Soporte

Si tienes problemas:

1. Verificar que la migración se ejecutó correctamente
2. Consultar logs de la aplicación
3. Ejecutar: `python scripts/gestionar_modulo_ia.py listar`
4. Verificar en PostgreSQL directamente

Para más información, consultar `documentacion/SISTEMA_MODULOS_POR_BD.md`
