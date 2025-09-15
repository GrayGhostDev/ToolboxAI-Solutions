const fs = require('fs');

// Fix auth-sync.ts
let authSync = fs.readFileSync('services/auth-sync.ts', 'utf8');
authSync = authSync.replace(/if \(null \/\* terminalSync removed \*\/\) \{[\s\S]*?\}/g, '// Terminal sync removed');
authSync = authSync.replace(/null \/\* terminalSync removed \*\/\.[^;]+;/g, '// Terminal sync call removed;');
authSync = authSync.replace(/catch\(error/g, 'catch((error: any)');
fs.writeFileSync('services/auth-sync.ts', authSync);

// Fix performance-monitor.ts
let perfMon = fs.readFileSync('utils/performance-monitor.ts', 'utf8');
perfMon = perfMon.replace(/if \(null \/\* terminalSync removed \*\/\) \{[\s\S]*?\}/g, '// Terminal sync removed');
perfMon = perfMon.replace(/null \/\* terminalSync removed \*\/\.[^;]+;/g, '// Terminal sync call removed;');
perfMon = perfMon.replace(/catch\(error/g, 'catch((error: any)');
fs.writeFileSync('utils/performance-monitor.ts', perfMon);

console.log('Fixed terminal sync references');
