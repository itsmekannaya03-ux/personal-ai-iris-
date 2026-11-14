$ProgressPreference = 'SilentlyContinue'
Add-Type -AssemblyName System.IO.Compression.FileSystem

$source = "C:\Users\itsme\Desktop\IGRIS-AI\AI model (iris)"
$destDir = "C:\Users\itsme\Desktop\IGRIS-AI\website\public\downloads"
$zipPath = Join-Path $destDir "iris-ai.zip"

if (!(Test-Path $destDir)) {
    New-Item -ItemType Directory -Path $destDir -Force | Out-Null
}
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

$tempStage = Join-Path $env:TEMP ("iris_stage_" + [guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $tempStage -Force | Out-Null

Write-Host "Copying files to staging directory..." -ForegroundColor Cyan

Get-ChildItem -Path $source | ForEach-Object {
    if ($_.PSIsContainer) {
        if ($_.Name -notin @("__pycache__", ".venv", ".git", "test_folder", "scratch")) {
            $destSub = Join-Path $tempStage $_.Name
            robocopy $_.FullName $destSub /E /XD "node_modules" "__pycache__" ".git" ".venv" /XF "*.log" "screenshot_*.png" "*.tmp" /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
        }
    } else {
        if ($_.Name -notmatch '^screenshot_|\.log$|\.read$|\.wav$|\.mp3$') {
            Copy-Item -Path $_.FullName -Destination $tempStage -Force
        }
    }
}

# Remove duplicate 38MB model files in backend/ui (they are preserved in vision/data)
$dupOnnx = Join-Path $tempStage "backend\ui\face_recognition_sface_2021dec.onnx"
if (Test-Path $dupOnnx) { Remove-Item $dupOnnx -Force }
$dupHaar = Join-Path $tempStage "backend\ui\haarcascade_frontalface_default.xml"
if (Test-Path $dupHaar) { Remove-Item $dupHaar -Force }
$dupYunet = Join-Path $tempStage "backend\ui\face_detection_yunet_2023mar.onnx"
if (Test-Path $dupYunet) { Remove-Item $dupYunet -Force }

Write-Host "Compressing to $zipPath..." -ForegroundColor Cyan
[System.IO.Compression.ZipFile]::CreateFromDirectory($tempStage, $zipPath, [System.IO.Compression.CompressionLevel]::Optimal, $false)

Remove-Item -Path $tempStage -Recurse -Force

if (Test-Path $zipPath) {
    $zipItem = Get-Item $zipPath
    Write-Host "SUCCESS! iris-ai.zip created successfully." -ForegroundColor Green
    Write-Host ("Size: " + [math]::Round($zipItem.Length / 1MB, 2) + " MB (" + $zipItem.Length + " bytes)") -ForegroundColor Yellow
} else {
    Write-Host "FAILED to create zip." -ForegroundColor Red
}
