const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('Building clean IRIS AI distribution package (iris_package.zip)...');

const ZIP_NAME = 'iris_package.zip';

if (fs.existsSync(ZIP_NAME)) {
  fs.unlinkSync(ZIP_NAME);
}

const args = [
  '-a', '-c',
  '-f', ZIP_NAME,
  '--exclude=.venv',
  '--exclude=node_modules',
  '--exclude=.next',
  '--exclude=.git',
  '--exclude=__pycache__',
  '--exclude=screenshot_*.png',
  '--exclude=*.log',
  '--exclude=*.docx',
  '--exclude=*.mp4',
  '--exclude=' + ZIP_NAME,
  'iris.1 model',
  'AI model (iris)',
  'backend',
  'website',
  'engine',
  'installer',
  'data',
  'report_assets',
  'start_all.bat',
  'install.bat',
  'install.ps1',
  'run_app.py',
  'requirements.txt',
  'package.json'
];

const res = spawnSync('tar.exe', args, { stdio: 'inherit' });
if (fs.existsSync(ZIP_NAME)) {
  const stat = fs.statSync(ZIP_NAME);
  console.log(`SUCCESS! ${ZIP_NAME} created successfully.`);
  console.log('Package Size:', (stat.size / 1024 / 1024).toFixed(2), 'MB');
} else {
  console.error('Failed to create zip package.');
}
