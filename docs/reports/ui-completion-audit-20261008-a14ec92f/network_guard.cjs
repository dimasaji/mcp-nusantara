// Audit-only guard: tests must mock fetch and never open a network service.
const fs = require('node:fs');
const net = require('node:net');
function blocked(){throw new Error('UI_AUDIT_NETWORK_BLOCKED');}
net.Socket.prototype.connect = blocked;
net.Server.prototype.listen = blocked;
globalThis.fetch = blocked;
for(const name of ['readFileSync','readFile','openSync','open']) {
  const original=fs[name];
  fs[name]=function(path,...args){
    const value=String(path).replaceAll('\\','/').toLowerCase();
    if(/\.(db|db-wal|db-shm)$/.test(value)||value.includes('/data/knowledge/'))
      throw new Error('UI_AUDIT_PROTECTED_FILE_BLOCKED');
    return original.call(this,path,...args);
  };
}
