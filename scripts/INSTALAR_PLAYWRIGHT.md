# Instalación de Playwright para GCI

## Problema
GCI necesita Playwright para automatizar la consulta del SII. El error indica:
```
BrowserType.launch: Executable doesn't exist at
C:\Windows\system32\config\systemprofile\AppData\Local\ms-playwright\chromium-1187\chrome-win\chrome.exe
```

Esto significa que Playwright no ha descargado los navegadores en el contexto donde GCI se ejecuta.

## Solución Rápida

### Opción 1: PowerShell (Recomendado)
```powershell
# Ejecutar como Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\scripts\instalar_playwright.ps1
```

### Opción 2: Python
```bash
# Ejecutar como Administrator
python scripts\instalar_playwright.py
```

### Opción 3: Manual (desde GCI)
```bash
# Entrar a la carpeta de GCI
cd C:\Users\Administrator\Desktop\Gestion-Consulta-Integral

# Activar venv
.venv\Scripts\activate

# Instalar Playwright
python -m playwright install
python -m playwright install-deps

# Desactivar venv
deactivate
```

## Verificar Instalación

```bash
# Verificar que los navegadores están instalados
python -m playwright install --with-deps

# O ejecutar un test simple
python -c "from playwright.sync_api import sync_playwright; print(' Playwright funcionando')"
```

## Notas Importantes

1. **Ejecutar como Administrator**: Playwright necesita permisos de admin
2. **Primer download es lento**: Los navegadores son ~500MB, paciencia
3. **GCI_PATH**: Si GCI está en otra ruta, define: `setx GCI_PATH "C:\ruta\a\GCI"`
4. **Usuario Administrator**: GCI se ejecuta bajo ese contexto, necesita Playwright ahí

## Solución de Problemas

### "Module not found: playwright"
- GCI no tiene playwright en su requirements.txt
- Instalar manualmente: `.venv\Scripts\pip install playwright`

### "Chromium not found"
- Ejecutar: `playwright install --with-deps`
- Puede tardar 10+ minutos

### Permisos denegados
- Abrir PowerShell/CMD como Administrator
- Ejecutar el script nuevamente

## Próximos Pasos

Después de instalar Playwright, GCI debería poder:
1.  Desencriptar contraseñas (ya funciona con `.encryption_key`)
2.  Automatizar consultas SII
3.  Generar reportes F29 y DJ

Luego prueba desde Evolve:
```bash
python aplicacion.py
# Selecciona opción 5 (F29 + DJ) y verifica que GCI se ejecute correctamente
```
