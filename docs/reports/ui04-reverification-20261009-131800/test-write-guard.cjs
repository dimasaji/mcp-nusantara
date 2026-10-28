// Tests may write evidence only; existing project/dependency/config files are protected.
require('../../../control-plane/tests/inspection-preview-network-guard.cjs');
const fs=require('node:fs');
const path=require('node:path');
const {syncBuiltinESMExports}=require('node:module');
const root=path.resolve(__dirname).toLowerCase()+path.sep;
function writable(file){
  if(typeof file==='number')return; // stdio descriptors, not pathname writes.
  const target=path.resolve(String(file)).toLowerCase();
  if(!target.startsWith(root))throw new Error('UI04_TEST_WRITE_OUTSIDE_EVIDENCE_BLOCKED: '+target);
}
for(const name of ['writeFileSync','writeFile','appendFileSync','appendFile','mkdirSync','mkdir','rmSync','rm','unlinkSync','unlink','rmdirSync','rmdir']){
  const original=fs[name];fs[name]=function(file,...args){writable(file);return original.call(this,file,...args);};
}
for(const name of ['writeFile','appendFile','mkdir','rm','unlink','rmdir']){
  const original=fs.promises[name];fs.promises[name]=function(file,...args){writable(file);return original.call(this,file,...args);};
}
for(const name of ['openSync','open']){
  const original=fs[name];fs[name]=function(file,flags,...args){
    if(typeof flags==='string'?/[wa+]/.test(flags):typeof flags==='number'&&(flags&(fs.constants.O_WRONLY|fs.constants.O_RDWR|fs.constants.O_CREAT|fs.constants.O_TRUNC)))writable(file);
    return original.call(this,file,flags,...args);
  };
}
const originalOpen=fs.promises.open;
fs.promises.open=function(file,flags,...args){if(typeof flags==='string'?/[wa+]/.test(flags):typeof flags==='number'&&(flags&(fs.constants.O_WRONLY|fs.constants.O_RDWR|fs.constants.O_CREAT|fs.constants.O_TRUNC)))writable(file);return originalOpen.call(this,file,flags,...args);};
syncBuiltinESMExports();
