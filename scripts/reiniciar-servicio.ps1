# Script para reiniciar el servicio Evolve Soluciones
# Ejecutar como Administrador

$serviceName = "evolve-soluciones"
$nssmPath = "C:\tools\nssm\nssm.exe"

Write-Host "Reiniciando servicio $serviceName..." -ForegroundColor Yellow

& $nssmPath restart $serviceName

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "Estado del servicio:" -ForegroundColor Cyan
& $nssmPath status $serviceName

Write-Host ""
Write-Host "Listo! Verificar en: https://portal.evolveasesores.cl/salud" -ForegroundColor Green
