# Post-Update helper for Evolve Soluciones
# - Reinicia el servicio (NSSM)
# - Valida salud local y externa
# - Muestra bindings IIS y estado de puertos

param(
    [string]$Servicio = "evolve-soluciones",
    [string]$Dominio = "portal.evolveasesores.cl",
    [string]$ProyectoRoot = "C:\\Users\\Administrator\\Desktop\\evolve-soluciones"
)

Write-Host "[INFO] Reiniciando servicio NSSM: $Servicio" -ForegroundColor Cyan
$Nssm = "C:\\tools\\nssm\\nssm.exe"
if (-not (Test-Path $Nssm)) { Write-Host "[WARN] NSSM no encontrado en $Nssm" -ForegroundColor Yellow }
else { & $Nssm restart $Servicio | Out-Host }

Start-Sleep -Seconds 2

Write-Host "[INFO] Comprobando que Waitress escuche en 127.0.0.1:8000" -ForegroundColor Cyan
(netstat -ano | findstr ":8000") | Out-Host

Write-Host "[INFO] Salud local (directo a Waitress)" -ForegroundColor Cyan
try { Invoke-WebRequest http://127.0.0.1:8000/salud -UseBasicParsing -TimeoutSec 10 | Select-Object StatusCode,Content | Out-Host }
catch { Write-Host "[ERROR] Salud local fallo: $($_.Exception.Message)" -ForegroundColor Red }

Write-Host "[INFO] Salud via IIS HTTP (Host header)" -ForegroundColor Cyan
try { Invoke-WebRequest http://127.0.0.1/salud -Headers @{Host=$Dominio} -UseBasicParsing -MaximumRedirection 0 -TimeoutSec 10 | Select-Object StatusCode,Headers | Out-Host }
catch { Write-Host "[WARN] HTTP probablemente redirige a HTTPS: $($_.Exception.Message)" -ForegroundColor Yellow }

Write-Host "[INFO] Salud via IIS HTTPS (Host header, ignorando validación)" -ForegroundColor Cyan
Add-Type @" 
using System.Net; using System.Security.Cryptography.X509Certificates;
public class TrustAllCertsPolicy : ICertificatePolicy { public bool CheckValidationResult(ServicePoint s, X509Certificate c, WebRequest r, int p){ return true; } }
"@
[System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy
try { Invoke-WebRequest https://127.0.0.1/salud -Headers @{Host=$Dominio} -UseBasicParsing -TimeoutSec 10 | Select-Object StatusCode,Content | Out-Host }
catch { Write-Host "[ERROR] HTTPS local fallo: $($_.Exception.Message)" -ForegroundColor Red }

Write-Host "[INFO] Bindings IIS del sitio portal-evolve" -ForegroundColor Cyan
Import-Module WebAdministration
Get-WebBinding -Name "portal-evolve" | Format-Table -AutoSize | Out-Host

Write-Host "[INFO] Puertos en escucha 80/443" -ForegroundColor Cyan
(netstat -ano | findstr ":80") | Out-Host
(netstat -ano | findstr ":443") | Out-Host

Write-Host "[INFO] Prueba externa (DNS debe apuntar): https://$Dominio/salud" -ForegroundColor Cyan
try { Invoke-WebRequest https://$Dominio/salud -UseBasicParsing -TimeoutSec 15 | Select-Object StatusCode,Content | Out-Host }
catch { Write-Host "[WARN] Prueba externa fallo: $($_.Exception.Message)" -ForegroundColor Yellow }

Write-Host "[DONE] Post-Update finalizado" -ForegroundColor Green
