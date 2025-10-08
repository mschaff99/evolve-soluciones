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

### 001 - Autenticación (PostgreSQL)
**Archivo**: `001_crear_tablas_autenticacion_postgres.sql`

Crea las tablas necesarias para el sistema de autenticación:
- `usuarios`
- `roles`
- `permisos`
- Relaciones y constraints

**Estado**: ✓ Aplicada

### 002 - Catálogo Códigos F29 (PostgreSQL)
**Archivo**: `002_crear_tabla_codigos_observaciones_f29.sql`

Crea tabla centralizada para códigos de observaciones del Formulario 29:
- Tabla `codigos_observaciones_f29`
- 16 códigos iniciales
- Índices y triggers
- Clasificación por tipo de operación

**Códigos incluidos**: W39, FM01, PPM01, W08, W38, W40, W01, W22, W10, PPM08, W19, W14, W12, PPM10, W01LF, W16

**Documentación**: Ver `documentacion/CATALOGO_CODIGOS_F29.md`

**Verificación**:
```bash
python scripts/verificar_codigos_observaciones.py
```

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
