# Script para instalar Playwright en GCI
# ==========================================
# Ejecutar como Administrator
# Instala los navegadores de Playwright en el contexto del usuario actual

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Instalador de Playwright para GCI" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Rutas posibles de GCI
$rutas_gci = @(
    "C:\Users\Administrator\Desktop\Gestion-Consulta-Integral",
    "c:\Users\mscha\Desktop\Gestion-Consulta-Integral"
)

# Encontrar GCI
$dir_gci = $null
foreach ($ruta in $rutas_gci) {
    if (Test-Path $ruta) {
        $dir_gci = $ruta
        Write-Host " GCI encontrado en: $dir_gci" -ForegroundColor Green
        break
    }
}

if (-not $dir_gci) {
    Write-Host "ERROR: No se encontró GCI en ninguna ruta:" -ForegroundColor Red
    $rutas_gci | ForEach-Object { Write-Host "   - $_" }
    Write-Host "Define la variable de entorno GCI_PATH si está en otra ubicación" -ForegroundColor Yellow
    exit 1
}

# Detectar venv de GCI
$venv_paths = @(
    "$dir_gci\.venv\Scripts\python.exe",
    "$dir_gci\venv\Scripts\python.exe"
)

$python_gci = $null
foreach ($venv_py in $venv_paths) {
    if (Test-Path $venv_py) {
        $python_gci = $venv_py
        Write-Host " Python de GCI encontrado: $python_gci" -ForegroundColor Green
        break
    }
}

if (-not $python_gci) {
    Write-Host "ERROR: No se encontró venv de GCI en:" -ForegroundColor Red
    $venv_paths | ForEach-Object { Write-Host "   - $_" }
    Write-Host "Asegúrate de que GCI tiene un entorno virtual activado" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "🚀 Instalando Playwright..." -ForegroundColor Cyan
Write-Host "Directorio de trabajo: $dir_gci" -ForegroundColor Cyan
Write-Host "Python a usar: $python_gci" -ForegroundColor Cyan
Write-Host ""

# Cambiar al directorio de GCI
Push-Location $dir_gci

try {
    # Ejecutar playwright install
    & $python_gci -m playwright install

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host " Playwright instalado exitosamente" -ForegroundColor Green
        Write-Host ""
        Write-Host "Navegadores instalados:" -ForegroundColor Green
        & $python_gci -m playwright install-deps --help
    }
    else {
        Write-Host ""
        Write-Host "Error durante la instalación de Playwright" -ForegroundColor Red
        Write-Host "Exit code: $LASTEXITCODE" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "Excepción: $_" -ForegroundColor Red
    exit 1
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " Instalación completada" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
