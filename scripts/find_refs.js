const fs = require('fs');
const path = require('path');

const target = 'AI model (iris)';
const matches = [];

function search(dir) {
  for (const f of fs.readdirSync(dir)) {
    if (f === '.venv' || f === 'node_modules' || f === '.next' || f === '.git' || f === '__pycache__' || f.endsWith('.pdf') || f.endsWith('.zip')) continue;
    const p = path.join(dir, f);
    try {
      const s = fs.statSync(p);
      if (s.isDirectory()) search(p);
      else if (f.endsWith('.py') || f.endsWith('.ps1') || f.endsWith('.bat') || f.endsWith('.js') || f.endsWith('.json') || f.endsWith('.ts') || f.endsWith('.tsx') || f.endsWith('.md')) {
        const c = fs.readFileSync(p, 'utf8');
        if (c.includes(target)) {
          matches.push(p);
        }
      }
    } catch {}
  }
}

search('.');
console.log('Total files referencing "' + target + '": ' + matches.length);
matches.forEach(m => console.log(m));

