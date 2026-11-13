const fs = require('fs');
const path = require('path');

const src = 'AI model (iris)';
const dst = 'iris.1 model';

console.log(`Syncing ${src} -> ${dst}...`);

function copyDir(source, target) {
  if (!fs.existsSync(target)) {
    fs.mkdirSync(target, { recursive: true });
  }

  for (const item of fs.readdirSync(source)) {
    if (item === '.venv' || item === '__pycache__' || item.endsWith('.log')) continue;
    const srcPath = path.join(source, item);
    const dstPath = path.join(target, item);
    const stat = fs.statSync(srcPath);

    if (stat.isDirectory()) {
      copyDir(srcPath, dstPath);
    } else {
      fs.copyFileSync(srcPath, dstPath);
    }
  }
}

copyDir(src, dst);
console.log(`SUCCESS: ${dst} created and populated!`);

