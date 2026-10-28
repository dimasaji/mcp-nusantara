"""Run existing npm test script, retain stdout/stderr/exit code in fresh evidence."""
import json
import os
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
node='C:/Users/dmaza/AppData/Local/hermes/node/node.exe'
npm='C:/Users/dmaza/AppData/Local/hermes/node/node_modules/npm/bin/npm-cli.js'
guard=(ROOT/'docs/reports/ui04-chat-timeout-20261009-130937/test-write-guard.cjs').read_bytes()
if not (OUT/'test-write-guard.cjs').exists():
    with (OUT/'test-write-guard.cjs').open('xb') as stream:stream.write(guard)
env=os.environ.copy()
env['PATH']=str(Path(node).parent)+os.pathsep+env.get('PATH','')
env['NODE_OPTIONS']='--require "'+(OUT/'preload.cjs').as_posix()+'"'
env['npm_config_cache']=str(OUT/'npm-cache')
args=[node,npm,'--prefix','control-plane','test','--','--run','tests/assistant.test.tsx','--configLoader','runner','--no-cache','--pool=threads','--maxWorkers=1','--minWorkers=1','--reporter=default','--reporter=json','--outputFile='+str(OUT/'TEST_RESULTS.json')]
r=subprocess.run(args,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
with (OUT/'TEST_EXECUTION_02.json').open('x',encoding='utf-8') as stream:json.dump({'command':args,'working_directory':str(ROOT),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'transient_test_environment':'Installed Node PATH; report-local npm cache and child-only guards. No global configuration or dependencies changed.'},stream,ensure_ascii=False,indent=2)
print(json.dumps({'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr},ensure_ascii=False))
