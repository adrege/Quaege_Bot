# Quaege Bot - Windows Build Script
# This script builds all executables using PyInstaller

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "    Quaege Bot - Windows Build Script" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists and activate it
$venvPath = ".\quaege tools.venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "[1/5] Activating virtual environment..." -ForegroundColor Yellow
    & $venvPath
} else {
    Write-Host "Warning: Virtual environment not found at 'quaege tools.venv'" -ForegroundColor Red
    Write-Host "Using system Python instead..." -ForegroundColor Yellow
}

# Check if PyInstaller is installed
Write-Host "[2/5] Checking PyInstaller installation..." -ForegroundColor Yellow
$pyinstallerCheck = python -m PyInstaller --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller not found. Installing..." -ForegroundColor Yellow
    python -m pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install PyInstaller!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "PyInstaller version: $pyinstallerCheck" -ForegroundColor Green
}

# Clean previous builds
Write-Host "[3/5] Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path ".\build") {
    Remove-Item -Recurse -Force ".\build"
}
if (Test-Path ".\dist") {
    Remove-Item -Recurse -Force ".\dist"
}

# Build using the spec file
Write-Host "[4/5] Building executables with PyInstaller..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Gray
python -m PyInstaller build_windows.spec --clean

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Build failed!" -ForegroundColor Red
    exit 1
}

# Copy additional files to dist folder
Write-Host "[5/5] Copying additional files..." -ForegroundColor Yellow

$distFolder = ".\dist\Quaege_Bot"

# Copy the rekeningen_split folder if it exists
if (Test-Path ".\rekeningen_split") {
    Copy-Item -Recurse -Force ".\rekeningen_split" $distFolder
    Write-Host "  ✓ Copied rekeningen_split folder" -ForegroundColor Green
}

# Ensure settings.json exists in dist
if (-not (Test-Path "$distFolder\settings.json")) {
    Copy-Item ".\settings.json" $distFolder -ErrorAction SilentlyContinue
    if ($?) {
        Write-Host "  ✓ Copied settings.json" -ForegroundColor Green
    } else {
        Write-Host "  ℹ Creating default settings.json" -ForegroundColor Gray
        @"
{
    "csv_path": "",
    "betaal_link": "",
    "text": "",
    "eigen_email": ""
}
"@ | Out-File -Encoding UTF8 "$distFolder\settings.json"
    }
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "    Build completed successfully!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Your distributable application is in: $distFolder" -ForegroundColor Cyan
Write-Host ""
Write-Host "Contents:" -ForegroundColor Yellow
Write-Host "  • Quaege_Tools.exe         (Main GUI - double-click to run)" -ForegroundColor White
Write-Host "  • split_rekeningen.exe     (Tool executable)" -ForegroundColor Gray
Write-Host "  • generate_transactions.exe (Tool executable)" -ForegroundColor Gray
Write-Host "  • test_saldo_update.exe    (Tool executable)" -ForegroundColor Gray
Write-Host "  • Stuur_saldo_updates.exe  (Tool executable)" -ForegroundColor Gray
Write-Host "  • config.py                (Configuration file)" -ForegroundColor Gray
Write-Host "  • settings.json            (User settings)" -ForegroundColor Gray
Write-Host "  • Adrege_logo.png          (Logo image)" -ForegroundColor Gray
Write-Host "  • rekeningen_split/        (HTML templates)" -ForegroundColor Gray
Write-Host ""
Write-Host "To distribute:" -ForegroundColor Yellow
Write-Host "  1. Zip the entire 'Quaege_Bot' folder" -ForegroundColor White
Write-Host "  2. Send to users" -ForegroundColor White
Write-Host "  3. They extract and run Quaege_Tools.exe" -ForegroundColor White
Write-Host ""
