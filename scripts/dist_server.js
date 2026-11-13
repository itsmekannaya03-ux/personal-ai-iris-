const http = require('http');
const fs = require('fs');
const path = require('path');
const os = require('os');

const PORT = 8765;
const ZIP_PATH = path.resolve('iris_package.zip');

// Get current PC Wi-Fi IPv4 address
function getLocalIp() {
  const interfaces = os.networkInterfaces();
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name]) {
      if (iface.family === 'IPv4' && !iface.internal) {
        return iface.address;
      }
    }
  }
  return '127.0.0.1';
}

const hostIp = getLocalIp();

const server = http.createServer((req, res) => {
  const url = req.url.split('?')[0];

  if (url === '/install' || url === '/') {
    const installScript = `# IRIS AI - Autonomous Remote Network Bootstrap
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "         DOWNLOADING IRIS.1 SYSTEM PACKAGE OVER WI-FI...        " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

$destDir = "$HOME\\Desktop\\IRIS-AI"
$zipPath = "$env:TEMP\\iris_package.zip"

Write-Host "[1/3] Downloading IRIS.1 system files (151 MB)..." -ForegroundColor Yellow
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
} catch {}
Invoke-WebRequest -Uri "http://${hostIp}:${PORT}/download" -OutFile $zipPath -UseBasicParsing

Write-Host "[2/3] Extracting files into $destDir..." -ForegroundColor Yellow
if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }

$extracted = $false
try {
    tar.exe -xf $zipPath -C $destDir 2>$null
    if (Test-Path (Join-Path $destDir "install.ps1")) { $extracted = $true }
} catch {}

if (-not $extracted) {
    Expand-Archive -Path $zipPath -DestinationPath $destDir -Force
}

Remove-Item -Force $zipPath -ErrorAction SilentlyContinue

Write-Host "[3/3] Launching IRIS.1 Autonomous Pre-Flight Diagnostic Check..." -ForegroundColor Green
Write-Host ""

Set-Location $destDir
& (Join-Path $destDir "install.ps1")
`;

    res.writeHead(200, {
      'Content-Type': 'text/plain; charset=utf-8',
      'Access-Control-Allow-Origin': '*'
    });
    res.end(installScript);
    console.log(`[${new Date().toLocaleTimeString()}] Sent install bootstrap script to: ${req.socket.remoteAddress}`);
    return;
  }

  if (url === '/download') {
    if (!fs.existsSync(ZIP_PATH)) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('Package not found');
      return;
    }

    const stat = fs.statSync(ZIP_PATH);
    res.writeHead(200, {
      'Content-Type': 'application/zip',
      'Content-Length': stat.size,
      'Content-Disposition': 'attachment; filename="iris_package.zip"'
    });

    const stream = fs.createReadStream(ZIP_PATH);
    stream.pipe(res);
    console.log(`[${new Date().toLocaleTimeString()}] Streaming iris_package.zip (${(stat.size / 1024 / 1024).toFixed(1)} MB) to: ${req.socket.remoteAddress}`);
    return;
  }

  res.writeHead(404, { 'Content-Type': 'text/plain' });
  res.end('Not Found');
});

server.listen(PORT, '0.0.0.0', () => {
  console.log('================================================================');
  console.log('       IRIS AI - WI-FI NETWORK DISTRIBUTION SERVER ACTIVE       ');
  console.log('================================================================');
  console.log(` Local IP Address: ${hostIp}`);
  console.log(` Port:             ${PORT}`);
  console.log(` Package:          ${ZIP_PATH} (${(fs.statSync(ZIP_PATH).size / 1024 / 1024).toFixed(1)} MB)`);
  console.log('');
  console.log(' On the target PC, open CMD and paste this ONE line:');
  console.log(` powershell -ExecutionPolicy Bypass -Command "irm http://${hostIp}:${PORT}/install | iex"`);
  console.log('================================================================');
  console.log(' Press Ctrl+C in this window when installation on the target PC is done.');
});
