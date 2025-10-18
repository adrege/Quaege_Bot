# Builds standalone Windows executables using PyInstaller
param(
    [switch]$OneFile = $false,
    [switch]$NoConsole = $true
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Ensure-Venv {
    if (-not (Test-Path -Path '.\\quaege tools.venv\\Scripts\\Activate.ps1')) {
        Write-Host 'Python venv not found. Please create or set your environment, or edit this script.' -ForegroundColor Yellow
    } else {
        . '.\\quaege tools.venv\\Scripts\\Activate.ps1'
    }
}

function Ensure-PyInstaller {
    if (-not (python -c "import PyInstaller" 2>$null)) {
        Write-Host 'Installing PyInstaller...'
        pip install --upgrade pip
        pip install pyinstaller
    }
}

function Build-App {
    param([string]$Entry, [string]$Name)
    $common = @()
    if ($NoConsole) { $common += '--noconsole' }
    if ($OneFile) { $common += '--onefile' } else { $common += '--onedir' }
    $distPath = Join-Path (Get-Location) 'dist/QuaegeTools'
    if (-not (Test-Path $distPath)) { New-Item -ItemType Directory -Force -Path $distPath | Out-Null }
    # Data: bundle settings template, logo, and html folder
    $common += @( 
        "--add-data","settings.json;.",
        "--add-data","Adrege_logo.png;.",
        "--add-data","rekeningen_split;rekeningen_split"
    )
    # Hidden imports for scientific stack
    $hidden = @( '--hidden-import','pandas','--hidden-import','numpy','--hidden-import','openpyxl','--hidden-import','dateutil','--hidden-import','pytz','--hidden-import','bs4','--hidden-import','pypdf' )

    pyinstaller @common @hidden --distpath $distPath --name $Name $Entry
}

Push-Location $PSScriptRoot
try {
    Ensure-Venv
    Ensure-PyInstaller

    # Clean previous builds
    if (Test-Path 'build') { Remove-Item -Recurse -Force 'build' }
    if (Test-Path 'dist') { Remove-Item -Recurse -Force 'dist' }

    # Build GUI
    Build-App -Entry 'main_gui.py' -Name 'QuaegeTools'
    # Build tools (CLI)
    Build-App -Entry 'scripts\\split_rekeningen.py' -Name 'split_rekeningen'
    Build-App -Entry 'scripts\\generate_transactions.py' -Name 'generate_transactions'
    Build-App -Entry 'scripts\\test_saldo_update.py' -Name 'test_saldo_update'
    Build-App -Entry 'scripts\\Stuur_saldo_updates.py' -Name 'Stuur_saldo_updates'

    Write-Host "Build complete. See the 'dist' folder." -ForegroundColor Green
}
finally {
    Pop-Location
}
