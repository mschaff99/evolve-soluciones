# Script de PowerShell para iniciar Evolve Soluciones con Tunnelmole
Write-Host ""
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "  EVOLVE SOLUCIONES - INICIANDO CON TÚNEL PÚBLICO" -ForegroundColor Yellow
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host ""

# Cambiar al directorio del proyecto
Set-Location "C:\Users\Administrator\Desktop\evolve-soluciones"

Write-Host "⚡ Iniciando aplicación Flask..." -ForegroundColor Green
Start-Process -FilePath "python" -ArgumentList "aplicacion.py" -WindowStyle Normal

Write-Host "⏳ Esperando 8 segundos para que Flask inicie..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

Write-Host "🚇 Creando túnel público con Tunnelmole..." -ForegroundColor Magenta
Write-Host ""
Write-Host " Tu aplicación estará disponible en la URL que muestre Tunnelmole" -ForegroundColor Cyan
Write-Host "🌐 Comparte esa URL para acceso externo" -ForegroundColor Cyan
Write-Host "💚 GRATIS y sin límites de tiempo!" -ForegroundColor Green
Write-Host ""
Write-Host "Para detener: Presiona Ctrl+C" -ForegroundColor Red
Write-Host ""

tunnelmole 5000

Read-Host "Presiona Enter para continuar"
