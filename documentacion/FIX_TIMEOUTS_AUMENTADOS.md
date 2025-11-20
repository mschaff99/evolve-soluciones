# Fix: Timeouts Aumentados para Procesos GCI Largos

**Fecha**: 3 de noviembre de 2025
**Problema**: Timeouts insuficientes causaban que procesos largos fueran abortados prematuramente.

## 🐛 Contexto del Problema

Después de implementar el fix del modal de progreso colgado, se identificó que los timeouts configurados eran insuficientes para empresas con muchos períodos tributarios:

- Empresas con >36 períodos de F29 pueden tardar 5-8 minutos en procesarse
- El proceso GCI necesita tiempo para autenticarse, descargar datos y guardar en BD
- Los timeouts de 30s-3min estaban matando procesos válidos antes de completar

## 📊 Timeouts Aumentados

### Comparación Antes/Después

| Componente | ANTES | DESPUÉS | Aumento |
|------------|-------|---------|---------|
| **JavaScript Polling Total** | 5 min | 10 min | +100% |
| **JavaScript Intervalo Checks** | 1-2s | 2-3s | +50% |
| **Proceso Python GCI** | 30s | 10 min | +1900% |
| **Flask REQUEST_TIMEOUT** | 3 min | 10 min | +233% |
| **Waitress channel_timeout** | 2 min | 10 min | +400% |

## 🔧 Cambios Implementados

### 1. JavaScript Frontend (`situacion-tributaria.js`)

```javascript
// ANTES
const maxTimeoutMs = 5 * 60 * 1000; // 5 minutos
pollingTimer = setTimeout(checkStatus, 1000);
pollingTimer = setTimeout(checkStatus, 2000);

// DESPUÉS
const maxTimeoutMs = 10 * 60 * 1000; // 10 minutos (aumentado para procesos lentos)
pollingTimer = setTimeout(checkStatus, 2000); // Primer check después de 2 segundos
pollingTimer = setTimeout(checkStatus, 3000); // 3 segundos entre checks (más tiempo para procesos pesados)
```

**Razón**: Dar más tiempo total y reducir frecuencia de polling para no saturar el servidor.

### 2. Servicio GCI Backend (`servicio_integracion_gci.py`)

```python
# ANTES
rc = proceso.wait(timeout=30)
logf.write("WARNING: Proceso GCI tardó más de 30 segundos, finalizando...\n")

# DESPUÉS
rc = proceso.wait(timeout=600)  # 10 minutos para procesos pesados (F29 + DJ)
logf.write("WARNING: Proceso GCI tardó más de 10 minutos, finalizando...\n")
```

**Razón**: El subproceso GCI necesita tiempo suficiente para:
- Iniciar navegador Playwright
- Autenticarse en SII
- Descargar F29 de múltiples períodos
- Procesar Declaraciones Juradas
- Guardar todos los datos en BD

### 3. Configuración Flask (`configuracion/configuracion.py`)

```python
# ANTES
REQUEST_TIMEOUT = 180  # 3 minutos para requests HTTP largos

# DESPUÉS
REQUEST_TIMEOUT = 600  # 10 minutos para requests HTTP largos (GCI puede tomar tiempo)
```

**Razón**: Flask no debe abortar requests mientras el proceso GCI está en ejecución.

### 4. Servidor Waitress (`wsgi_waitress.py`)

```python
# ANTES
serve(
    app,
    host='0.0.0.0',
    port=8080,
    threads=4,
    channel_timeout=120,  # 2 minutos
    cleanup_interval=30,
    url_scheme='http'
)

# DESPUÉS
serve(
    app,
    host='0.0.0.0',
    port=8080,
    threads=4,
    channel_timeout=600,  # 10 minutos - para procesos largos como GCI
    cleanup_interval=30,
    url_scheme='http'
)
```

**Razón**: Waitress no debe cerrar la conexión HTTP mientras el cliente está haciendo polling.

## 🎯 Archivos Modificados

1. **`aplicacion/estaticos/js/situacion-tributaria.js`**
   - Línea ~194: `maxTimeoutMs` 5min → 10min
   - Línea ~329: Intervalo polling 2s → 3s
   - Línea ~333: Primer check 1s → 2s

2. **`aplicacion/servicios/servicio_integracion_gci.py`**
   - Línea ~224: `timeout=30` → `timeout=600`
   - Línea ~227: Mensaje de warning actualizado

3. **`configuracion/configuracion.py`**
   - Línea ~88: `REQUEST_TIMEOUT = 180` → `REQUEST_TIMEOUT = 600`
   - Comentario explicativo añadido

4. **`wsgi_waitress.py`**
   - Línea ~49: `channel_timeout=120` → `channel_timeout=600`
   - Comentario explicativo añadido

## 🚀 Despliegue

### Pasos Manuales

```powershell
# 1. Navegar al directorio de producción
cd C:\inetpub\wwwroot\evolve-soluciones

# 2. Hacer backup
Copy-Item -Path aplicacion -Destination "aplicacion_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')" -Recurse

# 3. Actualizar código
git pull origin main

# 4. Reiniciar servicio
Restart-Service -Name "EvolveWaitress"

# 5. Verificar servicio
Get-Service -Name "EvolveWaitress" | Select-Object Status, DisplayName

# 6. Limpiar caché del navegador (IMPORTANTE)
# Ctrl+Shift+Delete → Limpiar caché
```

### Script Automatizado

```powershell
# Ejecutar desde scripts/
.\deploy-postupdate.ps1
```

## 🧪 Testing

### Casos de Prueba

####  Caso 1: Empresa Pequeña (<12 períodos)
- **Tiempo esperado**: 1-2 minutos
- **Comportamiento**: Debe completar normalmente y redirigir
- **Verificación**: Modal se cierra automáticamente

####  Caso 2: Empresa Mediana (12-36 períodos)
- **Tiempo esperado**: 3-5 minutos
- **Comportamiento**: Progreso visible, sin timeout
- **Verificación**: Barra de progreso avanza correctamente

####  Caso 3: Empresa Grande (>36 períodos)
- **Tiempo esperado**: 5-8 minutos
- **Comportamiento**: Debe completar sin timeout
- **Verificación**: Proceso finaliza exitosamente dentro de 10min

#### ⚠️ Caso 4: Proceso Extremadamente Lento (>10 minutos)
- **Tiempo esperado**: >10 minutos
- **Comportamiento**: Timeout con mensaje apropiado
- **Verificación**: Mensaje "Tiempo de espera excedido"
- **Acción**: Revisar logs, internet, o reducir períodos

## 📝 Consideraciones Importantes

### Para Desarrollo
- En desarrollo local los procesos suelen ser más rápidos
- Usar logs de consola (F12) para monitorear polling
- Verificar logs Python en `logs/gci_*.log`

### Para Producción
- **CRÍTICO**: Reiniciar Waitress después de cambios en `wsgi_waitress.py`
- Monitorear recursos del servidor (CPU, RAM)
- Considerar límite de períodos si hay problemas de performance

### Limitaciones Conocidas
- **10 minutos es el máximo razonable** para UX
- Si un proceso toma >10min regularmente, considerar:
  - Procesar períodos en lotes
  - Optimizar queries de BD
  - Revisar velocidad de internet
  - Verificar performance del sitio SII

##  Troubleshooting

### Proceso sigue haciendo timeout
1. Verificar logs en `logs/gci_*.log`
2. Revisar velocidad de internet
3. Verificar que Playwright está instalado: `python -m playwright install`
4. Probar con menos períodos primero
5. Revisar queries SQL por lentitud

### Modal se cierra prematuramente
1. Verificar que se reinició Waitress
2. Limpiar caché del navegador completamente
3. Revisar logs de consola (F12)
4. Verificar que no hay errores 500 en Network tab

### Servidor consume mucha RAM
1. Limitar threads de Waitress si es necesario
2. Monitorear procesos GCI con Process Explorer
3. Verificar que procesos viejos se cierran correctamente
4. Revisar logs por procesos zombie

## 📚 Referencias Técnicas

- **Waitress Documentation**: https://docs.pylonsproject.org/projects/waitress/en/stable/
- **Flask Timeouts**: https://flask.palletsprojects.com/en/2.3.x/config/
- **Subprocess Timeout**: https://docs.python.org/3/library/subprocess.html#subprocess.Popen.wait
- **JavaScript setTimeout**: https://developer.mozilla.org/en-US/docs/Web/API/setTimeout

## 📋 Checklist Post-Despliegue

- [ ] Código actualizado desde Git
- [ ] Servicio Waitress reiniciado
- [ ] Servicio corriendo correctamente
- [ ] Caché del navegador limpiado
- [ ] Prueba con empresa pequeña exitosa
- [ ] Prueba con empresa mediana exitosa
- [ ] Logs monitoreados por 24h
- [ ] Sin reportes de timeouts prematuros

---

**Última actualización**: 3 de noviembre de 2025
**Versión**: 2.0 (Timeouts aumentados a 10 minutos)
**Relacionado**: `FIX_MODAL_PROGRESO_COLGADO.md`
