#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Script para desplegar el fix del modal de progreso que se quedaba colgado.

.DESCRIPTION
    Este script copia el archivo JavaScript corregido al servidor de producción.
    El problema era que el polling no se detenía correctamente cuando los procesos finalizaban.

.NOTES
    Autor: Evolve Soluciones
    Fecha: 2025-11-03
    Fix: Modal de progreso quedaba en "Configurando acceso al SII..." al 10%
#>

param(
    [string]$ServidorProduccion = "localhost",
    [string]$RutaProduccion = "C:\inetpub\wwwroot\evolve-soluciones"
)

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host " FIX: Modal de Progreso Colgado" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que existe el archivo corregido
$archivoLocal = "$PSScriptRoot\..\aplicacion\estaticos\js\situacion-tributaria.js"
if (-not (Test-Path $archivoLocal)) {
    Write-Host "ERROR: No se encuentra el archivo $archivoLocal" -ForegroundColor Red
    exit 1
}

Write-Host "[1/3] Archivo encontrado: $archivoLocal" -ForegroundColor Green

# Crear backup en producción
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$rutaBackup = "$RutaProduccion\aplicacion\estaticos\js\situacion-tributaria.js.backup_$timestamp"

if (Test-Path "$RutaProduccion\aplicacion\estaticos\js\situacion-tributaria.js") {
    Write-Host "[2/3] Creando backup en: $rutaBackup" -ForegroundColor Yellow
    Copy-Item "$RutaProduccion\aplicacion\estaticos\js\situacion-tributaria.js" -Destination $rutaBackup
} else {
    Write-Host "[2/3] No existe archivo anterior (primera vez)" -ForegroundColor Yellow
}

# Copiar archivo corregido
Write-Host "[3/3] Copiando archivo corregido a producción..." -ForegroundColor Cyan
Copy-Item $archivoLocal -Destination "$RutaProduccion\aplicacion\estaticos\js\situacion-tributaria.js" -Force

Write-Host ""
Write-Host "Despliegue completado exitosamente" -ForegroundColor Green
Write-Host ""
Write-Host "Cambios realizados:" -ForegroundColor Cyan
Write-Host "  - Agregado flag 'pollingActivo' para controlar el polling" -ForegroundColor White
Write-Host "  - Verificación inmediata si ambos procesos (op1 y op3) están terminados" -ForegroundColor White
Write-Host "  - Limpieza correcta del timer antes de redireccionar" -ForegroundColor White
Write-Host "  - Detección de procesos inexistentes después de 10 segundos" -ForegroundColor White
Write-Host "  - Prevención de múltiples ejecuciones del polling" -ForegroundColor White
Write-Host ""
Write-Host "NOTA: No requiere reiniciar el servidor. Los cambios se aplican inmediatamente." -ForegroundColor Yellow
Write-Host "      Los usuarios deben refrescar la página (Ctrl+F5) para ver los cambios." -ForegroundColor Yellow
Write-Host ""
