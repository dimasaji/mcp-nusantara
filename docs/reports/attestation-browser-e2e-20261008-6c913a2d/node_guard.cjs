// No Node HTTP/socket client or listening server is needed for this mode.
const net=require('node:net');
globalThis.__NUSANTARA_MOCK_NETWORK_GUARD__=true;
net.Socket.prototype.connect=function(){throw new Error('NODE_NETWORK_BLOCKED');};
net.Server.prototype.listen=function(){throw new Error('NODE_LISTENER_BLOCKED');};
globalThis.fetch=async()=>{throw new Error('NODE_FETCH_BLOCKED');};
const fs=require('node:fs');
for(const name of ['open','openSync','readFile','readFileSync']){
  const original=fs[name];fs[name]=function(file,...args){
    if(typeof file==='string' && (/\.db(?:-wal|-shm)?$/i.test(file)||/[\\/]data[\\/]knowledge[\\/]/i.test(file)))
      throw new Error('PROTECTED_READ_BLOCKED');
    return original.call(this,file,...args);
  };
}
