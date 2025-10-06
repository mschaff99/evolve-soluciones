# Catálogo de Códigos de Observaciones F29

## 📋 Descripción

Este documento describe el catálogo centralizado de códigos de observaciones del Formulario 29 (F29) del SII, almacenado en PostgreSQL.

## 🗄️ Estructura de la Tabla

La tabla `codigos_observaciones_f29` se encuentra en la base de datos **evolve (PostgreSQL)** y contiene:

```sql
CREATE TABLE codigos_observaciones_f29 (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL UNIQUE,      -- Código único (ej: W39, FM01)
    descripcion TEXT NOT NULL,               -- Descripción del código
    activo BOOLEAN DEFAULT TRUE,             -- Si está activo
    fecha_creacion TIMESTAMP,
    fecha_actualizacion TIMESTAMP
);
```

## 📦 Códigos Actuales

| Código | Descripción |
|--------|-------------|
| W39 | Control Precautorio Proveedores |
| FM01 | Remanente CF |
| PPM01 | PPM |
| W08 | Crédito Fiscal |
| W38 | Nota de Crédito Emitidas fuera de plazo |
| W40 | Nota de Crédito Emitidas fuera de plazo |
| W01 | Débito Fiscal |
| W22 | Exportaciones |
| W10 | NC Compras |
| PPM08 | Honorarios |
| W19 | Impuesto Especifico (Crédito) |
| W14 | IVA Retenido a Terceros |
| W12 | Importaciones |
| PPM10 | Retencion impuesto tasa 10% |
| W01LF | Debito Fiscal |
| W16 | Iva Retenido por NC emitidas |

## 🚀 Instalación Inicial

### 1. Ejecutar Migración SQL

Conectarse a PostgreSQL y ejecutar:

```bash
# Opción 1: Con psql
psql -U postgres -d evolve -f migraciones/002_crear_tabla_codigos_observaciones_f29.sql

# Opción 2: Con pgAdmin
# 1. Conectar a la base de datos 'evolve'
# 2. Abrir Query Tool
# 3. Cargar y ejecutar el archivo 002_crear_tabla_codigos_observaciones_f29.sql
```

### 2. Verificar Instalación

```bash
# Activar entorno virtual
.venv\Scripts\activate

# Ejecutar script de verificación
python scripts/verificar_codigos_observaciones.py
```

El script mostrará:
- ✓ Si la tabla existe
- ✓ Cantidad de códigos registrados
- ✓ Listado de todos los códigos con sus tipos
- ✓ Resumen por tipo de operación

## 🔧 Mantenimiento

### Agregar Nuevos Códigos

```sql
INSERT INTO codigos_observaciones_f29
    (codigo, descripcion)
VALUES
    ('W99', 'Nuevo Código de Ejemplo');
```

### Modificar Código Existente

```sql
UPDATE codigos_observaciones_f29
SET descripcion = 'Nueva descripción'
WHERE codigo = 'W99';
```

### Desactivar Código (no eliminar)

```sql
UPDATE codigos_observaciones_f29
SET activo = FALSE
WHERE codigo = 'W99';
```

## 📊 Consultas Útiles

### Ver Todos los Códigos Activos

```sql
SELECT codigo, descripcion
FROM codigos_observaciones_f29
WHERE activo = TRUE
ORDER BY codigo;
```

### Buscar Código Específico

```sql
SELECT codigo, descripcion
FROM codigos_observaciones_f29
WHERE codigo LIKE 'W%' AND activo = TRUE
ORDER BY codigo;
```

### Códigos sin Usar (no referenciados en observaciones)

```sql
SELECT c.codigo, c.descripcion
FROM codigos_observaciones_f29 c
LEFT JOIN observaciones o ON c.codigo = o.codigo
WHERE o.codigo IS NULL AND c.activo = TRUE;
```

## 🔄 Integración con el Sistema

### En Python (ServicioConsultaIntegral)

```python
# El método obtener_codigos_observaciones_unicos() ahora consulta el catálogo
servicio = ServicioConsultaIntegral()
codigos = servicio.obtener_codigos_observaciones_unicos()

# Retorna lista de diccionarios:
# [
#   {
#     'codigo': 'W39',
#     'descripcion': 'Control Precautorio Proveedores'
#   },
#   {
#     'codigo': 'FM01',
#     'descripcion': 'Remanente CF'
#   },
#   ...
# ]
```

### Fallback Automático

Si la tabla del catálogo no existe o falla la consulta, el sistema automáticamente:
1. Intenta obtener códigos desde la tabla `observaciones` (códigos ya usados)
2. Retorna lista en formato compatible
3. Registra el error en los logs

## 🎯 Ventajas del Catálogo

1. **Centralización**: Un único lugar para todos los códigos
2. **Documentación**: Descripción clara de cada código
3. **Extensibilidad**: Fácil agregar nuevos códigos sin modificar código
4. **Mantenibilidad**: Activar/desactivar códigos sin eliminarlos
5. **Auditoría**: Fechas de creación y actualización
6. **Consistencia**: Todos usan la misma fuente de verdad

## 📝 Buenas Prácticas

1. **NO eliminar códigos**: Usar `activo = FALSE` en su lugar
2. **Descripciones claras**: Usar terminología del SII
3. **Nomenclatura consistente**: Seguir convención de códigos W##, PPM##, FM##, etc.
4. **Validar antes de agregar**: Verificar que el código no exista
5. **Mantener sincronización**: Actualizar cuando el SII agregue nuevos códigos

## 🔍 Troubleshooting

### La tabla no existe
```bash
# Ejecutar migración SQL
psql -U postgres -d evolve -f migraciones/002_crear_tabla_codigos_observaciones_f29.sql
```

### Tabla vacía
```bash
# Re-ejecutar migración (tiene ON CONFLICT DO NOTHING)
# o ejecutar solo las instrucciones INSERT del archivo
```

### No se muestran códigos en la aplicación
1. Verificar que `activo = TRUE`
2. Revisar conexión a PostgreSQL en `configuracion.py`
3. Ejecutar script de verificación
4. Revisar logs de la aplicación

## 📞 Soporte

Para agregar o modificar códigos, contactar al administrador del sistema o consultar la documentación del SII sobre el Formulario 29.

---

**Última actualización**: 06 de octubre de 2025
**Versión de migración**: 002
