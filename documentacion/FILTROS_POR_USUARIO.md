# Guía de Filtros por Usuario

## Arquitectura de Permisos

### Cómo Funciona

```
PostgreSQL (auth)              MySQL (stratex/otras BDs)
├─ admin-stratex              ├─ empresas
│  └─ rol: administrador      │  ├─ auditor: "ALEXEI"  ← Usuario ve esta
├─ ALEXEI                     │  ├─ auditor: "JUAN"    ← Usuario NO ve
│  └─ rol: usuario           │  └─ auditor: "ALEXEI"  ← Usuario ve esta
└─ JUAN
   └─ rol: usuario

Regla:
- Admin: Ve TODAS las empresas
- Usuario normal: Ve solo donde empresas.auditor = usuario.nombre_usuario
```

## Uso en Controladores

### Ejemplo 1: Listar Empresas del Usuario

```python
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from aplicacion.utilidades.filtros_empresas import obtener_empresas_usuario

@app.route('/mis-empresas')
@login_required
def listar_empresas():
    """
    Muestra las empresas del usuario actual
    - Si es admin: muestra todas
    - Si es usuario normal: muestra solo donde auditor = nombre_usuario
    """
    empresas = obtener_empresas_usuario(current_user)
    
    return render_template('empresas.html', empresas=empresas)
```

### Ejemplo 2: Listar con Filtros Adicionales

```python
@app.route('/empresas-activas')
@login_required
def empresas_activas():
    """Muestra solo empresas activas del usuario"""
    empresas = obtener_empresas_usuario(
        current_user,
        campos="run_rut, empresa, auditor, correo",
        condiciones_extra="AND activo = 1"
    )
    
    return render_template('empresas.html', empresas=empresas)
```

### Ejemplo 3: Consulta Manual con Filtro

```python
from flask_login import current_user
from aplicacion.modelos.base_datos import obtener_conexion_local
from aplicacion.utilidades.filtros_empresas import construir_filtro_auditor
import pymysql

@app.route('/empresas-por-grupo/<grupo>')
@login_required
def empresas_por_grupo(grupo):
    """Muestra empresas de un grupo específico"""
    conexion = obtener_conexion_local()
    
    try:
        # Construir filtro base
        where_clause, params = construir_filtro_auditor(current_user)
        
        # Consulta base
        consulta = """
            SELECT run_rut, empresa, auditor, grupo
            FROM empresas
        """
        
        # Aplicar filtros
        if where_clause:
            # Usuario normal: WHERE auditor = 'ALEXEI' AND grupo = 'A'
            consulta += f" {where_clause} AND grupo = %s"
            params = params + (grupo,)
        else:
            # Admin: WHERE grupo = 'A'
            consulta += " WHERE grupo = %s"
            params = (grupo,)
        
        with conexion.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(consulta, params)
            empresas = cursor.fetchall()
        
        return render_template('empresas_grupo.html', 
                              empresas=empresas, 
                              grupo=grupo)
    finally:
        conexion.close()
```

### Ejemplo 4: Verificar Acceso a Empresa Específica

```python
from flask import flash, redirect, url_for
from aplicacion.utilidades.filtros_empresas import puede_acceder_empresa

@app.route('/empresa/<run_rut>/editar')
@login_required
def editar_empresa(run_rut):
    """Solo permite editar si el usuario tiene acceso"""
    
    # Verificar permiso
    if not puede_acceder_empresa(current_user, run_rut):
        flash('No tienes permisos para editar esta empresa', 'error')
        return redirect(url_for('listar_empresas'))
    
    # El usuario tiene acceso, continuar...
    empresa = obtener_empresa_por_rut(run_rut)
    return render_template('editar_empresa.html', empresa=empresa)
```

## Uso en Servicios

### Ejemplo: Servicio de Empresas

```python
# aplicacion/servicios/servicio_empresas.py

from aplicacion.utilidades.filtros_empresas import obtener_empresas_usuario, puede_acceder_empresa

class ServicioEmpresas:
    """Servicio para gestión de empresas con permisos"""
    
    @staticmethod
    def obtener_empresas_usuario(usuario, filtros=None):
        """
        Obtiene empresas según permisos del usuario
        
        Args:
            usuario: Usuario actual
            filtros: Dict con filtros adicionales {'grupo': 'A', 'activo': 1}
        """
        condiciones = []
        
        if filtros:
            if filtros.get('grupo'):
                condiciones.append(f"AND grupo = '{filtros['grupo']}'")
            if filtros.get('activo') is not None:
                condiciones.append(f"AND activo = {filtros['activo']}")
        
        condiciones_extra = " ".join(condiciones)
        
        return obtener_empresas_usuario(
            usuario,
            condiciones_extra=condiciones_extra
        )
    
    @staticmethod
    def actualizar_empresa(usuario, run_rut, datos):
        """Actualiza empresa solo si el usuario tiene acceso"""
        
        # Verificar permiso
        if not puede_acceder_empresa(usuario, run_rut):
            raise PermissionError(f"Usuario {usuario.nombre_usuario} no tiene acceso a empresa {run_rut}")
        
        # Continuar con actualización...
        from aplicacion.modelos.base_datos import obtener_conexion_local
        
        conexion = obtener_conexion_local()
        try:
            with conexion.cursor() as cursor:
                consulta = """
                    UPDATE empresas 
                    SET empresa = %s, correo = %s
                    WHERE run_rut = %s
                """
                cursor.execute(consulta, (datos['empresa'], datos['correo'], run_rut))
                conexion.commit()
                
            return True
        finally:
            conexion.close()
```

## Uso en Templates (Jinja2)

### Mostrar Lista de Empresas

```html
<!-- plantillas/paginas/empresas.html -->

{% extends "diseños/base.html" %}

{% block contenido %}
<div class="container">
    <h1>Mis Empresas</h1>
    
    {% if current_user.es_administrador() %}
        <div class="alert alert-info">
            <i class="fas fa-crown"></i>
            Viendo TODAS las empresas (modo administrador)
        </div>
    {% else %}
        <div class="alert alert-secondary">
            <i class="fas fa-user"></i>
            Viendo empresas asignadas a: {{ current_user.nombre_usuario }}
        </div>
    {% endif %}
    
    <table class="table">
        <thead>
            <tr>
                <th>RUT</th>
                <th>Empresa</th>
                <th>Auditor</th>
                <th>Acciones</th>
            </tr>
        </thead>
        <tbody>
            {% for empresa in empresas %}
            <tr>
                <td>{{ empresa.run_rut }}</td>
                <td>{{ empresa.empresa }}</td>
                <td>
                    <span class="badge bg-primary">{{ empresa.auditor }}</span>
                </td>
                <td>
                    <a href="{{ url_for('ver_empresa', run_rut=empresa.run_rut) }}" 
                       class="btn btn-sm btn-info">
                        Ver
                    </a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
```

## Crear Usuarios que Coincidan con Auditores

### Desde Script Python

```python
# scripts/crear_usuarios_desde_auditores.py

from aplicacion.modelos.usuario import Usuario
from aplicacion.modelos.base_datos import ejecutar_consulta

# Obtener auditores únicos de MySQL
consulta = "SELECT DISTINCT auditor FROM empresas WHERE auditor IS NOT NULL AND auditor != ''"
auditores = ejecutar_consulta(consulta)

for row in auditores:
    auditor = row['auditor']
    email = f"{auditor.lower()}@evolve.cl"
    
    try:
        usuario = Usuario.crear_usuario(
            nombre_usuario=auditor,
            email=email,
            contraseña="Cambiar123",  # Contraseña temporal
            rol="usuario"
        )
        print(f"✓ Usuario creado: {auditor}")
    except ValueError as e:
        print(f"✗ {auditor}: {e}")
```

### Crear Usuario Manualmente

```python
from aplicacion.modelos.usuario import Usuario

# Crear usuario ALEXEI (coincide con auditor en empresas)
usuario = Usuario.crear_usuario(
    nombre_usuario="ALEXEI",  # Debe coincidir EXACTAMENTE con columna auditor
    email="alexei@evolve.cl",
    contraseña="Alexei123",
    rol="usuario"
)
```

## Resumen de Funciones

| Función | Uso | Retorna |
|---------|-----|---------|
| `construir_filtro_auditor(usuario)` | Construir WHERE para consultas | `(where_clause, params)` |
| `construir_filtro_and_auditor(usuario)` | Agregar AND a consulta existente | `(and_clause, params)` |
| `obtener_empresas_usuario(usuario, ...)` | Obtener lista de empresas | `list` de empresas |
| `puede_acceder_empresa(usuario, rut)` | Verificar permiso | `bool` |

## Ventajas de Este Sistema

✅ **Simple**: Basado en columna `auditor` existente  
✅ **Seguro**: Filtros aplicados en servidor, no en cliente  
✅ **Flexible**: Admin ve todo, usuarios solo lo suyo  
✅ **Escalable**: Fácil agregar más reglas de negocio  
✅ **Sin cambios en BD**: Usa estructura actual  

## Próximos Pasos

1. Crear usuarios en PostgreSQL que coincidan con auditores en MySQL
2. Actualizar controladores para usar `obtener_empresas_usuario()`
3. Agregar verificación `puede_acceder_empresa()` en rutas de edición
4. Testear con diferentes usuarios
