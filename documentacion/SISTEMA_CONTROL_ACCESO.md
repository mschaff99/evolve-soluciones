# Sistema de Control de Acceso Multi-Nivel

##  Descripción General

El sistema implementa **doble validación de autenticación**:

1. **PostgreSQL (auth)**: Credenciales y datos de usuario
2. **MySQL (por base de datos)**: Permisos, auditor asignado y tipo de usuario

## 🔐 Flujo de Autenticación

```
┌─────────────────┐
│ Usuario ingresa │
│  credenciales   │
└────────┬────────┘
         │
         ▼
┌──────────────────────────┐
│ PASO 1: PostgreSQL       │
│ - Verifica usuario       │
│ - Verifica contraseña    │
│ - Verifica activo        │
│ - Obtiene base_datos_mysql│
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ PASO 2: MySQL            │
│ - Busca en usuarios_acceso│
│ - Verifica estado = 'V'  │
│ - Obtiene auditor        │
│ - Obtiene tipo_usuario   │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ Login exitoso            │
│ - Crea sesión            │
│ - Guarda auditor         │
│ - Guarda tipo_usuario    │
└──────────────────────────┘
```

## 📊 Estructura de Tabla MySQL

### `usuarios_acceso`

| Campo              | Tipo                    | Descripción                              |
|--------------------|-------------------------|------------------------------------------|
| usuario            | VARCHAR(50) PK          | Nombre de usuario (debe coincidir con PostgreSQL) |
| auditor            | VARCHAR(100) NOT NULL   | Nombre del auditor asignado              |
| tipo_usuario       | ENUM('admin','usuario') | Tipo de permiso del usuario              |
| estado             | CHAR(1) NOT NULL        | 'V' = Vigente, 'I' = Inactivo           |
| fecha_creacion     | DATETIME                | Fecha de creación del registro           |
| fecha_modificacion | DATETIME                | Última modificación                      |

## 🚀 Instalación

### 1. Ejecutar Migración en Cada Base de Datos

```bash
# Para stratex
mysql -u root -p stratex < migraciones/005_usuarios_por_base_datos.sql

# Para evolve
mysql -u root -p evolve < migraciones/005_usuarios_por_base_datos.sql
```

### 2. Si Ya Existe la Tabla (Actualización)

```bash
# Agregar columna tipo_usuario a tabla existente
mysql -u root -p stratex < migraciones/005b_agregar_tipo_usuario.sql
mysql -u root -p evolve < migraciones/005b_agregar_tipo_usuario.sql
```

## 📝 Gestión de Usuarios

### Agregar Usuario Normal

```sql
INSERT INTO usuarios_acceso (usuario, auditor, tipo_usuario, estado)
VALUES ('juan.perez', 'auditor_juan', 'usuario', 'V');
```

### Agregar Administrador

```sql
INSERT INTO usuarios_acceso (usuario, auditor, tipo_usuario, estado)
VALUES ('admin-stratex', 'admin', 'admin', 'V');
```

### Actualizar Usuarios Existentes

```sql
-- Actualizar tipo de usuario (ejemplo tus usuarios actuales)
UPDATE usuarios_acceso SET tipo_usuario = 'admin' WHERE usuario = 'admin-stratex';
UPDATE usuarios_acceso SET tipo_usuario = 'admin' WHERE usuario = 'PILAR';
UPDATE usuarios_acceso SET tipo_usuario = 'usuario' WHERE usuario = 'mschaff';
```

### Desactivar Usuario Temporalmente

```sql
UPDATE usuarios_acceso SET estado = 'I' WHERE usuario = 'juan.perez';
```

### Reactivar Usuario

```sql
UPDATE usuarios_acceso SET estado = 'V' WHERE usuario = 'juan.perez';
```

### Cambiar Auditor Asignado

```sql
UPDATE usuarios_acceso SET auditor = 'nuevo_auditor' WHERE usuario = 'juan.perez';
```

## 🛡️ Decoradores Disponibles

### `@login_required`
Verifica que el usuario esté autenticado (Flask-Login estándar).

```python
@app.route('/ruta')
@login_required
def mi_vista():
    return "Contenido protegido"
```

### `@requiere_modulo('nombre_modulo')`
Verifica que el módulo esté habilitado para la base de datos.

```python
@app.route('/<base_datos>/empresas')
@login_required
@requiere_modulo('empresas')
def listar_empresas(base_datos):
    return "Lista de empresas"
```

### `@admin_mysql_requerido`
Verifica que el usuario tenga tipo_usuario = 'admin' en MySQL.

```python
@app.route('/<base_datos>/admin/configuracion')
@login_required
@admin_mysql_requerido
def configuracion_admin(base_datos):
    return "Solo administradores"
```

### `@solo_administradores`
Verifica que el usuario sea admin en PostgreSQL (rol = 'administrador').

```python
@app.route('/sistema/usuarios')
@login_required
@solo_administradores
def gestionar_usuarios_sistema():
    return "Gestión de usuarios del sistema"
```

## 🔄 Diferencias Entre Niveles de Admin

| Característica | PostgreSQL Admin | MySQL Admin |
|----------------|------------------|-------------|
| Tabla          | auth.usuarios (rol='administrador') | usuarios_acceso (tipo_usuario='admin') |
| Alcance        | Global - todos las BD | Por base de datos específica |
| Uso típico     | Crear usuarios del sistema | Operaciones administrativas dentro de una BD |
| Decorador      | `@solo_administradores` | `@admin_mysql_requerido` |

## 💡 Casos de Uso

### Usuario Normal
- **PostgreSQL**: `rol = 'usuario'`
- **MySQL**: `tipo_usuario = 'usuario'`
- **Puede**: Consultar datos, usar módulos habilitados
- **No puede**: Crear/eliminar empresas, modificar configuraciones

### Administrador de Base de Datos
- **PostgreSQL**: `rol = 'usuario'` (o 'administrador')
- **MySQL**: `tipo_usuario = 'admin'`
- **Puede**: TODO dentro de su base de datos asignada
- **No puede**: Acceder a otras bases de datos

### Super Administrador
- **PostgreSQL**: `rol = 'administrador'`
- **MySQL**: `tipo_usuario = 'admin'` en todas las BD
- **Puede**: TODO en todo el sistema

## 🧪 Verificar Configuración Actual

```sql
-- Ver todos los usuarios configurados
SELECT usuario, auditor, tipo_usuario, estado, fecha_creacion
FROM usuarios_acceso
ORDER BY tipo_usuario DESC, usuario;

-- Ver solo administradores
SELECT usuario, auditor, estado
FROM usuarios_acceso
WHERE tipo_usuario = 'admin';

-- Ver solo usuarios vigentes
SELECT usuario, auditor, tipo_usuario
FROM usuarios_acceso
WHERE estado = 'V';
```

## 📌 Información en Sesión de Flask

Después del login exitoso, la sesión contiene:

```python
session['auditor_mysql']        # Nombre del auditor
session['tipo_usuario_mysql']   # 'admin' o 'usuario'
session['session_token']         # Token de sesión única
```

Puedes acceder a esto en templates:

```jinja2
<!-- Mostrar info del usuario -->
<p>Usuario: {{ current_user.nombre_usuario }}</p>
<p>Auditor: {{ session.auditor_mysql }}</p>
<p>Tipo: {{ session.tipo_usuario_mysql }}</p>

<!-- Mostrar contenido solo a admins -->
{% if session.tipo_usuario_mysql == 'admin' %}
    <button>Eliminar empresa</button>
{% endif %}
```

## ⚠️ Importante

1. **Sincronización**: El `usuario` en MySQL debe coincidir EXACTAMENTE con `nombre_usuario` en PostgreSQL
2. **Case-sensitive**: Los nombres de usuario son sensibles a mayúsculas/minúsculas
3. **Cada BD es independiente**: Debes crear el registro en cada base de datos MySQL
4. **Estado por defecto**: Al crear un usuario, usa `estado = 'V'` para que esté activo
5. **Tipo por defecto**: Si no especificas, será `tipo_usuario = 'usuario'`

## 🔧 Solución de Problemas

### Error: "Usuario no registrado en base de datos"
**Causa**: No existe el registro en `usuarios_acceso` de esa BD MySQL.
**Solución**:
```sql
INSERT INTO usuarios_acceso (usuario, auditor, tipo_usuario, estado)
VALUES ('nombre_usuario', 'nombre_auditor', 'usuario', 'V');
```

### Error: "Usuario no vigente"
**Causa**: El campo `estado` es 'I' (Inactivo).
**Solución**:
```sql
UPDATE usuarios_acceso SET estado = 'V' WHERE usuario = 'nombre_usuario';
```

### Usuario no puede acceder a funciones de admin
**Causa**: `tipo_usuario = 'usuario'` pero necesita ser 'admin'.
**Solución**:
```sql
UPDATE usuarios_acceso SET tipo_usuario = 'admin' WHERE usuario = 'nombre_usuario';
```

## 📚 Ejemplo Completo

```sql
-- Configurar usuario completo para 'mschaff' en stratex
INSERT INTO usuarios_acceso (usuario, auditor, tipo_usuario, estado)
VALUES ('mschaff', 'matias', 'admin', 'V')
ON DUPLICATE KEY UPDATE
    tipo_usuario = 'admin',
    estado = 'V',
    auditor = 'matias';

-- Verificar
SELECT * FROM usuarios_acceso WHERE usuario = 'mschaff';
```

Ahora cuando `mschaff` inicie sesión:
1.  Autentica contra PostgreSQL
2.  Valida vigencia en MySQL stratex
3.  Guarda auditor = 'matias'
4.  Guarda tipo_usuario = 'admin'
5.  Puede usar `@admin_mysql_requerido` en rutas protegidas
