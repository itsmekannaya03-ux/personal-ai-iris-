param(
    [string]$Token = "",
    [string]$ApiUrl = "https://igris.ai/api"
)

$IgrisDir = "$env:USERPROFILE\.igris"
$EngineDir = "$IgrisDir\engine"

Write-Host "╭──────────────────────────────────────╮" -ForegroundColor Cyan
Write-Host "│        Installing IGRIS AI...        │" -ForegroundColor Cyan
Write-Host "╰──────────────────────────────────────╯" -ForegroundColor Cyan
Write-Host ""

# 1. Check if Ollama is installed
$ollama = Get-Command "ollama" -ErrorAction SilentlyContinue
if (-not $ollama) {
    Write-Host "→ Installing Ollama..." -ForegroundColor Yellow
    $installer = "$env:TEMP\OllamaSetup.exe"
    Invoke-WebRequest -Uri "https://ollama.com/download/OllamaSetup.exe" -OutFile $installer
    Start-Process -Wait -FilePath $installer -ArgumentList "/silent"
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
}

# 2. Create IGRIS directory
New-Item -ItemType Directory -Path $IgrisDir -Force | Out-Null
New-Item -ItemType Directory -Path "$IgrisDir\chroma" -Force | Out-Null
New-Item -ItemType Directory -Path "$IgrisDir\logs" -Force | Out-Null

# 3. Pull the AI model
Write-Host "→ Pulling AI model (llama3.2:3b)..." -ForegroundColor Yellow
ollama pull llama3.2:3b 2>$null
if ($?) {
    Write-Host "  Model ready!" -ForegroundColor Green
}

# 4. Download profile if token is provided
if ($Token) {
    Write-Host "→ Fetching your profile..." -ForegroundColor Yellow
    try {
        $response = Invoke-RestMethod -Uri "$ApiUrl/installer/$Token"
        $response.profile | ConvertTo-Json -Depth 5 | Set-Content "$IgrisDir\profile.json"
        if ($response.theme) {
            $themeJson = @{ "theme" = $response.theme } | ConvertTo-Json
            Set-Content "$IgrisDir\.theme.json" -Value $themeJson
        }
        Write-Host "  Welcome, $($response.profile.name)!" -ForegroundColor Green
        Write-Host "  Your AI will be named: $($response.ai_name)" -ForegroundColor Green
    } catch {
        Write-Host "  Could not fetch profile. Using defaults." -ForegroundColor Yellow
    }
} else {
    Write-Host "  [No token provided — using default profile]" -ForegroundColor Yellow
}

# 5. Install Python dependencies
if (Test-Path "$PSScriptRoot\..\requirements.txt") {
    Write-Host "→ Installing engine dependencies..." -ForegroundColor Yellow
    pip install -r "$PSScriptRoot\..\requirements.txt" 2>$null
    Write-Host "  Dependencies installed!" -ForegroundColor Green
} else {
    Write-Host "→ Creating engine directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $EngineDir -Force | Out-Null
    pip install ollama whisper pyautogui psutil pyttsx3 SpeechRecognition fastapi uvicorn pydantic chromadb sentence-transformers 2>$null
    Write-Host "  Dependencies installed!" -ForegroundColor Green
}

# 6. Create startup script
if ($Token -and $response) { $displayName = $response.ai_name } else { $displayName = "IGRIS" }
@"
@echo off
cd /d "$EngineDir"
echo   $displayName is starting...
python server.py
"@ | Out-File -FilePath "$IgrisDir\start.bat" -Encoding ASCII

# 7. Create CLI alias
$profilePath = "$env:USERPROFILE\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1"
if (Test-Path $profilePath) {
    Add-Content $profilePath "`nfunction ai { python `"$EngineDir\cli.py`" @args }"
} else {
    New-Item -ItemType Directory -Path (Split-Path $profilePath) -Force | Out-Null
    Set-Content $profilePath "function ai { python `"$EngineDir\cli.py`" @args }"
}

# 8. Start the engine
Write-Host ""
Write-Host "╭──────────────────────────────────────╮" -ForegroundColor Green
if ($Token -and $response) { $displayName2 = "$($response.ai_name) AI" } else { $displayName2 = "IGRIS AI" }
Write-Host "│  $((' ' + $displayName2).PadRight(38))│" -ForegroundColor Green
Write-Host "│  installed successfully!             │" -ForegroundColor Green
Write-Host "│                                      │" -ForegroundColor Green
Write-Host "│  Dashboard: http://localhost:5743     │" -ForegroundColor Green
Write-Host "│  CLI:       ai 'your message'        │" -ForegroundColor Green
Write-Host "╰──────────────────────────────────────╯" -ForegroundColor Green

Write-Host ""
Write-Host "→ Starting AI..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit -Command python `"$EngineDir\server.py`""
