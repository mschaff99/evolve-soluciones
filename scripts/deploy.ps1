# Script de Deployment para Evolve Soluciones
# Ejecutar desde: C:\Users\Administrator\Desktop\evolve-soluciones

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DEPLOYMENT EVOLVE SOLUCIONES" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Variables
$projectPath = "C:\Users\Administrator\Desktop\evolve-soluciones"
$serviceName = "evolve-soluciones"
$nssmPath = "C:\tools\nssm\nssm.exe"

# Cambiar al directorio del proyecto
Set-Location $projectPath

Write-Host "[1/6] Verificando estado del servicio..." -ForegroundColor Yellow
& $nssmPath status $serviceName

Write-Host ""
Write-Host "[2/6] Deteniendo servicio..." -ForegroundColor Yellow
& $nssmPath stop $serviceName
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "[3/6] Actualizando código desde Git..." -ForegroundColor Yellow
git pull origin main

Write-Host ""
Write-Host "[4/6] Instalando/actualizando dependencias..." -ForegroundColor Yellow
& "$projectPath\.venv\Scripts\pip.exe" install -r requirements.txt --quiet

Write-Host ""
Write-Host "[5/6] Iniciando servicio..." -ForegroundColor Yellow
& $nssmPath start $serviceName
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "[6/6] Verificando estado final..." -ForegroundColor Yellow
& $nssmPath status $serviceName

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  DEPLOYMENT COMPLETADO" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Verificar aplicación en:" -ForegroundColor Cyan
Write-Host "  https://portal.evolveasesores.cl/salud" -ForegroundColor White
Write-Host ""

# Mostrar últimas líneas del log
Write-Host "Últimas líneas del log:" -ForegroundColor Cyan
Get-Content "$projectPath\logs\waitress-out.log" -Tail 10
