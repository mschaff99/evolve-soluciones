# Migraciones de Base de Datos

Este directorio contiene los scripts de migración SQL para las bases de datos del sistema Evolve Soluciones.

## 📁 Estructura

- `001_*.sql` - Migraciones para autenticación (PostgreSQL)
- `002_*.sql` - Migración para catálogo de códigos F29 (PostgreSQL)

## 🗄️ Bases de Datos

### PostgreSQL (evolve)
- **Usuario**: postgres
- **Base de datos**: evolve
- **Uso**: Autenticación, catálogos y configuraciones

### MySQL (evolve_local / Stratex)
- **Base de datos local**: evolve
- **Base de datos remota**: stratex
- **Uso**: Datos operacionales de empresas y períodos

##  Cómo Ejecutar Migraciones

### Opción 1: Con psql (Línea de comandos)

```bash
# Activar PostgreSQL en PATH y ejecutar
psql -U postgres -d evolve -f migraciones/002_crear_tabla_codigos_observaciones_f29.sql
```

### Opción 2: Con pgAdmin (GUI)

1. Abrir pgAdmin
2. Conectar al servidor PostgreSQL
3. Seleccionar base de datos `evolve`
4. Abrir Query Tool (Tools → Query Tool)
5. Abrir el archivo de migración (.sql)
6. Ejecutar (F5)

### Opción 3: Desde Python

```bash
# Activar entorno virtual
.venv\Scripts\activate

# Usar el script de verificación que indica si falta ejecutar migración
python scripts/verificar_codigos_observaciones.py
```

##  Lista de Migraciones

# Migraciones de Base de Datos

## Índice de Migraciones

### 001 - Tablas de Autenticación
**Archivo**: `001_crear_tablas_autenticacion_postgres.sql`
**Descripción**: Crea el schema `auth` y las tablas básicas de autenticación
**Tablas**:
- `auth.usuarios`
- `auth.sesiones_usuario`
- `auth.intentos_login`

### 002 - Códigos de Observaciones F29
**Archivo**: `002_crear_tabla_codigos_observaciones_f29.sql`
**Descripción**: Crea tabla de catálogo de códigos de observaciones
**Tablas**:
- `auth.codigos_observaciones_f29`

### 003 - Sistema de Módulos por Base de Datos
**Archivo**: `003_sistema_modulos_por_bd.sql`
**Descripción**: Sistema de habilitación de módulos por base de datos (multi-tenant)
**Tablas**:
- `auth.modulos_sistema` - Catálogo de módulos disponibles
- `auth.bases_datos_mysql` - Registro de bases de datos MySQL (clientes)
- `auth.modulos_habilitados_bd` - Habilitación de módulos por BD

**Funciones**:
- `auth.modulo_habilitado(p_nombre_bd, p_codigo_modulo)` - Verifica si módulo está habilitado

**Vistas**:
- `auth.vista_modulos_habilitados` - Vista consolidada de módulos por BD

---

## Ejecución de Migraciones

### Prerrequisitos

- PostgreSQL 12+
- Base de datos `evolve_auth` creada
- Usuario con permisos de creación de tablas

### Método 1: psql (Recomendado)

```powershell
# Conectarse a PostgreSQL
psql -U postgres -d evolve_auth

# Ejecutar migración específica
\i migraciones/001_crear_tablas_autenticacion_postgres.sql
\i migraciones/002_crear_tabla_codigos_observaciones_f29.sql
\i migraciones/003_sistema_modulos_por_bd.sql
```

### Método 2: Script Python

```python
# scripts/ejecutar_migraciones.py
import psycopg2
from pathlib import Path

def ejecutar_migracion(archivo_sql):
    conn = psycopg2.connect(
        host='localhost',
        user='postgres',
        password='tu_password',
        database='evolve_auth'
    )

    with open(archivo_sql, 'r', encoding='utf-8') as f:
        sql = f.read()

    with conn.cursor() as cur:
        cur.execute(sql)

    conn.commit()
    conn.close()
    print(f"Migración {archivo_sql} ejecutada correctamente")

# Ejecutar migraciones en orden
ejecutar_migracion('migraciones/001_crear_tablas_autenticacion_postgres.sql')
ejecutar_migracion('migraciones/002_crear_tabla_codigos_observaciones_f29.sql')
ejecutar_migracion('migraciones/003_sistema_modulos_por_bd.sql')
```

---

## Verificación Post-Migración

### Verificar Tablas Creadas

```sql
-- Listar todas las tablas en schema auth
SELECT tablename
FROM pg_tables
WHERE schemaname = 'auth'
ORDER BY tablename;

-- Resultado esperado:
-- bases_datos_mysql
-- codigos_observaciones_f29
-- intentos_login
-- modulos_habilitados_bd
-- modulos_sistema
-- sesiones_usuario
-- usuarios
```

### Verificar Datos Iniciales

```sql
-- Verificar módulos registrados (debe haber 9)
SELECT COUNT(*) FROM auth.modulos_sistema;

-- Verificar bases de datos registradas (debe haber 2: stratex, evolve)
SELECT COUNT(*) FROM auth.bases_datos_mysql;

-- Verificar módulos habilitados
SELECT
    bd.nombre_base_datos,
    COUNT(mh.id) as modulos_habilitados
FROM auth.bases_datos_mysql bd
LEFT JOIN auth.modulos_habilitados_bd mh ON bd.id = mh.id_base_datos
GROUP BY bd.nombre_base_datos;
```

### Verificar Funciones

```sql
-- Probar función de verificación de módulo
SELECT auth.modulo_habilitado('stratex', 'consulta_f29');  -- Debe ser TRUE
SELECT auth.modulo_habilitado('evolve', 'ia');             -- Debe ser FALSE
```

---

## Rollback (Revertir Migraciones)

### Eliminar Migración 003

```sql
DROP VIEW IF EXISTS auth.vista_modulos_habilitados;
DROP FUNCTION IF EXISTS auth.modulo_habilitado(VARCHAR, VARCHAR);
DROP TABLE IF EXISTS auth.modulos_habilitados_bd CASCADE;
DROP TABLE IF EXISTS auth.bases_datos_mysql CASCADE;
DROP TABLE IF EXISTS auth.modulos_sistema CASCADE;
```

### Eliminar Migración 002

```sql
DROP TABLE IF EXISTS auth.codigos_observaciones_f29 CASCADE;
```

### Eliminar Migración 001

```sql
DROP TABLE IF EXISTS auth.intentos_login CASCADE;
DROP TABLE IF EXISTS auth.sesiones_usuario CASCADE;
DROP TABLE IF EXISTS auth.usuarios CASCADE;
DROP SCHEMA IF EXISTS auth CASCADE;
```

---

## Agregar Nueva Migración

### Nomenclatura

```
00X_descripcion_breve.sql
```

Donde:
- `00X`: Número secuencial con padding (004, 005, etc.)
- `descripcion_breve`: Descripción en snake_case

### Template de Migración

```sql
-- =====================================================
-- Script de Migración - [TÍTULO]
-- Base de Datos: PostgreSQL
-- Versión: X.X.X
-- Fecha: DD de mes de YYYY
-- Descripción: [Descripción detallada]
-- =====================================================

-- [SQL aquí]

-- Mensaje de confirmación
DO $$
BEGIN
    RAISE NOTICE '=================================================';
    RAISE NOTICE 'Migración 00X: [TÍTULO] completada';
    RAISE NOTICE '=================================================';
END $$;
```

---

## Errores Comunes

### Error: "role does not exist"

```sql
-- Crear rol si no existe
CREATE ROLE evolve_app WITH LOGIN PASSWORD 'password';
GRANT CONNECT ON DATABASE evolve_auth TO evolve_app;
GRANT USAGE ON SCHEMA auth TO evolve_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA auth TO evolve_app;
```

### Error: "schema auth does not exist"

```sql
-- Crear schema
CREATE SCHEMA IF NOT EXISTS auth;
```

### Error: FK violation en usuarios.base_datos_mysql

**Causa**: La migración 003 NO debe tener FK desde `usuarios.base_datos_mysql` hacia `bases_datos_mysql.nombre_base_datos` porque MySQL está en servidor separado.

**Solución**: Ya está corregido en migración 003. Si existe la FK, eliminarla:

```sql
ALTER TABLE auth.usuarios DROP CONSTRAINT IF EXISTS fk_usuario_base_datos;
```

---

## Documentación Relacionada

- **Sistema de Módulos**: `documentacion/SISTEMA_MODULOS_POR_BD.md`
- **Arquitectura**: `documentacion/ARQUITECTURA_COMPLETA.md`
- **Instalación**: `documentacion/INICIO_RAPIDO.md`


##  Verificar Estado de Migraciones

### PostgreSQL

```sql
-- Ver todas las tablas en evolve
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- Verificar tabla de códigos F29
SELECT COUNT(*) as total_codigos
FROM codigos_observaciones_f29
WHERE activo = TRUE;
```

### MySQL/Stratex

```sql
-- Ver tablas en evolve local
SHOW TABLES FROM evolve;

-- Ver tablas en stratex
SHOW TABLES FROM stratex;
```

##  Consideraciones Importantes

1. **Backups**: Hacer backup antes de ejecutar migraciones en producción
2. **Orden**: Ejecutar migraciones en orden numérico
3. **Idempotencia**: Las migraciones usan `IF NOT EXISTS` y `ON CONFLICT DO NOTHING`
4. **Rollback**: Guardar copia de datos antes de migraciones destructivas
5. **Testing**: Probar en desarrollo antes de aplicar en producción

## 🛠️ Crear Nueva Migración

### Nomenclatura

```
00X_nombre_descriptivo_[postgres|mysql].sql
```

Donde:
- `00X` = Número secuencial (3 dígitos)
- `nombre_descriptivo` = Descripción clara en snake_case
- `[postgres|mysql]` = Motor de base de datos

### Template Básico

```sql
-- =============================================================================
-- Migración 00X: [Título descriptivo]
-- =============================================================================
-- Base de datos: [evolve|stratex|evolve_local]
-- Motor: [PostgreSQL|MySQL]
-- Propósito: [Descripción del propósito]
-- Fecha: YYYY-MM-DD
-- =============================================================================

-- Verificar base de datos actual
SELECT current_database(); -- PostgreSQL
-- SELECT DATABASE(); -- MySQL

-- [Tu código SQL aquí]

-- Verificación
-- [Consultas para verificar que se aplicó correctamente]
```

##  Scripts de Utilidad

### Verificación General
```bash
python scripts/verificar_conexiones.py
```

### Verificación Específica - Códigos F29
```bash
python scripts/verificar_codigos_observaciones.py
```

### Inicializar Base de Datos Completa
```bash
python scripts/inicializar_base_datos.py
```

## 🐛 Troubleshooting

### Error: "psql no reconocido"
Agregar PostgreSQL al PATH:
```powershell
$env:Path += ";C:\Program Files\PostgreSQL\16\bin"
```

### Error: "Tabla ya existe"
Las migraciones son idempotentes, el error es informativo. Verificar que los datos estén correctos.

### Error: "Permisos insuficientes"
Ejecutar como usuario `postgres` o con rol de superusuario.

### Error: "Base de datos no existe"
```sql
-- Crear base de datos evolve primero
CREATE DATABASE evolve;
```

## 📝 Historial de Cambios

| Versión | Fecha | Descripción |
|---------|-------|-------------|
| 001 | 2024 | Sistema de autenticación PostgreSQL |
| 002 | 2025-10-06 | Catálogo de códigos F29 |

---

**Última actualización**: 06 de octubre de 2025
