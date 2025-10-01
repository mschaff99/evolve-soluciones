# Guía de Instalación - Sistema de Autenticación

## Arquitectura de Bases de Datos

El sistema utiliza una arquitectura híbrida:

- **PostgreSQL**: Sistema de autenticación (usuarios y sesiones)
- **MySQL**: Gestión empresarial (empresas, F29, consolidados, etc.)
- **MongoDB**: Almacenamiento de archivos (opcional)

## Requisitos Previos

### PostgreSQL
- PostgreSQL 12 o superior
- Cliente psql (para ejecutar scripts SQL)

### Python
- Python 3.8 o superior
- pip (gestor de paquetes)

## Paso 1: Instalar PostgreSQL

### Windows

1. Descargar PostgreSQL desde: https://www.postgresql.org/download/windows/
2. Ejecutar el instalador y seguir las instrucciones
3. Anotar la contraseña del usuario `postgres`
4. Agregar PostgreSQL al PATH (usualmente: `C:\Program Files\PostgreSQL\16\bin`)

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

### macOS

```bash
brew install postgresql@16
brew services start postgresql@16
```

## Paso 2: Crear Base de Datos

### Conectar a PostgreSQL

```bash
# Windows / Linux / macOS
psql -U postgres
```

### Crear base de datos

```sql
-- Crear base de datos
CREATE DATABASE evolve_auth;

-- Conectar a la base de datos
\c evolve_auth

-- Verificar conexión
SELECT current_database();

-- Salir
\q
```

## Paso 3: Ejecutar Migración

Ejecutar el script SQL para crear las tablas:

```bash
# Desde el directorio raíz del proyecto
psql -U postgres -d evolve_auth -f migraciones/001_crear_tablas_autenticacion_postgres.sql
```

### Verificar que las tablas se crearon

```bash
psql -U postgres -d evolve_auth -c "\dt auth.*"
```

Deberías ver:
- `auth.usuarios`
- `auth.sesiones_usuario`
- `auth.intentos_login`

## Paso 4: Instalar Dependencias Python

```bash
# Activar entorno virtual
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

# Instalar psycopg2 (driver de PostgreSQL)
pip install psycopg2-binary==2.9.9

# Instalar todas las dependencias
pip install -r requirements.txt
```

## Paso 5: Configurar Variables de Entorno

### Crear archivo `.env`

Copiar `env.ejemplo` a `.env`:

```bash
# Windows
copy env.ejemplo .env

# Linux/macOS
cp env.ejemplo .env
```

### Editar `.env` con tus credenciales

```env
# BASE DE DATOS POSTGRESQL (Sistema de Autenticación)
POSTGRES_HOST=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=tu-password-postgres
POSTGRES_DB=evolve_auth
POSTGRES_PORT=5432

# BASE DE DATOS MYSQL (Gestión Empresarial)
DB_HOST=127.0.0.1
DB_USER=root
DB_PASSWORD=tu-password-mysql
DB_NAME=evolve
DB_PORT=3306

# CLAVE SECRETA (Importante en producción)
SECRET_KEY=genera-una-clave-secreta-aleatoria-aqui
```

## Paso 6: Inicializar con Usuario Admin

Ejecutar el script de inicialización:

```bash
python scripts/inicializar_base_datos.py
```

El script te pedirá:
- Nombre de usuario (default: `admin`)
- Email (default: `admin@evolve.cl`)
- Contraseña (mínimo 8 caracteres)
- Confirmar contraseña

### Ejemplo de ejecución

```
============================================================
INICIALIZACION DE BASE DE DATOS - EVOLVE SOLUCIONES
============================================================

1. Verificando conexion a PostgreSQL...
Conexion exitosa a PostgreSQL
Version: PostgreSQL 16.1...

2. Verificando tablas...
Todas las tablas necesarias existen

3. Verificando usuario administrador...

4. Creando usuario administrador...
------------------------------------------------------------
Nombre de usuario para admin [admin]: admin
Email para admin [admin@evolve.cl]: admin@evolve.cl
Contraseña para admin: ********
Confirmar contraseña: ********

Usuario administrador creado exitosamente
ID: 1
Usuario: admin
Email: admin@evolve.cl
Rol: administrador
------------------------------------------------------------

Inicializacion completada exitosamente

Puedes iniciar sesion en:
  http://localhost:5000/auth/iniciar-sesion
```

## Paso 7: Iniciar la Aplicación

```bash
# Modo desarrollo
python aplicacion.py

# Modo producción (Waitress)
python wsgi_waitress.py
```

## Paso 8: Verificar Funcionamiento

### Acceder al login

Navega a: http://localhost:5000

Deberías ser redirigido a: http://localhost:5000/auth/iniciar-sesion

### Iniciar sesión

Usa las credenciales del administrador que creaste:
- Usuario: `admin`
- Contraseña: la que estableciste

## Comandos Útiles de PostgreSQL

### Ver usuarios en la base de datos

```sql
SELECT id, nombre_usuario, email, rol, activo 
FROM auth.usuarios;
```

### Ver sesiones activas

```sql
SELECT s.id, u.nombre_usuario, s.direccion_ip, s.fecha_ultima_actividad, s.activa
FROM auth.sesiones_usuario s
JOIN auth.usuarios u ON s.id_usuario = u.id
WHERE s.activa = TRUE
ORDER BY s.fecha_ultima_actividad DESC;
```

### Ver intentos de login

```sql
SELECT nombre_usuario, direccion_ip, exitoso, fecha_intento, mensaje
FROM auth.intentos_login
ORDER BY fecha_intento DESC
LIMIT 20;
```

### Limpiar sesiones expiradas

```sql
SELECT auth.limpiar_sesiones_expiradas(1440); -- 24 horas
```

### Resetear contraseña de un usuario (desde psql)

```python
# Desde Python
from werkzeug.security import generate_password_hash

nueva_contraseña = "NuevaContraseña123"
hash_contraseña = generate_password_hash(nueva_contraseña)
print(hash_contraseña)
```

```sql
-- Luego en PostgreSQL
UPDATE auth.usuarios 
SET hash_contraseña = 'el-hash-generado-aqui' 
WHERE nombre_usuario = 'admin';
```

## Solución de Problemas

### Error: "No existe el esquema auth"

```sql
-- Crear esquema manualmente
CREATE SCHEMA IF NOT EXISTS auth;
```

### Error: "FATAL: password authentication failed"

Verifica que la contraseña en `.env` sea correcta:
```env
POSTGRES_PASSWORD=tu-password-correcto
```

### Error: "could not connect to server"

Verifica que PostgreSQL esté ejecutándose:

```bash
# Windows
net start postgresql-x64-16

# Linux
sudo systemctl status postgresql
sudo systemctl start postgresql

# macOS
brew services list
brew services start postgresql@16
```

### Error: "psycopg2 module not found"

```bash
pip install psycopg2-binary==2.9.9
```

### Puerto 5432 en uso

Cambiar el puerto en `.env`:
```env
POSTGRES_PORT=5433
```

Y en `postgresql.conf` cambiar también.

## Seguridad en Producción

### 1. Cambiar credenciales por defecto

Nunca usar `postgres` con contraseña débil en producción.

### 2. Configurar SSL

En `.env`:
```env
POSTGRES_SSLMODE=require
```

### 3. Limitar acceso por IP

Editar `pg_hba.conf`:
```
# Solo permitir conexiones locales
host    evolve_auth    postgres    127.0.0.1/32    scram-sha-256
```

### 4. Usar variables de entorno seguras

No commitear el archivo `.env` al repositorio.

### 5. Habilitar HTTPS

En producción, configurar:
```env
SESSION_COOKIE_SECURE=True
WTF_CSRF_SSL_STRICT=True
```

## Backup y Restauración

### Hacer backup

```bash
pg_dump -U postgres -d evolve_auth -F c -f backup_auth_$(date +%Y%m%d).dump
```

### Restaurar backup

```bash
pg_restore -U postgres -d evolve_auth -c backup_auth_20240101.dump
```

## Monitoreo

### Ver conexiones activas

```sql
SELECT count(*) FROM pg_stat_activity 
WHERE datname = 'evolve_auth';
```

### Ver tamaño de la base de datos

```sql
SELECT pg_size_pretty(pg_database_size('evolve_auth'));
```

## Contacto y Soporte

Para problemas o preguntas, contactar al equipo de desarrollo.
