# Fix: Modal de Progreso Quedaba Colgado

**Fecha**: 2025-11-03
**Módulo**: Situación Tributaria / Consulta Nueva Empresa
**Archivo**: `aplicacion/estaticos/js/situacion-tributaria.js`

## Problema

El modal de progreso de la consulta de nueva empresa se quedaba colgado mostrando:
- Título: "Guardando credencial..."
- Descripción: "Configurando acceso al SII..."
- Barra de progreso: 10%

Esto ocurría **después de que el proceso backend había terminado exitosamente**.

### Síntomas

1. El usuario veía el modal colgado indefinidamente
2. La empresa SÍ se consultaba correctamente en el backend
3. Los datos F29 y DJ SÍ se descargaban y guardaban
4. El modal nunca pasaba del 10% ni redireccionaba
5. Al recargar manualmente, los datos aparecían correctos

## Causa Raíz

El código de polling tenía **múltiples problemas**:

### 1. Condición de Finalización Incorrecta
```javascript
// ANTES (INCORRECTO):
if (st.op3 && st.op3.finished && esperadoOp3 && !esperadoOp1) {
  // Solo se ejecutaba si se cumplía la secuencia exacta
}
```

Esta condición requería que:
- `esperadoOp1 = false` (que op1 se marcara como visto terminado)
- `esperadoOp3 = true` (que op3 NO se hubiera marcado como visto)

**Problema**: Si el backend terminaba AMBOS procesos muy rápido (antes del primer poll o entre polls), la condición nunca se cumplía porque `esperadoOp1` podía no haberse actualizado a tiempo.

### 2. Timer No Se Limpiaba Correctamente
```javascript
// ANTES (INCORRECTO):
clearTimeout(pollingTimer);
// ... pero luego al final:
pollingTimer = setTimeout(checkStatus, 2000); // Se volvía a ejecutar!
```

El `clearTimeout` se ejecutaba, pero la función seguía fluyendo y al final se volvía a programar el polling.

### 3. Sin Control de Estado del Polling
No había un flag que indicara si el polling debía seguir activo o no, lo que causaba que:
- Se pudieran ejecutar múltiples instancias
- No se pudiera detener correctamente
- El timer se reprogramara incluso después de errores

### 4. Sin Manejo de Procesos Ya Terminados
Si el backend procesaba todo muy rápido, el primer poll podía encontrar ambos procesos terminados, pero el código no lo manejaba porque esperaba una secuencia gradual.

## Solución Implementada

### 1. Flag de Control `pollingActivo`
```javascript
let pollingActivo = true;

async function checkStatus() {
  // Primera línea: verificar si debemos continuar
  if (!pollingActivo) {
    if (pollingTimer) clearTimeout(pollingTimer);
    return;
  }
  // ... resto del código
}
```

### 2. Verificación Inmediata de Finalización
```javascript
// NUEVO: Verificar primero si ambos terminaron (cualquier orden)
const op1Terminado = st.op1 && st.op1.finished;
const op3Terminado = st.op3 && st.op3.finished;

if (op1Terminado && op3Terminado) {
  pollingActivo = false;
  if (pollingTimer) clearTimeout(pollingTimer);

  // Mostrar 100% y redirigir
  // ...
  return;
}
```

Esto captura el caso donde ambos procesos terminan antes de que se ejecute el primer poll o entre polls.

### 3. Limpieza Correcta del Timer
```javascript
// En TODOS los casos de finalización:
pollingActivo = false;  // Marcar como inactivo PRIMERO
if (pollingTimer) clearTimeout(pollingTimer);  // Limpiar timer
// ... resto de la lógica
return;  // Salir inmediatamente
```

Y al final de la función:
```javascript
// Solo continuar si sigue activo
if (pollingActivo) {
  pollingTimer = setTimeout(checkStatus, 2000);
}
```

### 4. Detección de Procesos Inexistentes
```javascript
const hayProcesos = (st.op1 && st.op1.exists) || (st.op3 && st.op3.exists);
if (!hayProcesos && (Date.now() - startTime > 10000)) {
  pollingActivo = false;
  if (pollingTimer) clearTimeout(pollingTimer);
  // Mostrar mensaje de "Sin procesos activos"
  return;
}
```

Esto detecta casos donde el backend:
- Falló sin reportar error
- Terminó antes del primer poll
- No creó los archivos de estado

## Casos Cubiertos

###  Caso 1: Proceso Normal (Secuencial)
1. Poll 1: op1 en progreso → 30%
2. Poll 2: op1 terminado → 60%
3. Poll 3: op3 en progreso → 80%
4. Poll 4: op3 terminado → 100% → redirección

###  Caso 2: Proceso Muy Rápido
1. Poll 1: ambos terminados → 100% inmediato → redirección

###  Caso 3: Error en Backend
1. Poll 1: no hay procesos activos después de 10s → mensaje de advertencia

###  Caso 4: Timeout
1. Después de 5 minutos → mensaje de timeout → botón cerrar visible

###  Caso 5: Error de Red
1. Fetch falla → catch → mensaje de error → botón cerrar visible

## Cambios en el Código

**Archivo**: `aplicacion/estaticos/js/situacion-tributaria.js`

**Líneas modificadas**: ~190-300 (función `ejecutarConsultaNueva`)

**Cambios principales**:
1.  Agregado `let pollingActivo = true`
2.  Verificación al inicio de `checkStatus()` para salir si inactivo
3.  Verificación temprana de `op1Terminado && op3Terminado`
4.  `pollingActivo = false` en TODOS los casos de finalización
5.  Limpieza del timer antes de `return` en todos los casos
6.  Detección de procesos inexistentes después de 10s
7.  Condicional `if (pollingActivo)` antes de reprogramar el polling

## Deployment

### Opción 1: Script Automatizado
```powershell
.\scripts\fix-modal-progreso.ps1
```

### Opción 2: Manual
1. Crear backup:
   ```powershell
   Copy-Item "C:\inetpub\wwwroot\evolve-soluciones\aplicacion\estaticos\js\situacion-tributaria.js" `
             "C:\inetpub\wwwroot\evolve-soluciones\aplicacion\estaticos\js\situacion-tributaria.js.backup"
   ```

2. Copiar archivo corregido:
   ```powershell
   Copy-Item "aplicacion\estaticos\js\situacion-tributaria.js" `
             "C:\inetpub\wwwroot\evolve-soluciones\aplicacion\estaticos\js\situacion-tributaria.js" -Force
   ```

3. **No requiere reiniciar el servidor**

4. Usuarios deben refrescar con `Ctrl+F5` para limpiar caché

## Testing

### Casos de Prueba

1. **Proceso normal**:
   - Consultar empresa nueva
   - Verificar que el progreso avanza: 10% → 30% → 60% → 80% → 100%
   - Verificar redirección automática

2. **Proceso rápido**:
   - Empresa pequeña con pocos períodos
   - Verificar que pasa directo a 100% y redirige

3. **Error de credencial**:
   - Ingresar credencial incorrecta
   - Verificar mensaje de error y botón cerrar visible

4. **RUT ya existente con procesos completos**:
   - Consultar RUT que ya existe
   - Verificar que detecta "Sin procesos activos" o redirige

## Prevención Futura

### Checklist para Polling
- [ ] Usar flag de control (`activo`, `enProceso`, etc.)
- [ ] Verificar flag al inicio de cada iteración
- [ ] Limpiar timer ANTES de return en todos los casos
- [ ] Desactivar flag ANTES de limpiar timer
- [ ] Usar condicional antes de reprogramar polling
- [ ] Manejar caso de "proceso ya terminado" antes del primer poll
- [ ] Timeout apropiado con limpieza correcta
- [ ] Error handling con limpieza en catch

### Pattern Recomendado
```javascript
let pollingActivo = true;

async function poll() {
  if (!pollingActivo) {
    clearTimer();
    return;
  }

  try {
    const result = await fetch(...);

    // Verificar condición de finalización PRIMERO
    if (resultado.terminado) {
      pollingActivo = false;
      clearTimer();
      // Acción final
      return;
    }

    // Actualizar UI progreso

  } catch (e) {
    pollingActivo = false;
    clearTimer();
    // Mostrar error
    return;
  }

  // Solo continuar si sigue activo
  if (pollingActivo) {
    timer = setTimeout(poll, intervalo);
  }
}
```

## Referencias

- Issue: Modal colgado en "Configurando acceso al SII..." 10%
- Archivo: `aplicacion/estaticos/js/situacion-tributaria.js`
- Función: `ejecutarConsultaNueva()`
- Script deploy: `scripts/fix-modal-progreso.ps1`
