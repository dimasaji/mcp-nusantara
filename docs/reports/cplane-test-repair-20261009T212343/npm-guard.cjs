// Scoped npm launcher: only the exact requested test/build scripts may spawn.
const cp=require('node:child_process');
const path=require('node:path');
const rawSpawn=cp.spawn,rawExecFileSync=cp.execFileSync;
require('../../../control-plane/tests/inspection-preview-network-guard.cjs');
const guardedSpawn=cp.spawn,guardedExecFileSync=cp.execFileSync;
const workspace=path.resolve(__dirname,'../../../control-plane');
const scripts=new Set([
  'vitest run --pool=threads --maxWorkers=1 --minWorkers=1 --reporter=default --reporter=json --outputFile.json=../docs/reports/cplane-test-repair-20261009T212343/ALL_UNIT.json',
  'tsc --noEmit && vite build --outDir ../docs/reports/cplane-test-repair-20261009T212343/build',
]);
cp.spawn=function(command,args,options){
  if(process.argv[1]?.endsWith('npm-cli.js')&&path.basename(String(command)).toLowerCase()==='cmd.exe'&&
     args?.length===4&&args[0]==='/d'&&args[1]==='/s'&&args[2]==='/c'&&scripts.has(args[3])&&
     path.resolve(options.cwd).toLowerCase()===workspace.toLowerCase())
    return rawSpawn.call(this,command,args,options);
  return guardedSpawn.call(this,command,args,options);
};
cp.execFileSync=function(command,args,options){
  const git='C:/Users/dmaza/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe';
  if(path.resolve(String(command)).toLowerCase()===path.resolve(git).toLowerCase()&&
     args?.length===2&&args[0]==='rev-parse'&&args[1]==='HEAD')
    return rawExecFileSync.call(this,command,args,options);
  return guardedExecFileSync.call(this,command,args,options);
};
require('node:module').syncBuiltinESMExports();
