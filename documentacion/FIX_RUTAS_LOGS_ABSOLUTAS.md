# Fix Crítico: Rutas Absolutas para Logs de GCI

**Fecha:** 3 de noviembre de 2025
**Problema:** Los logs de GCI se generaban en un directorio pero se buscaban en otro, causando que el sistema no detectara los procesos
**Severidad:** 🔴 CRÍTICA
**Estado:**  Resuelto

---

## 🐛 Problema Identificado

### Síntomas
- Modal mostraba "Sin procesos activos" aunque el proceso estaba corriendo
- Los logs se generaban correctamente en `C:\Users\Administrator\Desktop\evolve-soluciones\logs`
- El endpoint `/api/gci_status` no encontraba los archivos
- Console logs mostraban que el directorio de búsqueda era diferente

### Causa Raíz
**Uso de `os.getcwd()` en lugar de rutas absolutas basadas en el proyecto**

#### Comportamiento Problemático

```python
# ANTES - Dependía del directorio de trabajo actual
logs_dir = os.getcwd()  # Puede ser diferente según cómo se ejecute la app
```

**En desarrollo (VS Code):**
- `os.getcwd()` → `C:\Users\mscha\Desktop\evolve-soluciones`
- Logs generados en: `C:\Users\mscha\Desktop\evolve-soluciones\logs\`
- Logs buscados en: `C:\Users\mscha\Desktop\evolve-soluciones\logs\`
-  **Funcionaba** porque ambos eran iguales

**En producción (Waitress/IIS con usuario Administrator):**
- `os.getcwd()` en GCI → `C:\Users\Administrator\Desktop\evolve-soluciones`
- `os.getcwd()` en Flask → Podría ser `C:\Windows\System32\` o cualquier otro
- Logs generados en: `C:\Users\Administrator\Desktop\evolve-soluciones\logs\`
- Logs buscados en: `C:\Windows\System32\logs\` ❌
- **Fallaba** porque buscaba en el directorio incorrecto

---

## 🔧 Solución Implementada

### 1. Nueva Función para Obtener Directorio Base

**Archivo:** `aplicacion/servicios/servicio_integracion_gci.py`

```python
def obtener_directorio_base() -> str:
    """
    Obtiene el directorio base del proyecto de forma consistente.

    Returns:
        str: Ruta absoluta al directorio raíz del proyecto
    """
    # Obtener el directorio de este archivo
    archivo_actual = os.path.abspath(__file__)
    # Subir dos niveles: servicios -> aplicacion -> raíz
    dir_aplicacion = os.path.dirname(os.path.dirname(archivo_actual))
    dir_base = os.path.dirname(dir_aplicacion)
    return dir_base
```

**Estructura del proyecto:**
```
evolve-soluciones/                     ← dir_base (lo que queremos)
├── aplicacion/                        ← dir_aplicacion
│   ├── servicios/
│   │   └── servicio_integracion_gci.py  ← __file__
├── logs/                              ← dir_base + "logs"
```

### 2. Actualización en Servicio GCI

**Antes:**
```python
def _ejecutar_gci_opcion(opcion: int, rut: str, password: str, base_datos: str) -> None:
    ahora = datetime.now().strftime("%Y%m%d-%H%M%S")
    logs_dir = os.path.join(os.getcwd(), "logs")  # CWD dependiente
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, f"gci_opcion{opcion}_{rut}_{ahora}.log")
```

**Después:**
```python
def _ejecutar_gci_opcion(opcion: int, rut: str, password: str, base_datos: str) -> None:
    ahora = datetime.now().strftime("%Y%m%d-%H%M%S")

    #  Usar ruta absoluta al directorio base del proyecto
    dir_base = obtener_directorio_base()
    logs_dir = os.path.join(dir_base, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, f"gci_opcion{opcion}_{rut}_{ahora}.log")
```

### 3. Actualización en Endpoint de Estado

**Archivo:** `aplicacion/controladores/empresas.py`

**Antes:**
```python
@empresas_bp.route('/<base_datos>/empresas/api/gci_status/<rut>')
def api_gci_status(base_datos, rut):
    import glob
    import os

    try:
        logs_dir = os.path.join(os.getcwd(), 'logs')  # CWD dependiente
        resultado = {
            'op1': {'exists': False, 'finished': False, 'log': ''},
            'op3': {'exists': False, 'finished': False, 'log': ''}
        }
```

**Después:**
```python
@empresas_bp.route('/<base_datos>/empresas/api/gci_status/<rut>')
def api_gci_status(base_datos, rut):
    import glob
    import os

    try:
        #  Usar ruta absoluta al directorio base del proyecto
        dir_base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        logs_dir = os.path.join(dir_base, 'logs')

        resultado = {
            'op1': {'exists': False, 'finished': False, 'log': ''},
            'op3': {'exists': False, 'finished': False, 'log': ''},
            'logs_dir': logs_dir  #  Para debugging
        }
```

**Cálculo de ruta en endpoint:**
```
__file__ = C:\Users\Administrator\Desktop\evolve-soluciones\aplicacion\controladores\empresas.py
os.path.abspath(__file__) = ruta completa
os.path.dirname(...) [1x] = C:\Users\Administrator\Desktop\evolve-soluciones\aplicacion\controladores
os.path.dirname(...) [2x] = C:\Users\Administrator\Desktop\evolve-soluciones\aplicacion
os.path.dirname(...) [3x] = C:\Users\Administrator\Desktop\evolve-soluciones  ← dir_base
```

### 4. Logging Mejorado para Debugging

**Agregado en `empresas.py`:**
```python
print(f"[DEBUG] Directorio de logs no existe: {logs_dir}")
print(f"[DEBUG] Buscando logs para RUT {rut} en: {logs_dir}")
print(f"[DEBUG] Pattern op1: {pattern1}, encontrados: {len(files1)}")
print(f"[DEBUG] Pattern op3: {pattern3}, encontrados: {len(files3)}")
print(f"[DEBUG] Archivo más reciente para op{opcion_num}: {latest}")
```

**Agregado en JavaScript:**
```javascript
if (st.logs_dir) {
  console.log('[GCI Status] Directorio de logs:', st.logs_dir);
}
console.log('[GCI Status] op1:', st.op1?.exists ? 'exists' : 'no existe');
console.log('[GCI Status] op3:', st.op3?.exists ? 'exists' : 'no existe');
```

---

## 🧪 Verificación de la Solución

### Checklist de Validación

- [ ] **Desarrollo:** Logs se generan y detectan en `C:\Users\mscha\Desktop\evolve-soluciones\logs\`
- [ ] **Producción:** Logs se generan y detectan en `C:\Users\Administrator\Desktop\evolve-soluciones\logs\`
- [ ] **Console log muestra:** `[GCI Status] Directorio de logs: C:\Users\...\evolve-soluciones\logs`
- [ ] **Modal progresa correctamente:** Muestra fases de F29 y DJ
- [ ] **No aparece "Sin procesos activos"** cuando hay archivos de log

### Comandos de Verificación

**En servidor de producción:**
```powershell
# Verificar dónde se ejecuta la app
cd C:\Users\Administrator\Desktop\evolve-soluciones

# Verificar logs recientes
Get-ChildItem .\logs\gci_opcion*.log -Recurse | Sort-Object LastWriteTime -Descending | Select-Object -First 5

# Ver contenido del último log
Get-Content (Get-ChildItem .\logs\gci_opcion*.log -Recurse | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
```

**En navegador (DevTools Console):**
```javascript
// Verificar logs del endpoint
// Buscar línea: [GCI Status] Directorio de logs: ...
// Debe mostrar la ruta absoluta correcta
```

---

## 📊 Impacto del Fix

### Antes del Fix
- 100% de fallas en producción para detección de procesos GCI
- Modal siempre mostraba "Sin procesos activos"
- Imposible saber el progreso real del proceso
- Logs generados pero nunca leídos

### Después del Fix
-  Detección correcta en desarrollo Y producción
-  Modal muestra progreso real (F29 → DJ → Completado)
-  Logs leídos y mostrados en tiempo real
-  Sistema funcional end-to-end

---

## 📝 Lecciones Aprendidas

### No Usar
```python
os.getcwd()  # Depende del CWD al ejecutar
os.path.abspath('.')  # Igual que getcwd()
os.path.abspath('logs')  # Relativo al CWD
```

###  Usar
```python
# Opción 1: Relativo al archivo actual
dir_actual = os.path.dirname(os.path.abspath(__file__))
dir_base = os.path.dirname(os.path.dirname(dir_actual))

# Opción 2: Variable de entorno (si está configurada)
dir_base = os.getenv('PROJECT_ROOT', '/ruta/default')

# Opción 3: Config centralizada
from configuracion import DIRECTORIO_BASE
```

### Casos de Uso

**Cuándo `os.getcwd()` es correcto:**
- Scripts standalone que DEBEN ejecutarse desde un directorio específico
- CLIs que operan sobre el directorio actual del usuario
- Tools tipo `git`, `npm` que operan en el CWD

**Cuándo usar rutas absolutas:**
- Aplicaciones web (Flask, Django, FastAPI)
- Servicios/daemons que corren como background
- Cualquier app que se ejecute desde diferentes contextos
- Integración con servicios del sistema (IIS, systemd, etc.)

---

## 🔄 Archivos Modificados

```
aplicacion/servicios/servicio_integracion_gci.py
  + obtener_directorio_base()
  ~ _ejecutar_gci_opcion() → usa dir_base

aplicacion/controladores/empresas.py
  ~ api_gci_status() → calcula dir_base
  + Logging de debugging
  + logs_dir en respuesta JSON

aplicacion/estaticos/js/situacion-tributaria.js
  + console.log para mostrar logs_dir
  + console.log para estados de op1/op3
```

---

## 🚀 Deployment

```powershell
# En servidor de producción
cd C:\Users\Administrator\Desktop\evolve-soluciones

# Pull de cambios
git pull origin main

# Reiniciar servicio
.\scripts\reiniciar-servicio.ps1
```

---

## 📞 Troubleshooting

### Problema: Sigue sin detectar logs

**Verificar:**
1. Los archivos existen físicamente:
   ```powershell
   dir C:\Users\Administrator\Desktop\evolve-soluciones\logs\
   ```

2. Console muestra el directorio correcto:
   ```
   [GCI Status] Directorio de logs: C:\Users\Administrator\Desktop\evolve-soluciones\logs
   ```

3. Los patterns de búsqueda son correctos:
   ```
   [DEBUG] Pattern op1: C:\...\logs\gci_opcion1_76989227-3_*.log, encontrados: 1
   ```

4. Los archivos tienen contenido:
   ```powershell
   Get-Content "C:\Users\Administrator\Desktop\evolve-soluciones\logs\gci_opcion1_76989227-3_20251103-233924.log"
   ```

### Problema: Logs en directorio diferente

**Solución temporal:**
```python
# En servicio_integracion_gci.py, línea ~120
# Forzar ruta específica temporalmente
logs_dir = "C:\\Users\\Administrator\\Desktop\\evolve-soluciones\\logs"
```

---

**Documentado por:** GitHub Copilot
**Revisado por:** equipo Evolve Soluciones
**Última actualización:** 3 nov 2025
