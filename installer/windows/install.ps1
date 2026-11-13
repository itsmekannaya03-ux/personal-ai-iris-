param(
    [string]$Token = "",
    [string]$ApiUrl = "https://iris.ai/api"
)

$IrisDir = "$env:USERPROFILE\.iris"
$EngineDir = "$IrisDir\engine"
$ModelDir = "$EngineDir\iris.1 model"

Write-Host "╭──────────────────────────────────────╮" -ForegroundColor Cyan
Write-Host "│         Installing IRIS AI...        │" -ForegroundColor Cyan
Write-Host "╰──────────────────────────────────────╯" -ForegroundColor Cyan
Write-Host ""

# 1. Check Python
$py = Get-Command "python" -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "→ Installing Python 3.11..." -ForegroundColor Yellow
    $pyInstaller = "$env:TEMP\py_installer.exe"
    Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" -OutFile $pyInstaller -UseBasicParsing
    Start-Process -Wait -FilePath $pyInstaller -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1 Include_pip=1"
    Remove-Item -Force $pyInstaller -ErrorAction SilentlyContinue
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
}

# 2. Check if the AI runtime engine is installed
$IRIS Neural Core = Get-Command "IRIS Neural Core" -ErrorAction SilentlyContinue
if (-not $IRIS Neural Core) {
    Write-Host "→ Installing IRIS Neural Core AI engine..." -ForegroundColor Yellow
    $installer = "$env:TEMP\IRIS Neural CoreSetup.exe"
    Invoke-WebRequest -Uri "https://IRIS Neural Core.com/download/IRIS Neural CoreSetup.exe" -OutFile $installer -UseBasicParsing
    Start-Process -Wait -FilePath $installer -ArgumentList "/silent"
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
}

# 3. Create IRIS directory
New-Item -ItemType Directory -Path $IrisDir -Force | Out-Null
New-Item -ItemType Directory -Path "$IrisDir\chroma" -Force | Out-Null
New-Item -ItemType Directory -Path "$IrisDir\logs" -Force | Out-Null
New-Item -ItemType Directory -Path "$IrisDir\memory" -Force | Out-Null

# 4. Pull the AI model
Write-Host "→ Downloading AI model (llama3.2:3b)..." -ForegroundColor Yellow
IRIS Neural Core pull llama3.2:3b 2>$null
if ($?) {
    Write-Host "  Model ready!" -ForegroundColor Green
}

# 5. Download profile if token is provided
if ($Token) {
    Write-Host "→ Fetching your profile from dashboard..." -ForegroundColor Yellow
    try {
        $response = Invoke-RestMethod -Uri "$ApiUrl/installer/$Token"
        $response.profile | ConvertTo-Json -Depth 5 | Set-Content "$IrisDir\profile.json"
        if ($response.theme) {
            $themeJson = @{ "theme" = $response.theme } | ConvertTo-Json
            Set-Content "$IrisDir\.theme.json" -Value $themeJson
        }
        Write-Host "  Welcome, $($response.profile.name)!" -ForegroundColor Green
        Write-Host "  Your AI will be named: $($response.ai_name)" -ForegroundColor Green
    } catch {
        Write-Host "  Could not fetch profile. Using defaults." -ForegroundColor Yellow
    }
} else {
    Write-Host "  [No token provided — using default profile]" -ForegroundColor Yellow
}

# 6. Install Python dependencies
if (Test-Path "$PSScriptRoot\..\requirements.txt") {
    Write-Host "→ Installing engine dependencies..." -ForegroundColor Yellow
    pip install -r "$PSScriptRoot\..\requirements.txt" 2>$null
    Write-Host "  Dependencies installed!" -ForegroundColor Green
} else {
    Write-Host "→ Creating engine directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $EngineDir -Force | Out-Null
    pip install fastapi uvicorn websockets requests aiohttp opencv-python onnxruntime numpy pillow edge-tts sounddevice soundfile pywebview pyautogui pywin32 psutil 2>$null
    Write-Host "  Dependencies installed!" -ForegroundColor Green
}

# 7. Create startup script
if ($Token -and $response) { $displayName = $response.ai_name } else { $displayName = "IRIS" }
@"
@echo off
cd /d "$EngineDir"
echo   $displayName is starting...
python run_server.py
"@ | Out-File -FilePath "$IrisDir\start.bat" -Encoding ASCII

# 8. Create CLI alias
$profilePath = "$env:USERPROFILE\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1"
if (Test-Path $profilePath) {
    Add-Content $profilePath "`nfunction iris { python `"$EngineDir\run_server.py`" @args }"
} else {
    New-Item -ItemType Directory -Path (Split-Path $profilePath) -Force | Out-Null
    Set-Content $profilePath "function iris { python `"$EngineDir\run_server.py`" @args }"
}

# 9. Start the engine
Write-Host ""
Write-Host "╭──────────────────────────────────────╮" -ForegroundColor Green
if ($Token -and $response) { $displayName2 = "$($response.ai_name) AI" } else { $displayName2 = "IRIS AI" }
Write-Host "│  $((' ' + $displayName2).PadRight(38))│" -ForegroundColor Green
Write-Host "│  installed successfully!             │" -ForegroundColor Green
Write-Host "│                                      │" -ForegroundColor Green
Write-Host "│  Dashboard: http://localhost:5743     │" -ForegroundColor Green
Write-Host "│  CLI:       iris                     │" -ForegroundColor Green
Write-Host "╰──────────────────────────────────────╯" -ForegroundColor Green

Write-Host ""
Write-Host "→ Starting AI..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit -Command python `"$EngineDir\run_server.py`""
