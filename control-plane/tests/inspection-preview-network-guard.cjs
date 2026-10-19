// Test tooling may transform source; production services/connections are blocked.
const fs=require('node:fs');
const net=require('node:net');
const subprocess=require('node:child_process');
const path=require('node:path');
const {syncBuiltinESMExports}=require('node:module');
const isolatedOutput=process.env.NUSANTARA_TEST_RUN_DIR?path.resolve(process.env.NUSANTARA_TEST_RUN_DIR):null;
if(isolatedOutput){for(let current=isolatedOutput;;current=path.dirname(current)){if(fs.existsSync(path.join(current,'FINALIZED.json')))throw new Error('FINALIZED_RUN_IMMUTABLE');if(path.dirname(current)===current)break;}}
function blocked(){const error=new Error('PREVIEW_TEST_EXTERNAL_EFFECT_BLOCKED');process.stderr.write(error.stack+'\n');throw error;}
function writeAllowed(target){
  const value=path.resolve(String(target));
  if(isolatedOutput&&value!==isolatedOutput&&!value.startsWith(isolatedOutput+path.sep)){
    const error=new Error('TEST_WRITE_OUTSIDE_ISOLATED_RUN: '+value);process.stderr.write(error.stack+'\n');throw error;
  }
}
function writeIntent(flags){return typeof flags==='number'?(flags&3)!==0||!!(flags&0x40)||!!(flags&0x80):/[wax+]/.test(String(flags));}
net.Socket.prototype.connect=blocked;
net.Server.prototype.listen=blocked;
globalThis.fetch=blocked;
for(const name of ['readFileSync','readFile','openSync','open','writeFileSync','writeFile','appendFileSync','appendFile']){
  const original=fs[name];
  fs[name]=function(path,...args){
    const value=String(path).replaceAll('\\','/').toLowerCase();
    if(/\.(db|db-wal|db-shm)$/.test(value)||value.includes('/data/'))blocked();
    if(['writeFileSync','writeFile','appendFileSync','appendFile'].includes(name)||(['openSync','open'].includes(name)&&writeIntent(args[0])))writeAllowed(path);
    return original.call(this,path,...args);
  };
}
for(const name of ['readFile','open','writeFile','appendFile']){
  const original=fs.promises[name];
  fs.promises[name]=function(file,...args){
    const value=String(file).replaceAll('\\','/').toLowerCase();
    if(/\.(db|db-wal|db-shm)$/.test(value)||value.includes('/data/'))blocked();
    if(['writeFile','appendFile'].includes(name)||(name==='open'&&writeIntent(args[0])))writeAllowed(file);
    return original.call(this,file,...args);
  };
}
for(const name of ['mkdirSync','mkdir','rmSync','rm','unlinkSync','unlink','renameSync','rename','copyFileSync','copyFile']){
  const original=fs[name];if(typeof original!=='function')continue;
  fs[name]=function(from,to,...args){
    const targets=name.startsWith('rename')||name.startsWith('copyFile')?[from,to]:[from];
    for(const target of targets)writeAllowed(target);
    return original.call(this,from,to,...args);
  };
}
for(const name of ['mkdir','rm','unlink','rename','copyFile']){
  const original=fs.promises[name];if(typeof original!=='function')continue;
  fs.promises[name]=function(from,to,...args){
    const targets=['rename','copyFile'].includes(name)?[from,to]:[from];
    for(const target of targets)writeAllowed(target);
    return original.call(this,from,to,...args);
  };
}
for(const name of ['createWriteStream']){
  const original=fs[name];
  fs[name]=function(file,...args){writeAllowed(file);return original.call(this,file,...args);};
}
const transformer=path.resolve(__dirname,'../node_modules/@esbuild/win32-x64/esbuild.exe');
const reportProbe="const r=require('node:process').report;r.excludeNetwork=true;console.log(JSON.stringify(r.getReport().header));";
for(const name of ['spawn','spawnSync','execFile','execFileSync']){
  const original=subprocess[name];
  subprocess[name]=function(command,...args){
    // Rollup's optional Windows diagnostic receives its supported unavailable result.
    if(name==='spawnSync'&&path.resolve(String(command)).toLowerCase()===process.execPath.toLowerCase()
      &&args[0]?.length===2&&args[0][0]==='-p'&&args[0][1]===reportProbe)
      return {status:1,stdout:'',stderr:''};
    if(path.resolve(String(command)).toLowerCase()!==transformer.toLowerCase())blocked();
    return original.call(this,command,...args);
  };
}
subprocess.exec=function(command,...args){
  // Vite probes Windows drive mappings. Supply an empty fixture without executing it.
  if(command!=='net use')return blocked();
  const callback=args.at(-1);
  if(typeof callback==='function')queueMicrotask(()=>callback(null,'',''));
  return null;
};
subprocess.execSync=blocked;
const originalFork=subprocess.fork;
const vitestWorker=path.resolve(__dirname,'../node_modules/tinypool/dist/entry/process.js');
subprocess.fork=function(modulePath,...args){
  if(path.resolve(String(modulePath)).toLowerCase()!==vitestWorker.toLowerCase())return blocked();
  return originalFork.call(this,modulePath,...args);
};
syncBuiltinESMExports();
