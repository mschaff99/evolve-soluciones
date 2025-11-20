# Estados del Formulario 29 (F29)

## 📊 Descripción

Este documento describe los diferentes estados que puede tener un período tributario en el sistema de Consulta Integral F29.

## 🎨 Estados y Símbolos

### Tabla de Estados

| Símbolo | Descripción | Total Observaciones | Color Badge | Ícono |
|---------|-------------|---------------------|-------------|-------|
| `✓` | OK, sin observación | 0 | Verde (`bg-success`) | `fa-check` |
| `X` | Con observación | > 0 | Rojo/Rosa (`bg-danger`) | `fa-times` |
| `⚠️` | Sin procesar por SII | 0 | Amarillo/Naranja (`bg-warning badge-sin-procesar`) | `fa-exclamation-triangle` |
| `-` | Guión/neutral | 0 | Gris (`bg-secondary`) | `fa-minus` |
| `` (vacío) | Vacío/futuro/sin datos | 0 | Transparente (`bg-light`) | `fa-circle` |

##  Detalles de Cada Estado

### ✓ OK, Sin Observación
- **Significado**: El período fue procesado por el SII y no tiene observaciones
- **Acción del usuario**: No requiere acción
- **Color**: Verde (#16A39A)
- **Ejemplo**: Declaración enviada y aceptada sin problemas

### X Con Observación
- **Significado**: El período tiene observaciones que deben ser revisadas
- **Acción del usuario**: Hacer clic para ver detalles de observaciones en modal
- **Color**: Rojo/Rosa (#E13278)
- **Tooltip**: Muestra lista de códigos y descripciones de observaciones al pasar el mouse
- **Badge contador**: Muestra el número total de observaciones
- **Ejemplo**: "W39: Control Precautorio Proveedores"

### ⚠️ Sin Procesar por SII
- **Significado**: El período fue declarado pero el SII aún no lo ha procesado
- **Acción del usuario**: Esperar a que el SII procese la declaración
- **Color**: Amarillo/Naranja (#FFA500)
- **Nota**: Es normal en períodos recientes o durante alta carga del SII
- **Ejemplo**: Declaración enviada hace menos de 24 horas

### - Guión/Neutral
- **Significado**: Estado neutral, período sin información específica
- **Acción del usuario**: No requiere acción
- **Color**: Gris (#6b7280)
- **Ejemplo**: Período informativo sin declaración requerida

### (Vacío) Sin Datos
- **Significado**: No hay información para este período
- **Acción del usuario**: No requiere acción
- **Color**: Transparente con borde
- **Ejemplo**: Períodos futuros o empresa sin actividad

## 🔄 Flujo de Estados Típico

```
1. (Vacío) → Sin datos
          ↓
2. ⚠️ → Declaración enviada, esperando procesamiento SII
          ↓
3. ✓ → SII procesó sin observaciones
   O
   X → SII procesó con observaciones
```

## 💻 Implementación Técnica

### HTML Template (Jinja2)

```jinja2
{% if datos_periodo.tabla_resultados == '✓' %}
    <span class="badge bg-success" title="OK, sin observaciones">
        <i class="fas fa-check"></i>
    </span>
{% elif datos_periodo.tabla_resultados == '⚠️' %}
    <span class="badge bg-warning badge-sin-procesar" title="Sin procesar por SII">
        <i class="fas fa-exclamation-triangle"></i>
    </span>
{% elif datos_periodo.tabla_resultados == 'X' %}
    <button class="btn btn-sm btn-danger btn-observaciones" ...>
        <i class="fas fa-times"></i>
        <span class="badge badge-count">{{ total_observaciones }}</span>
    </button>
{% elif datos_periodo.tabla_resultados == '-' %}
    <span class="badge bg-secondary" title="Período neutral">
        <i class="fas fa-minus"></i>
    </span>
{% else %}
    <span class="badge bg-light text-dark">
        <i class="fas fa-circle"></i>
    </span>
{% endif %}
```

### CSS

```css
/* OK, sin observación */
.badge.bg-success {
    background: #16A39A !important;
    color: white !important;
}

/* Sin procesar por SII */
.badge.bg-warning.badge-sin-procesar {
    background: #FFA500 !important;
    color: #000 !important;
    font-weight: 600;
}

/* Con observaciones */
.badge.bg-danger {
    background: #E13278 !important;
    color: white !important;
}
```

## 📝 Base de Datos

### Campo: `tabla_resultados`

Tipo: `VARCHAR` o `CHAR(1)`

Valores posibles almacenados en la columna `tabla_resultados` de la tabla `consulta_integral`:

```sql
-- Ejemplos de valores en BD
'✓'   -- OK
'X'   -- Con observación
'⚠️'  -- Sin procesar (nuevo)
'-'   -- Neutral
''    -- Vacío
```

### Consulta de Ejemplo

```sql
SELECT
    rut,
    periodo,
    tabla_resultados,
    CASE
        WHEN tabla_resultados = '✓' THEN 'OK'
        WHEN tabla_resultados = 'X' THEN 'Con Observación'
        WHEN tabla_resultados = '⚠️' THEN 'Sin Procesar SII'
        WHEN tabla_resultados = '-' THEN 'Neutral'
        ELSE 'Sin Datos'
    END as estado_descripcion,
    (SELECT COUNT(*) FROM observaciones WHERE consulta_id = ci.id) as total_obs
FROM stratex.consulta_integral ci
WHERE periodo = 202410;
```

##  UX/UI Consideraciones

### Tooltips
- Todos los badges tienen tooltip explicativo
- El badge de observaciones (X) muestra detalles al hacer hover
- Tooltips se cargan dinámicamente con Bootstrap

### Interactividad
- Solo el badge 'X' (Con observaciones) es clickeable
- Click abre modal con detalles completos
- Otros badges son informativos (no clickeables)

### Accesibilidad
- Iconos con significado visual claro
- Colores contrastantes (WCAG AA)
- Títulos descriptivos en todos los elementos
- Texto alternativo en iconos

## 📊 Estadísticas de Uso

### Conteo por Estado

```python
# En el template
{% set ns = namespace(ok=0, con_obs=0, sin_procesar=0, neutral=0, vacio=0) %}
{% for periodo in periodos %}
    {% if periodo.tabla_resultados == '✓' %}
        {% set ns.ok = ns.ok + 1 %}
    {% elif periodo.tabla_resultados == 'X' %}
        {% set ns.con_obs = ns.con_obs + 1 %}
    {% elif periodo.tabla_resultados == '⚠️' %}
        {% set ns.sin_procesar = ns.sin_procesar + 1 %}
    {% elif periodo.tabla_resultados == '-' %}
        {% set ns.neutral = ns.neutral + 1 %}
    {% else %}
        {% set ns.vacio = ns.vacio + 1 %}
    {% endif %}
{% endfor %}
```

## 🔧 Mantenimiento

### Agregar Nuevo Estado

1. **Backend**: Agregar valor en la base de datos
2. **Template**: Agregar condición en el bloque `{% if %}`
3. **CSS**: Definir estilos para el nuevo badge
4. **Documentación**: Actualizar este archivo
5. **Testing**: Verificar visualización y comportamiento

### Modificar Estado Existente

1. Actualizar CSS para cambios visuales
2. Actualizar tooltips en el template
3. Actualizar documentación
4. Comunicar cambios al equipo

## 📞 Soporte

Para preguntas sobre estados o agregar nuevos estados, contactar al equipo de desarrollo.

---

**Última actualización**: 08 de octubre de 2025
**Versión**: 1.1
**Autor**: Evolve Soluciones
