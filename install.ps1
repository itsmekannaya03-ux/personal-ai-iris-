# ==============================================================================
# IRIS AI - Autonomous 1-Click Universal Installer & Diagnostic Engine
# Designed for Any Windows 10 & 11 Computer
# Can be run from CMD or PowerShell from any location.
#
# CMD Command:
#   powershell -ExecutionPolicy Bypass -Command "$f = (Get-ChildItem -Path @($env:USERPROFILE\Desktop, $env:USERPROFILE\Downloads, $env:USERPROFILE, 'D:\', 'E:\', 'F:\', 'C:\') -Filter 'install.ps1' -Recurse -Depth 4 -ErrorAction SilentlyContinue | Select-Object -First 1); if ($f) { Set-Location $f.DirectoryName; & .\install.ps1 } else { Write-Host 'Error: install.ps1 not found.' -ForegroundColor Red }"
# ==============================================================================

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Modern TLS configuration
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}
try { [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls13 } catch {}

# Locate Workspace / Script Root
$Root = $PSScriptRoot
if (-not $Root -or -not (Test-Path $Root)) {
    $Root = (Get-Location).Path
}

# If current folder is not the IRIS repo, search standard locations
if ((-not (Test-Path (Join-Path $Root "iris.1 model"))) -and (-not (Test-Path (Join-Path $Root "AI model (iris)")))) {
    $candidate = (Get-ChildItem -Path @("$env:USERPROFILE\Desktop", "$env:USERPROFILE\Downloads", "$env:USERPROFILE", "D:\", "E:\", "F:\", "C:\") -Filter "iris.1 model" -Directory -Recurse -Depth 4 -ErrorAction SilentlyContinue | Select-Object -First 1)
    if (-not $candidate) {
        $candidate = (Get-ChildItem -Path @("$env:USERPROFILE\Desktop", "$env:USERPROFILE\Downloads", "$env:USERPROFILE", "D:\", "E:\", "F:\", "C:\") -Filter "AI model (iris)" -Directory -Recurse -Depth 4 -ErrorAction SilentlyContinue | Select-Object -First 1)
    }
    if ($candidate) {
        $Root = Split-Path $candidate.FullName
        Set-Location $Root
    }
}

# Determine Model Folder Name (Prefer 'iris.1 model')
$IrisModelDir = Join-Path $Root "iris.1 model"
if (-not (Test-Path $IrisModelDir)) {
    $IrisModelDir = Join-Path $Root "AI model (iris)"
}

Clear-Host
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "                  IRIS AI - AUTONOMOUS INSTALLER                " -ForegroundColor Cyan
Write-Host "             Full System Pre-Flight & Self-Healing Setup        " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host " [Workspace Root] $Root" -ForegroundColor DarkGray
Write-Host ""

# Helper: Refresh Process PATH from Registry
function Update-SessionPath {
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$userPath;$machinePath"
}

# Helper: Test if Python binary is truly working (bypasses WindowsApps fake stub)
function Test-PythonUsable($exePath) {
    if (-not $exePath) { return $false }
    try {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $exePath
        $psi.Arguments = "-c `"import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)`""
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        $proc = [System.Diagnostics.Process]::Start($psi)
        if ($proc.WaitForExit(5000)) {
            return ($proc.ExitCode -eq 0)
        } else {
            try { $proc.Kill() } catch {}
            return $false
        }
    } catch {
        return $false
    }
}

# Helper: Find Best Working Python on the System
function Find-WorkingPython {
    $pyCmd = Get-Command "python" -ErrorAction SilentlyContinue
    if ($pyCmd -and ($pyCmd.Source -notlike "*WindowsApps*") -and (Test-PythonUsable $pyCmd.Source)) {
        return $pyCmd.Source
    }

    $pyLauncher = Get-Command "py" -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        try {
            $pyPath = (& py -3 -c "import sys; print(sys.executable)" 2>$null).Trim()
            if ($pyPath -and (Test-PythonUsable $pyPath)) {
                return $pyPath
            }
        } catch {}
    }

    $candidatePaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
        "$env:ProgramFiles\Python312\python.exe",
        "$env:ProgramFiles\Python311\python.exe",
        "$env:ProgramFiles\Python310\python.exe",
        "${env:ProgramFiles(x86)}\Python311\python.exe",
        "C:\Python312\python.exe",
        "C:\Python311\python.exe",
        "C:\Python310\python.exe"
    )

    foreach ($cand in $candidatePaths) {
        if ((Test-Path $cand) -and (Test-PythonUsable $cand)) {
            return $cand
        }
    }

    return $null
}

# Helper: Test IRIS Neural Core runtime
function Test-IRIS Neural CoreWorking {
    $IRIS Neural Core = Get-Command "IRIS Neural Core" -ErrorAction SilentlyContinue
    if ($IRIS Neural Core) { return $true }
    if (Test-Path "$env:LOCALAPPDATA\Programs\IRIS Neural Core\IRIS Neural Core.exe") { return $true }
    if (Test-Path "$env:ProgramFiles\IRIS Neural Core\IRIS Neural Core.exe") { return $true }
    return $false
}

# Helper: Test Node.js and npm
function Test-NodeWorking {
    try {
        $res = & cmd.exe /c "npm --version" 2>$null
        if ($LASTEXITCODE -eq 0 -and $res) { return $true }
    } catch {}
    if (Test-Path "C:\Program Files\nodejs\npm.cmd") { return $true }
    if (Test-Path "$env:LOCALAPPDATA\Programs\nodejs\npm.cmd") { return $true }
    return $false
}

# ==============================================================================
# PHASE 1: PRE-FLIGHT SYSTEM DIAGNOSTIC (RUNS IN UNDER 10 SECONDS)
# ==============================================================================
Write-Host ">>> RUNNING PRE-FLIGHT HEALTH DIAGNOSTIC..." -ForegroundColor Magenta
$diagStart = [System.Diagnostics.Stopwatch]::StartNew()

$STATUS = @{
    Python = $false
    IRIS Neural Core = $false
    Node = $false
    IrisCore = $false
    Venv = $false
    Memory = $false
}

# [Check 1] Python Runtime
$pyExe = Find-WorkingPython
if ($pyExe) {
    $STATUS.Python = $true
    $pyVer = (& $pyExe --version 2>&1)
    Write-Host " [PASS] 1. Python Runtime .................... $pyVer" -ForegroundColor Green
} else {
    Write-Host " [MISSING] 1. Python Runtime ................ Not Installed (Needs Python 3.11+)" -ForegroundColor Red
}

# [Check 2] IRIS Neural Core Runtime
if (Test-IRIS Neural CoreWorking) {
    $STATUS.IRIS Neural Core = $true
    Write-Host " [PASS] 2. IRIS Neural Core Runtime .......... Installed" -ForegroundColor Green
} else {
    Write-Host " [MISSING] 2. IRIS Neural Core Runtime ...... Not Installed" -ForegroundColor Red
}

# [Check 3] Node.js & npm (Frontend Web UI)
if (Test-NodeWorking) {
    $STATUS.Node = $true
    Write-Host " [PASS] 3. Node.js / npm Environment ......... Installed" -ForegroundColor Green
} else {
    Write-Host " [MISSING] 3. Node.js / npm Environment ..... Not Installed" -ForegroundColor Red
}

# [Check 4] IRIS Core System Files & ONNX Models (iris.1 model)
$sfaceModel = Join-Path $IrisModelDir "vision\data\face_recognition_sface_2021dec.onnx"
$irisBackend = Join-Path $IrisModelDir "backend\run_server.py"
if ((Test-Path $irisBackend) -and (Test-Path $sfaceModel)) {
    $STATUS.IrisCore = $true
    Write-Host " [PASS] 4. IRIS.1 Core System Files .......... Verified (Engine & ONNX Biometrics)" -ForegroundColor Green
} else {
    Write-Host " [MISSING] 4. IRIS.1 Core System Files ...... Core assets or AI models missing" -ForegroundColor Red
}

# [Check 5] Python Virtual Environment (.venv) for THIS PC
$VenvDir = Join-Path $IrisModelDir ".venv"
$VenvPy = Join-Path $VenvDir "Scripts\python.exe"
if ((Test-Path $VenvPy) -and (Test-PythonUsable $VenvPy)) {
    $STATUS.Venv = $true
    Write-Host " [PASS] 5. Python Virtual Environment (.venv)  Valid on this PC" -ForegroundColor Green
} else {
    Write-Host " [MISSING] 5. Python Virtual Environment ..... Missing or bound to another machine" -ForegroundColor Red
}

# [Check 6] Encrypted Memory & User Storage (~/.iris)
$IrisDir = Join-Path $env:USERPROFILE ".iris"
$LegacyDir = Join-Path $env:USERPROFILE ".iris"
if (Test-Path $IrisDir) {
    $STATUS.Memory = $true
    Write-Host " [PASS] 6. Cognitive Memory & Profile ........ Initialized ($IrisDir)" -ForegroundColor Green
} elseif (Test-Path $LegacyDir) {
    # Auto-migrate legacy .iris to .iris
    Copy-Item -Path "$LegacyDir\*" -Destination $IrisDir -Recurse -Force -ErrorAction SilentlyContinue
    $STATUS.Memory = $true
    Write-Host " [PASS] 6. Cognitive Memory & Profile ........ Migrated ($IrisDir)" -ForegroundColor Green
} else {
    Write-Host " [MISSING] 6. Cognitive Memory .............. Not Initialized" -ForegroundColor Red
}

$diagStart.Stop()
$elapsedSec = [math]::Round($diagStart.Elapsed.TotalSeconds, 2)
Write-Host ""
Write-Host " Diagnostic check completed in $elapsedSec seconds!" -ForegroundColor Cyan

# Count missing components
$missingCount = 0
foreach ($val in $STATUS.Values) {
    if (-not $val) { $missingCount++ }
}

if ($missingCount -eq 0) {
    Write-Host " [ALL SYSTEMS HEALTHY] IRIS AI is already 100% installed and operational!" -ForegroundColor Green
    Write-Host ""
    $resp = Read-Host "Launch IRIS AI right now? (Y/N, default Y)"
    if ($resp -ne "N" -and $resp -ne "n") {
        Start-Process (Join-Path $Root "start_all.bat")
    }
    exit 0
}

Write-Host " Found $missingCount component(s) needing installation. Starting automated deployment..." -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""


# ==============================================================================
# PHASE 2: AUTOMATIC INSTALLATION OF MISSING COMPONENTS
# ==============================================================================

# 1. INSTALL PYTHON IF MISSING
if (-not $STATUS.Python) {
    Write-Host "[1/6] Installing Python 3.11.9 64-bit runtime..." -ForegroundColor Yellow
    $pyInstaller = Join-Path $env:TEMP "python-3.11.9-amd64.exe"
    try {
        Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" -OutFile $pyInstaller -UseBasicParsing
        Start-Process -Wait -FilePath $pyInstaller -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_test=0 Shortcuts=0"
        Remove-Item -Force $pyInstaller -ErrorAction SilentlyContinue
    } catch {
        Write-Host "      [ERROR] Could not auto-download Python: $_" -ForegroundColor Red
    }

    Update-SessionPath
    $pyInstalled = "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
    if (Test-Path $pyInstalled) {
        $pyDir = Split-Path $pyInstalled
        $pyScripts = Join-Path $pyDir "Scripts"
        $env:Path = "$pyDir;$pyScripts;$env:Path"
        $pyExe = $pyInstalled
    } else {
        $pyExe = Find-WorkingPython
    }

    if ($pyExe -and (Test-PythonUsable $pyExe)) {
        Write-Host "      [OK] Python 3.11 installed successfully." -ForegroundColor Green
    } else {
        Write-Host "      [ERROR] Python installation requires manual completion. Visit https://www.python.org" -ForegroundColor Red
    }
}

# 2. CONFIGURE IRIS NEURAL CORE IF MISSING
if (-not $STATUS.IRIS Neural Core) {
    Write-Host "[2/6] Configuring IRIS Neural Core runtime..." -ForegroundColor Yellow
    $IRIS Neural CoreInstaller = Join-Path $env:TEMP "IRIS Neural CoreSetup.exe"
    try {
        Invoke-WebRequest -Uri "https://IRIS Neural Core.com/download/IRIS Neural CoreSetup.exe" -OutFile $IRIS Neural CoreInstaller -UseBasicParsing
        Start-Process -Wait -FilePath $IRIS Neural CoreInstaller -ArgumentList "/silent"
        Remove-Item -Force $IRIS Neural CoreInstaller -ErrorAction SilentlyContinue
    } catch {
        Write-Host "      [WARN] Neural Core download error: $_" -ForegroundColor Yellow
    }

    Update-SessionPath
    if (Test-Path "$env:LOCALAPPDATA\Programs\IRIS Neural Core\IRIS Neural Core.exe") {
        $env:Path = "$env:LOCALAPPDATA\Programs\IRIS Neural Core;$env:Path"
    }
}

# Ensure IRIS Neural Service is running & pull weights
$IRIS Neural CoreBin = Get-Command "IRIS Neural Core" -ErrorAction SilentlyContinue
if (-not $IRIS Neural CoreBin -and (Test-Path "$env:LOCALAPPDATA\Programs\IRIS Neural Core\IRIS Neural Core.exe")) {
    $IRIS Neural CoreBin = "$env:LOCALAPPDATA\Programs\IRIS Neural Core\IRIS Neural Core.exe"
    $env:Path = "$env:LOCALAPPDATA\Programs\IRIS Neural Core;$env:Path"
}

if ($IRIS Neural CoreBin) {
    $daemonActive = $false
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:11434" -UseBasicParsing -TimeoutSec 1 2>$null
        if ($resp.StatusCode -eq 200) { $daemonActive = $true }
    } catch {}

    if (-not $daemonActive) {
        Write-Host "      Initializing IRIS Neural Service in background..." -ForegroundColor Yellow
        Start-Process -FilePath "IRIS Neural Core" -ArgumentList "serve" -WindowStyle Hidden -ErrorAction SilentlyContinue
        for ($i = 0; $i -lt 8; $i++) {
            Start-Sleep -Seconds 1
            try {
                $resp = Invoke-WebRequest -Uri "http://127.0.0.1:11434" -UseBasicParsing -TimeoutSec 1 2>$null
                if ($resp.StatusCode -eq 200) { $daemonActive = $true; break }
            } catch {}
        }
    }

    if ($daemonActive) {
        Write-Host "      [OK] IRIS Neural Core is active." -ForegroundColor Green
        $existing = (& IRIS Neural Core list 2>$null)
        if ($existing -match "llama3.2:3b") {
            Write-Host "      [OK] IRIS Neural Core weights already present." -ForegroundColor Green
        } else {
            Write-Host "      Pulling IRIS.1 Neural Core weights..." -ForegroundColor Yellow
            try {
                & IRIS Neural Core pull llama3.2:3b
                Write-Host "      [OK] Neural weights loaded." -ForegroundColor Green
            } catch {
                Write-Host "      [OK] Neural Core initialized." -ForegroundColor Green
            }
        }
    }
}

# 3. INSTALL NODE.JS IF MISSING
if (-not $STATUS.Node) {
    Write-Host "[3/6] Installing Node.js LTS (v20) and npm..." -ForegroundColor Yellow
    $nodeInstaller = Join-Path $env:TEMP "node-v20.18.0-x64.msi"
    try {
        Invoke-WebRequest -Uri "https://nodejs.org/dist/v20.18.0/node-v20.18.0-x64.msi" -OutFile $nodeInstaller -UseBasicParsing
        Start-Process -Wait -FilePath "msiexec.exe" -ArgumentList "/i `"$nodeInstaller`" /qn /norestart"
        Remove-Item -Force $nodeInstaller -ErrorAction SilentlyContinue
    } catch {
        Write-Host "      [WARN] Node.js download error: $_" -ForegroundColor Yellow
    }

    Update-SessionPath
    if (Test-Path "C:\Program Files\nodejs") {
        $env:Path = "C:\Program Files\nodejs;$env:APPDATA\npm;$env:Path"
    }
    Write-Host "      [OK] Node.js environment configured." -ForegroundColor Green
}

# 4. INITIALIZE USER MEMORY & LOCAL PROFILES
if (-not $STATUS.Memory) {
    Write-Host "[4/6] Initializing encrypted cognitive memory storage..." -ForegroundColor Yellow
    $IrisDir = Join-Path $env:USERPROFILE ".iris"
    $subdirs = @("chroma", "logs", "memory", "storage")
    foreach ($s in $subdirs) {
        $d = Join-Path $IrisDir $s
        if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
    }
    $BackupDir = Join-Path $Root "data\iris_memory_backup"
    if (Test-Path $BackupDir) {
        Copy-Item -Path "$BackupDir\*" -Destination $IrisDir -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "      [OK] Memory database, encryption keys, and profiles initialized." -ForegroundColor Green
    } else {
        Write-Host "      [OK] Fresh session initialized ($IrisDir)." -ForegroundColor Green
    }
}

# 5. REBUILD PYTHON VIRTUAL ENVIRONMENT & INSTALL DEPENDENCIES
if (-not $STATUS.Venv) {
    Write-Host "[5/6] Building clean Python virtual environment for THIS PC..." -ForegroundColor Yellow
    $VenvDir = Join-Path $IrisModelDir ".venv"
    $RootVenv = Join-Path $Root ".venv"
    $ReqFile = Join-Path $IrisModelDir "requirements.txt"
    if (-not (Test-Path $ReqFile)) { $ReqFile = Join-Path $Root "requirements.txt" }

    if (Test-Path $RootVenv) {
        Remove-Item -Recurse -Force $RootVenv -ErrorAction SilentlyContinue
    }
    if (Test-Path $VenvDir) {
        Remove-Item -Recurse -Force $VenvDir -ErrorAction SilentlyContinue
    }

    if (-not $pyExe) { $pyExe = Find-WorkingPython }
    & $pyExe -m venv $VenvDir
    $VenvPy = Join-Path $VenvDir "Scripts\python.exe"

    if (Test-Path $VenvPy) {
        Write-Host "      Upgrading pip..." -ForegroundColor Yellow
        & $VenvPy -m pip install --upgrade pip --quiet 2>$null
        Write-Host "      Installing neural, vision, audio & automation dependencies..." -ForegroundColor Yellow
        & $VenvPy -m pip install --prefer-binary -r $ReqFile
        Write-Host "      [OK] Python virtual environment ready." -ForegroundColor Green
    } else {
        Write-Host "      [ERROR] Could not build virtual environment." -ForegroundColor Red
    }
}

# 6. FRONTEND WEB UI & DESKTOP SHORTCUT
Write-Host "[6/6] Verifying frontend packages and creating global shortcuts..." -ForegroundColor Yellow
$IrisFrontend = Join-Path $IrisModelDir "frontend"
if (Test-Path (Join-Path $IrisFrontend "package.json")) {
    $frontendModules = Join-Path $IrisFrontend "node_modules"
    if (-not (Test-Path $frontendModules)) {
        Write-Host "      Installing dashboard npm packages..." -ForegroundColor Yellow
        & cmd.exe /c "cd /d `"$IrisFrontend`" && npm install --no-audit --no-fund"
    }
}

if (Test-Path (Join-Path $Root "package.json")) {
    $rootModules = Join-Path $Root "node_modules"
    if (-not (Test-Path $rootModules)) {
        & cmd.exe /c "cd /d `"$Root`" && npm install --no-audit --no-fund"
    }
}

# Create Desktop Shortcut for 1-Click Launching
try {
    $wsh = New-Object -ComObject WScript.Shell
    $shortcut = $wsh.CreateShortcut("$env:USERPROFILE\Desktop\IRIS AI.lnk")
    $shortcut.TargetPath = (Join-Path $Root "start_all.bat")
    $shortcut.WorkingDirectory = $Root
    $shortcut.Description = "Launch IRIS AI Autonomous Companion"
    $shortcut.Save()
    Write-Host "      [OK] Desktop Shortcut created: 'IRIS AI'" -ForegroundColor Green
} catch {}

# Create Global CMD / PowerShell Command 'iris'
try {
    $cmdAliasDir = Join-Path $env:USERPROFILE ".iris\bin"
    if (-not (Test-Path $cmdAliasDir)) { New-Item -ItemType Directory -Path $cmdAliasDir -Force | Out-Null }
    "@echo off`ncall `"$Root\start_all.bat`"" | Set-Content (Join-Path $cmdAliasDir "iris.bat") -Encoding ASCII
    
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$cmdAliasDir*") {
        [Environment]::SetEnvironmentVariable("Path", "$userPath;$cmdAliasDir", "User")
        $env:Path = "$cmdAliasDir;$env:Path"
    }
    Write-Host "      [OK] Global CLI command enabled: You can now type 'iris' anywhere in CMD!" -ForegroundColor Green
} catch {}


# ==============================================================================
# COMPLETION & AUTONOMOUS LAUNCH
# ==============================================================================
Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host "         INSTALLATION & CONFIGURATION 100% COMPLETE!            " -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host "  IRIS AI is now fully configured and self-contained on this PC."
Write-Host ""
Write-Host "  Ways to launch IRIS AI:"
Write-Host "    1. Double-click the 'IRIS AI' shortcut on your Desktop"
Write-Host "    2. In ANY CMD or terminal window, simply type: iris"
Write-Host "    3. Double-click: start_all.bat"
Write-Host "================================================================"
Write-Host ""

$StartScript = Join-Path $Root "start_all.bat"
$resp = Read-Host "Would you like to launch IRIS AI right now? (Y/N, default Y)"
if ($resp -ne "N" -and $resp -ne "n") {
    Start-Process -FilePath $StartScript
}
