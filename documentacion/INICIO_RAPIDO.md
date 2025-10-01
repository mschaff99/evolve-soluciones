# Inicio Rápido - Sistema de Autenticación

## Resumen de Arquitectura

```
┌─────────────────────────────────────────────┐
│         EVOLVE SOLUCIONES                   │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────────┐  ┌────────────────────┐   │
│  │ PostgreSQL  │  │      MySQL         │   │
│  │  (Auth)     │  │   (Empresas)       │   │
│  │             │  │                    │   │
│  │ • Usuarios  │  │ • F29              │   │
│  │ • Sesiones  │  │ • Consolidados     │   │
│  │ • Intentos  │  │ • Tareas           │   │
│  └─────────────┘  └────────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

## Instalación en 5 Pasos

### 1. Instalar PostgreSQL

**Windows:**
```powershell
# Descargar desde: https://www.postgresql.org/download/windows/
# Instalar y anotar contraseña de postgres
```

**Linux:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

### 2. Crear Base de Datos

```bash
# Conectar a PostgreSQL
psql -U postgres

# En psql:
CREATE DATABASE evolve_auth;
\q
```

### 3. Ejecutar Migración

```bash
# Desde el directorio del proyecto
psql -U postgres -d evolve_auth -f migraciones/001_crear_tablas_autenticacion_postgres.sql
```

### 4. Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
copy env.ejemplo .env  # Windows
cp env.ejemplo .env    # Linux/Mac

# Editar .env y configurar:
POSTGRES_PASSWORD=tu-password-real
```

### 5. Inicializar Usuario Admin

```bash
# Instalar dependencias
pip install -r requirements.txt

# Verificar conexiones
python scripts/verificar_conexiones.py

# Crear usuario admin
python scripts/inicializar_base_datos.py
```

## Iniciar Aplicación

```bash
# Desarrollo
python aplicacion.py

# Producción
python wsgi_waitress.py
```

Accede en: **http://localhost:5000**

## Credenciales por Defecto

- **Usuario:** admin
- **Contraseña:** La que configuraste en el paso 5

## Verificación Rápida

```bash
# Verificar todas las conexiones
python scripts/verificar_conexiones.py

# Ver usuarios en PostgreSQL
psql -U postgres -d evolve_auth -c "SELECT * FROM auth.usuarios;"

# Ver sesiones activas
psql -U postgres -d evolve_auth -c "SELECT * FROM auth.sesiones_usuario WHERE activa = TRUE;"
```

## Estructura del Sistema

```
evolve-soluciones/
├── aplicacion/
│   ├── controladores/
│   │   └── autenticacion.py       # Rutas de login/logout
│   ├── modelos/
│   │   ├── base_datos.py          # Conexiones PostgreSQL/MySQL
│   │   ├── usuario.py             # Modelo Usuario
│   │   └── sesion.py              # Modelo Sesión
│   └── plantillas/
│       └── paginas/
│           └── iniciar_sesion.html
│
├── configuracion/
│   └── configuracion.py           # Config PostgreSQL/MySQL
│
├── migraciones/
│   └── 001_crear_tablas_autenticacion_postgres.sql
│
├── scripts/
│   ├── inicializar_base_datos.py # Crear admin
│   ├── verificar_conexiones.py   # Test conexiones
│   └── comandos-postgres.txt     # Comandos útiles
│
└── documentacion/
    ├── INICIO_RAPIDO.md           # Este archivo
    └── INSTALACION_AUTENTICACION.md # Guía completa
```

## Comandos Útiles

### PostgreSQL

```bash
# Ver usuarios
psql -U postgres -d evolve_auth -c "SELECT nombre_usuario, email, rol FROM auth.usuarios;"

# Limpiar sesiones expiradas
psql -U postgres -d evolve_auth -c "SELECT auth.limpiar_sesiones_expiradas(1440);"

# Ver intentos de login fallidos
psql -U postgres -d evolve_auth -c "SELECT * FROM auth.intentos_login WHERE exitoso = FALSE ORDER BY fecha_intento DESC LIMIT 10;"
```

### Python

```python
# Crear usuario desde Python
from aplicacion.modelos.usuario import Usuario

usuario = Usuario.crear_usuario(
    nombre_usuario="nuevo_usuario",
    email="usuario@evolve.cl",
    contraseña="Contraseña123",
    rol="usuario"
)
```

## Solución de Problemas

### Error: "No existe el esquema auth"
```sql
CREATE SCHEMA IF NOT EXISTS auth;
```
Luego ejecuta la migración nuevamente.

### Error: "psycopg2 module not found"
```bash
pip install psycopg2-binary==2.9.9
```

### Error: "could not connect to server"
```bash
# Verificar que PostgreSQL esté corriendo
# Windows:
net start postgresql-x64-16

# Linux:
sudo systemctl start postgresql
```

### Olvidé mi contraseña de admin

```python
# 1. Generar nuevo hash
from werkzeug.security import generate_password_hash
nuevo_hash = generate_password_hash("NuevaContraseña123")
print(nuevo_hash)

# 2. Actualizar en PostgreSQL
# psql -U postgres -d evolve_auth
# UPDATE auth.usuarios SET hash_contraseña = 'hash-aqui' WHERE nombre_usuario = 'admin';
```

## Próximos Pasos

1. **Configurar MySQL** para gestión empresarial
2. **Agregar más usuarios** desde el panel de admin
3. **Configurar HTTPS** para producción
4. **Configurar backup automático** de PostgreSQL

## Documentación Completa

- [Instalación Completa](INSTALACION_AUTENTICACION.md)
- [Comandos PostgreSQL](../scripts/comandos-postgres.txt)
- [README Principal](../README.md)

## Soporte

Para problemas o preguntas, revisar:
1. Logs de la aplicación
2. Logs de PostgreSQL
3. Script de verificación: `python scripts/verificar_conexiones.py`
