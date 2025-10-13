# Arquitectura Completa del Sistema

## 🏗️ Arquitectura de Bases de Datos

### Diagrama

```
┌─────────────────────────────────────────────────────────────┐
│                  SISTEMA EVOLVE SOLUCIONES                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PostgreSQL (evolve_auth)                                   │
│  ┌──────────────────────────────────────────────┐          │
│  │ auth.usuarios                                │          │
│  ├──────────────────────────────────────────────┤          │
│  │ id: 1                                        │          │
│  │ nombre_usuario: "admin-stratex"              │          │
│  │ rol: "administrador"                         │          │
│  │ base_datos_mysql: "stratex" ────────────┐   │          │
│  └──────────────────────────────────────────┼───┘          │
│                                              │              │
│                                              ▼              │
│  MySQL (stratex)                                            │
│  ┌──────────────────────────────────────────────┐          │
│  │ empresas                                     │          │
│  ├──────────────────────────────────────────────┤          │
│  │ run_rut: "76244083-0"                       │          │
│  │ empresa: "Friser S.A"                       │          │
│  │ auditor: "ALEXEI" ◄── Filtro para usuarios  │          │
│  └──────────────────────────────────────────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

##  Reglas de Acceso

### Nivel 1: Base de Datos (campo `base_datos_mysql`)

Cada usuario tiene asignada una base de datos MySQL específica:

```
Usuario: "admin-stratex"
└─ base_datos_mysql: "stratex"
   └─ Se conecta SOLO a MySQL.stratex

Usuario: "admin-empresaX"
└─ base_datos_mysql: "empresa_x"
   └─ Se conecta SOLO a MySQL.empresa_x
```

### Nivel 2: Filtro por Auditor (campo `auditor`)

Dentro de su base de datos asignada:

**Si el usuario es Administrador:**
```sql
-- Ve TODAS las empresas de su BD
SELECT * FROM empresas;
```

**Si el usuario es Normal:**
```sql
-- Solo ve empresas donde auditor = su nombre_usuario
SELECT * FROM empresas WHERE auditor = 'ALEXEI';
```

## 🔄 Flujo Completo de Acceso

### Ejemplo 1: Usuario Admin

```python
# 1. Usuario hace login
usuario = Usuario.obtener_por_nombre_usuario("admin-stratex")
# usuario.base_datos_mysql = "stratex"
# usuario.rol = "administrador"

# 2. Usuario accede a /empresas
from aplicacion.utilidades.filtros_empresas import obtener_empresas_usuario

empresas = obtener_empresas_usuario(current_user)

# Internamente hace:
# conexion = obtener_conexion_local("stratex")  ← BD del usuario
# SELECT * FROM empresas  ← Sin filtro porque es admin
```

**Resultado:** Ve TODAS las empresas de la base de datos "stratex"

### Ejemplo 2: Usuario Normal

```python
# 1. Usuario hace login
usuario = Usuario.obtener_por_nombre_usuario("ALEXEI")
# usuario.base_datos_mysql = "stratex"
# usuario.rol = "usuario"

# 2. Usuario accede a /empresas
empresas = obtener_empresas_usuario(current_user)

# Internamente hace:
# conexion = obtener_conexion_local("stratex")  ← BD del usuario
# SELECT * FROM empresas WHERE auditor = 'ALEXEI'  ← Filtrado
```

**Resultado:** Solo ve empresas donde `auditor = "ALEXEI"` en la BD "stratex"

## 💻 Uso en Código

### Obtener Empresas del Usuario

```python
from flask import render_template
from flask_login import login_required, current_user
from aplicacion.utilidades.filtros_empresas import obtener_empresas_usuario

@app.route('/empresas')
@login_required
def listar_empresas():
    """
    Automáticamente:
    1. Conecta a la BD del usuario (current_user.base_datos_mysql)
    2. Filtra por auditor si no es admin
    """
    empresas = obtener_empresas_usuario(current_user)

    return render_template('empresas.html', empresas=empresas)
```

### Verificar Permiso sobre Empresa

```python
from aplicacion.utilidades.filtros_empresas import puede_acceder_empresa

@app.route('/empresa/<run_rut>/editar')
@login_required
def editar_empresa(run_rut):
    """
    Verifica:
    1. La empresa existe en la BD del usuario
    2. Si no es admin, verifica que auditor = nombre_usuario
    """
    if not puede_acceder_empresa(current_user, run_rut):
        flash('No tienes permisos', 'error')
        return redirect(url_for('listar_empresas'))

    # Usuario tiene acceso, continuar...
    return render_template('editar_empresa.html')
```

### Consulta Manual

```python
from aplicacion.modelos.base_datos import obtener_conexion_local
from aplicacion.utilidades.filtros_empresas import construir_filtro_auditor

@app.route('/empresas/activas')
@login_required
def empresas_activas():
    # Conectar a la BD del usuario
    base_datos = current_user.base_datos_mysql
    conexion = obtener_conexion_local(base_datos)

    # Construir filtro según rol
    where_clause, params = construir_filtro_auditor(current_user)

    consulta = f"""
        SELECT run_rut, empresa, auditor
        FROM empresas
        {where_clause}
        AND activo = 1
    """

    with conexion.cursor() as cursor:
        cursor.execute(consulta, params if params else ())
        empresas = cursor.fetchall()

    conexion.close()
    return render_template('empresas.html', empresas=empresas)
```

## 🔧 Configuración de Usuarios

### Crear Usuario Admin (ve todo en su BD)

```python
from aplicacion.modelos.usuario import Usuario

admin = Usuario.crear_usuario(
    nombre_usuario="admin-stratex",
    email="admin@stratex.cl",
    contraseña="Admin123456",
    rol="administrador",
    base_datos_mysql="stratex"  # ← BD asignada
)
```

### Crear Usuario Normal (solo ve sus empresas)

```python
usuario = Usuario.crear_usuario(
    nombre_usuario="ALEXEI",  # ← Debe coincidir con campo 'auditor'
    email="alexei@stratex.cl",
    contraseña="Alexei123",
    rol="usuario",
    base_datos_mysql="stratex"  # ← Misma BD que admin
)
```

##  Tabla de Permisos

| Usuario | BD MySQL | Rol | Ve Empresas |
|---------|----------|-----|-------------|
| admin-stratex | stratex | administrador | TODAS en stratex |
| ALEXEI | stratex | usuario | Solo donde auditor='ALEXEI' en stratex |
| JUAN | stratex | usuario | Solo donde auditor='JUAN' en stratex |
| admin-empresaX | empresa_x | administrador | TODAS en empresa_x |

##  Ventajas de esta Arquitectura

 **Seguridad:** Cada usuario solo ve su BD y sus datos
 **Escalabilidad:** Fácil agregar nuevas BDs y usuarios
 **Flexibilidad:** Admin ve todo, usuarios solo lo suyo
 **Aislamiento:** Datos de diferentes empresas completamente separados
 **Simple:** Basado en campos existentes (base_datos_mysql, auditor)

## 🔐 Seguridad

### Validaciones Automáticas

1. **Conexión a BD:** Solo puede conectarse a SU base_datos_mysql
2. **Filtro por Auditor:** Usuarios normales solo ven WHERE auditor = nombre_usuario
3. **Verificación de Acceso:** puede_acceder_empresa() valida ambos niveles

### Ejemplo de Ataque Bloqueado

```python
# Usuario malicioso intenta:
empresas = obtener_empresas_usuario(
    usuario_alexei,  # base_datos_mysql = "stratex"
    conexion=obtener_conexion_local("empresa_x")  # Intenta otra BD
)

# BLOQUEADO: La función usa la BD del usuario, ignora conexión externa
#  Resultado: Solo ve empresas de "stratex"
```

## 📚 Archivos Clave

- `aplicacion/modelos/usuario.py` - Modelo con base_datos_mysql
- `aplicacion/modelos/base_datos.py` - Función obtener_conexion_local(nombre_bd)
- `aplicacion/utilidades/filtros_empresas.py` - Lógica de filtros
- `documentacion/FILTROS_POR_USUARIO.md` - Guía de uso
