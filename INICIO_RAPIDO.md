# Inicio Rápido - Sistema de Autenticación PostgreSQL

##  Estado Actual

- PostgreSQL está instalado y funcionando
- La base de datos `evolve_auth` existe
- Las tablas están creadas
- **Solo falta crear el usuario administrador**

## 🚀 Crear Usuario Administrador (2 opciones)

### Opción 1: Script Automático (Más Rápido)

```bash
python scripts/crear_admin_simple.py
```

**Credenciales creadas:**
- Usuario: `admin`
- Contraseña: `Admin123456`
- Email: `admin@evolve.cl`

⚠️ **IMPORTANTE:** Cambiar la contraseña después del primer login

### Opción 2: Script Interactivo (Personalizado)

```bash
python scripts/inicializar_base_datos.py
```

Este script te permite elegir:
- Tu propio nombre de usuario
- Tu propio email
- Tu propia contraseña

## 🎯 Iniciar la Aplicación

Una vez creado el usuario administrador:

```bash
# Desarrollo
python aplicacion.py

# Producción
python wsgi_waitress.py
```

Accede en: **http://localhost:5000**

## 📋 Resumen de Comandos

```powershell
# 1. Activar entorno virtual (si no está activado)
.venv\Scripts\activate

# 2. Crear usuario admin
python scripts/crear_admin_simple.py

# 3. Iniciar aplicación
python aplicacion.py

# 4. Abrir navegador
start http://localhost:5000
```

## 🔧 Si Tienes Problemas

### Ver usuarios existentes en PostgreSQL

```sql
SELECT id, nombre_usuario, email, rol, activo
FROM auth.usuarios;
```

### Resetear contraseña de admin

```sql
-- Generar nuevo hash desde Python:
-- from werkzeug.security import generate_password_hash
-- print(generate_password_hash("NuevaContraseña123"))

UPDATE auth.usuarios
SET hash_contraseña = 'hash-generado-aqui'
WHERE nombre_usuario = 'admin';
```

### Eliminar usuario y volver a crear

```sql
DELETE FROM auth.usuarios WHERE nombre_usuario = 'admin';
```

Luego ejecuta nuevamente:
```bash
python scripts/crear_admin_simple.py
```

## 📁 Arquitectura de Permisos

```
PostgreSQL (auth)              MySQL (stratex/otras BDs)
├─ admin-stratex              ├─ empresas
│  └─ rol: administrador      │  ├─ auditor: "ALEXEI"
├─ ALEXEI                     │  ├─ auditor: "JUAN"
│  └─ rol: usuario            │  └─ auditor: "ALEXEI"
└─ JUAN
   └─ rol: usuario

Regla de Acceso:
- Admin: Ve TODAS las empresas
- Usuario: Solo ve donde empresas.auditor = nombre_usuario
```

**IMPORTANTE:** El `nombre_usuario` en PostgreSQL debe coincidir **EXACTAMENTE** con la columna `auditor` en MySQL

## 🔐 Características de Seguridad

-  Contraseñas hasheadas con bcrypt
-  Tokens de sesión seguros
-  Protección CSRF
-  Registro de intentos de login
-  Expiración de sesiones (24h)
-  Validaciones client y server-side

## 📚 Documentación Adicional

- [Instalación Completa](documentacion/INSTALACION_AUTENTICACION.md)
- [Comandos PostgreSQL](scripts/comandos-postgres.txt)
- [README Principal](README.md)

## 🆘 Soporte

Si encuentras errores:

1. Verifica conexión: `python scripts/verificar_conexiones.py`
2. Revisa logs en: `logs/`
3. Verifica `.env` tiene las credenciales correctas

---

**¡Listo! Tu sistema de autenticación está configurado** 🎉
