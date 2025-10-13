# Sistema de Módulos por Base de Datos

## Descripción General

Sistema de habilitación de módulos/funcionalidades por base de datos MySQL (multi-tenant), permitiendo control granular de qué features están disponibles para cada cliente sin necesidad de Foreign Keys entre PostgreSQL y MySQL.

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                  EVOLVE SOLUCIONES                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PostgreSQL (auth) - Configuración y Permisos               │
│  ┌──────────────────────────────────────────────┐          │
│  │ 1. modulos_sistema (catálogo)                │          │
│  │    ├─ consulta_f29                           │          │
│  │    ├─ consolidado                            │          │
│  │    ├─ tareas                                 │          │
│  │    └─ ...                                    │          │
│  │                                              │          │
│  │ 2. bases_datos_mysql (registro)              │          │
│  │    ├─ stratex → Cliente A                    │          │
│  │    ├─ evolve → Cliente B                     │          │
│  │    └─ empresa_x → Cliente C                  │          │
│  │                                              │          │
│  │ 3. modulos_habilitados_bd (configuración)    │          │
│  │    ├─ stratex: [consulta_f29, consolidado]   │          │
│  │    ├─ evolve: [consulta_f29]                 │          │
│  │    └─ empresa_x: [tareas, proveedores]       │          │
│  └──────────────────────────────────────────────┘          │
│                          │                                  │
│                          ▼                                  │
│  MySQL (múltiples instancias) - Datos de Clientes          │
│  ┌──────────────────────────────────────────────┐          │
│  │ stratex/  evolve/  empresa_x/                │          │
│  │ └─ empresas, f29, consolidados, etc.         │          │
│  └──────────────────────────────────────────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Características Principales

- **Sin Foreign Keys entre PostgreSQL y MySQL**: Validación en código Python
- **Registro descriptivo**: Catálogo de BDs MySQL en PostgreSQL
- **Flexible**: Agregar/quitar módulos sin modificar BD
- **Multi-tenant**: Diferentes features por cliente
- **Auditable**: Historial de habilitaciones/deshabilitaciones

---

## Instalación

### 1. Ejecutar Migración SQL

```bash
# Conectarse a PostgreSQL
psql -U postgres -d evolve_auth

# Ejecutar migración
\i migraciones/003_sistema_modulos_por_bd.sql
```

### 2. Verificar Tablas Creadas

```sql
-- Verificar que las tablas existan
SELECT tablename FROM pg_tables
WHERE schemaname = 'auth'
  AND tablename LIKE 'modulos%';

-- Resultado esperado:
-- modulos_sistema
-- modulos_habilitados_bd
```

### 3. Verificar Datos Iniciales

```sql
-- Ver módulos registrados
SELECT codigo, nombre, requiere_licencia
FROM auth.modulos_sistema
ORDER BY orden_menu;

-- Ver bases de datos registradas
SELECT nombre_base_datos, nombre_cliente, estado
FROM auth.bases_datos_mysql;

-- Ver módulos habilitados por BD
SELECT * FROM auth.vista_modulos_habilitados;
```

---

## Uso en Código

### 1. Proteger Rutas con Decorador

```python
# aplicacion/controladores/consulta_integral_f29.py

from flask import Blueprint, render_template
from flask_login import login_required
from aplicacion.utilidades.decoradores import requiere_modulo

consulta_bp = Blueprint('consulta_f29', __name__)

@consulta_bp.route('/consulta-f29')
@login_required
@requiere_modulo('consulta_f29')  # ← Verificación automática
def vista_consulta():
    """
    Si el usuario intenta acceder y el módulo NO está habilitado
    para su BD, será redirigido con mensaje de error
    """
    return render_template('consulta_integral_f29.html')
```

### 2. Verificación Manual en Controladores

```python
from aplicacion.modelos.modulo import Modulo

@app.route('/dashboard')
@login_required
def dashboard():
    base_datos = current_user.base_datos_mysql

    # Verificar módulos habilitados
    tiene_consolidado = Modulo.verificar_modulo_habilitado(base_datos, 'consolidado')
    tiene_ia = Modulo.verificar_modulo_habilitado(base_datos, 'ia')

    return render_template('dashboard.html',
                          tiene_consolidado=tiene_consolidado,
                          tiene_ia=tiene_ia)
```

### 3. Mostrar Menú Dinámico en Templates

```python
# aplicacion.py - Context Processor

from aplicacion.modelos.modulo import Modulo

@aplicacion.context_processor
def inyectar_modulos_disponibles():
    """
    Hace disponibles los módulos habilitados en todos los templates
    """
    if current_user.is_authenticated:
        base_datos = current_user.base_datos_mysql
        modulos = Modulo.obtener_modulos_habilitados_bd(base_datos)
    else:
        modulos = []

    return dict(modulos_disponibles=modulos)
```

```html
<!-- aplicacion/plantillas/componentes/navbar.html -->
<nav class="navbar">
    <ul class="nav">
        {% for modulo in modulos_disponibles %}
        <li class="nav-item">
            <a href="/{{ current_user.base_datos_mysql }}{{ modulo.url_base }}"
               class="nav-link">
                <i class="bi bi-{{ modulo.icono }}"></i>
                {{ modulo.nombre }}
                {% if modulo.requiere_licencia %}
                <span class="badge bg-warning">PRO</span>
                {% endif %}
            </a>
        </li>
        {% endfor %}
    </ul>
</nav>
```

### 4. Lógica Condicional en Servicios

```python
# aplicacion/servicios/servicio_dashboard.py

from aplicacion.modelos.modulo import Modulo

class ServicioDashboard:
    def obtener_widgets(self, base_datos):
        """
        Retorna widgets según módulos habilitados
        """
        widgets = []

        # Widget básico (siempre disponible)
        widgets.append({'tipo': 'resumen_empresas'})

        # Widget condicional
        if Modulo.verificar_modulo_habilitado(base_datos, 'consolidado'):
            widgets.append({'tipo': 'consolidado_mensual'})

        if Modulo.verificar_modulo_habilitado(base_datos, 'tareas'):
            widgets.append({'tipo': 'tareas_pendientes'})

        if Modulo.verificar_modulo_habilitado(base_datos, 'ia'):
            widgets.append({'tipo': 'predicciones_ia'})

        return widgets
```

---

## Gestión de Módulos

### Habilitar Módulo para una BD

```python
from aplicacion.modelos.modulo import GestorModulos

# Habilitar módulo
GestorModulos.habilitar_modulo(
    nombre_base_datos='empresa_x',
    codigo_modulo='consolidado',
    usuario='admin'  # Opcional: quién lo habilitó
)
```

```sql
-- O directamente en SQL
INSERT INTO auth.modulos_habilitados_bd (id_base_datos, id_modulo, habilitado)
SELECT
    bd.id,
    m.id,
    TRUE
FROM auth.bases_datos_mysql bd, auth.modulos_sistema m
WHERE bd.nombre_base_datos = 'empresa_x'
  AND m.codigo = 'consolidado'
ON CONFLICT (id_base_datos, id_modulo)
DO UPDATE SET habilitado = TRUE;
```

### Deshabilitar Módulo

```python
from aplicacion.modelos.modulo import GestorModulos

# Deshabilitar módulo (mantiene historial)
GestorModulos.deshabilitar_modulo('empresa_x', 'consolidado')
```

```sql
-- O en SQL
UPDATE auth.modulos_habilitados_bd mh
SET habilitado = FALSE,
    fecha_deshabilitacion = CURRENT_TIMESTAMP
FROM auth.bases_datos_mysql bd, auth.modulos_sistema m
WHERE mh.id_base_datos = bd.id
  AND mh.id_modulo = m.id
  AND bd.nombre_base_datos = 'empresa_x'
  AND m.codigo = 'consolidado';
```

### Consultar Resumen de Módulos

```python
from aplicacion.modelos.modulo import GestorModulos

resumen = GestorModulos.obtener_resumen_modulos_bd('stratex')
print(f"Total módulos sistema: {resumen['total_modulos_sistema']}")
print(f"Módulos habilitados: {resumen['total_modulos_habilitados']}")
print(f"Módulos disponibles para habilitar: {len(resumen['modulos_disponibles'])}")
```

---

## Agregar Nueva Base de Datos

### 1. Registrar la BD

```sql
INSERT INTO auth.bases_datos_mysql
    (nombre_base_datos, nombre_cliente, estado, plan, fecha_contratacion)
VALUES
    ('nueva_empresa', 'Nueva Empresa S.A.', 'activo', 'basico', CURRENT_DATE);
```

### 2. Habilitar Módulos Básicos

```sql
-- Plan Básico: solo inicio y consulta F29
INSERT INTO auth.modulos_habilitados_bd (id_base_datos, id_modulo, habilitado)
SELECT
    bd.id,
    m.id,
    TRUE
FROM auth.bases_datos_mysql bd
CROSS JOIN auth.modulos_sistema m
WHERE bd.nombre_base_datos = 'nueva_empresa'
  AND m.codigo IN ('inicio', 'consulta_f29')
ON CONFLICT DO NOTHING;
```

### 3. Crear Usuario para la BD

```python
from aplicacion.modelos.usuario import Usuario

# Crear usuario asignado a la nueva BD
Usuario.crear_usuario(
    nombre_usuario='admin_nueva',
    email='admin@nuevaempresa.cl',
    contraseña='password123',
    rol='administrador',
    base_datos_mysql='nueva_empresa'  # ← BD asignada
)
```

---

## Planes de Servicio

### Ejemplos de Configuración por Plan

#### Plan Básico
```python
modulos_basico = ['inicio', 'consulta_f29', 'observaciones']
```

#### Plan Pro
```python
modulos_pro = ['inicio', 'consulta_f29', 'consolidado',
               'tareas', 'observaciones', 'reportes']
```

#### Plan Enterprise
```python
modulos_enterprise = ['inicio', 'consulta_f29', 'consolidado',
                      'tareas', 'observaciones', 'proveedores',
                      'email', 'ia', 'reportes']
```

### Script de Configuración por Plan

```python
# scripts/configurar_plan.py

from aplicacion.modelos.modulo import GestorModulos

PLANES = {
    'basico': ['inicio', 'consulta_f29', 'observaciones'],
    'pro': ['inicio', 'consulta_f29', 'consolidado', 'tareas',
            'observaciones', 'reportes'],
    'enterprise': ['inicio', 'consulta_f29', 'consolidado', 'tareas',
                   'observaciones', 'proveedores', 'email', 'ia', 'reportes']
}

def configurar_plan(nombre_bd, plan):
    """Configura módulos según plan contratado"""
    modulos = PLANES.get(plan, PLANES['basico'])

    for codigo_modulo in modulos:
        GestorModulos.habilitar_modulo(nombre_bd, codigo_modulo, 'admin')

    print(f"Plan '{plan}' configurado para {nombre_bd}")
    print(f"Módulos habilitados: {len(modulos)}")
```

---

## Consultas Útiles

### Ver Módulos por BD

```sql
SELECT * FROM auth.vista_modulos_habilitados
WHERE nombre_base_datos = 'stratex';
```

### BDs sin Módulos Habilitados

```sql
SELECT bd.nombre_base_datos, bd.nombre_cliente
FROM auth.bases_datos_mysql bd
LEFT JOIN auth.modulos_habilitados_bd mh ON bd.id = mh.id_base_datos
WHERE mh.id IS NULL
  AND bd.activo = TRUE;
```

### Módulos Más Populares

```sql
SELECT
    m.nombre,
    COUNT(mh.id) as total_bds_con_modulo
FROM auth.modulos_sistema m
LEFT JOIN auth.modulos_habilitados_bd mh ON m.id = mh.id_modulo AND mh.habilitado = TRUE
GROUP BY m.id, m.nombre
ORDER BY total_bds_con_modulo DESC;
```

---

## Testing

### Test de Verificación de Módulo

```python
# pruebas/test_modulos.py

from aplicacion.modelos.modulo import Modulo

def test_modulo_habilitado_stratex():
    # stratex tiene consulta_f29 habilitado
    assert Modulo.verificar_modulo_habilitado('stratex', 'consulta_f29') == True

def test_modulo_no_habilitado():
    # evolve NO tiene ia habilitado
    assert Modulo.verificar_modulo_habilitado('evolve', 'ia') == False

def test_bd_inexistente():
    # BD que no existe
    assert Modulo.verificar_modulo_habilitado('bd_inexistente', 'consulta_f29') == False
```

---

## Solución de Problemas

### Error: FK de usuarios a bases_datos_mysql

**Problema**: Error al intentar crear usuario con BD que no está registrada.

**Solución**: NO usar Foreign Key. La validación se hace en código Python:

```python
from aplicacion.modelos.modulo import BaseDatosMySQL

def validar_base_datos_usuario(nombre_bd):
    """Validar antes de asignar a usuario"""
    if not BaseDatosMySQL.validar_existe(nombre_bd):
        raise ValueError(f"La base de datos '{nombre_bd}' no está registrada")
    return True
```

### Usuario no ve módulos en el menú

**Verificar**:
1. ¿El usuario está autenticado?
2. ¿Tiene `base_datos_mysql` asignada?
3. ¿La BD está registrada en `auth.bases_datos_mysql`?
4. ¿Los módulos están habilitados en `auth.modulos_habilitados_bd`?

```sql
-- Query diagnóstico
SELECT
    u.nombre_usuario,
    u.base_datos_mysql,
    bd.nombre_cliente,
    bd.estado,
    COUNT(mh.id) as modulos_habilitados
FROM auth.usuarios u
LEFT JOIN auth.bases_datos_mysql bd ON u.base_datos_mysql = bd.nombre_base_datos
LEFT JOIN auth.modulos_habilitados_bd mh ON bd.id = mh.id_base_datos AND mh.habilitado = TRUE
WHERE u.nombre_usuario = 'nombre_usuario_aqui'
GROUP BY u.nombre_usuario, u.base_datos_mysql, bd.nombre_cliente, bd.estado;
```

---

## Migración desde Sistema Anterior

Si ya tienes usuarios con `base_datos_mysql` asignadas:

```sql
-- 1. Registrar todas las BDs únicas de usuarios
INSERT INTO auth.bases_datos_mysql (nombre_base_datos, nombre_cliente, estado)
SELECT DISTINCT
    base_datos_mysql,
    CONCAT('Cliente ', base_datos_mysql),
    'activo'
FROM auth.usuarios
WHERE base_datos_mysql IS NOT NULL
  AND base_datos_mysql != ''
ON CONFLICT (nombre_base_datos) DO NOTHING;

-- 2. Habilitar módulos básicos para todas
INSERT INTO auth.modulos_habilitados_bd (id_base_datos, id_modulo, habilitado)
SELECT
    bd.id,
    m.id,
    TRUE
FROM auth.bases_datos_mysql bd
CROSS JOIN auth.modulos_sistema m
WHERE m.codigo IN ('inicio', 'consulta_f29', 'observaciones')
ON CONFLICT DO NOTHING;
```

---

## Próximos Pasos

1. **Interfaz de Administración**: Crear panel web para gestionar módulos
2. **API REST**: Endpoints para consultar/modificar habilitaciones
3. **Webhooks**: Notificar cuando se habilita/deshabilita módulo
4. **Facturación**: Integrar con sistema de billing según módulos activos
5. **Analytics**: Dashboard de uso de módulos por cliente

---

## Referencias

- **Migración SQL**: `migraciones/003_sistema_modulos_por_bd.sql`
- **Modelo Python**: `aplicacion/modelos/modulo.py`
- **Decorador**: `aplicacion/utilidades/decoradores.py::requiere_modulo`
- **Documentación Arquitectura**: `documentacion/ARQUITECTURA_COMPLETA.md`
