// Refresh existing offline snapshot only from recorded report and JUnit bytes.
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const root=path.resolve(__dirname,'../../..');
const target=path.join(root,'control-plane/src/engineering-evidence.ts');
const read=relative=>fs.readFileSync(path.join(root,relative));
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const original=fs.readFileSync(target,'utf8');
const data=JSON.parse(original.replace(/^export default /,'').replace(/;\s*$/,''));
const ragDir='docs/reports/v1-remaining-20261009T182840';
const cloudDir='docs/reports/openrouter-workflow-20261009T184538';
const rag=JSON.parse(read(ragDir+'/EXECUTION_RESULTS.json'));
const cloud=JSON.parse(read(cloudDir+'/IMPLEMENTATION_REPORT.json'));
for(const item of rag.hashes){
  if(sha(read(item.path))!==item.after)throw new Error('RAG_SOURCE_CHANGED: '+item.path);
}
for(const item of cloud.audit.files){
  if(sha(read(item.path))!==item.after_sha256)throw new Error('CLOUD_SOURCE_CHANGED: '+item.path);
}
function source(relative){
  if(!data.sources.some(s=>s.path===relative))data.sources.push({path:relative,sha256:sha(read(relative))});
}
source(ragDir+'/EXECUTION_RESULTS.json');source(cloudDir+'/IMPLEMENTATION_REPORT.json');
data.unavailableRuns=[];
function appendRun(directory, run, counts, exitCode, deselected){
  const relative=directory+'/'+run+'/results.xml';
  if(!counts){
    data.unavailableRuns.push({name:run,status:'NOT_VERIFIED',
      detail:'JUnit tidak lengkap setelah pemeriksaan subprocess platform diblokir. Exit 1; tidak dihitung sebagai PASS.',
      reference:directory+'/IMPLEMENTATION_REPORT.json'});
    return;
  }
  const xml=read(relative).toString('utf8');
  const suite=xml.match(/<testsuite\s[^>]+>/)?.[0];
  for(const key of ['tests','failures','errors','skipped']){
    const recorded=Number(suite?.match(new RegExp('\\b'+key+'="(\\d+)"'))?.[1]);
    if(recorded!==counts[key])throw new Error('JUNIT_COUNT_MISMATCH: '+relative);
  }
  const guardPath=directory+'/'+run+'/guards.json';
  const guard=JSON.parse(read(guardPath));
  if(guard.pytest_exit!==exitCode)throw new Error('EXIT_MISMATCH: '+relative);
  source(relative);source(guardPath);
  if(!data.tests.some(t=>t.reference===relative))data.tests.push({
    exitCode,historical:true,deselected,skipped:counts.skipped,violations:guard.violations,
    id:run,tests:counts.tests,reference:relative,failures:counts.failures,errors:counts.errors,
    status:exitCode===0&&guard.violations.length===0?'PASS':counts.errors?'ERROR':'FAIL'});
}
for(const item of rag.runs)appendRun(ragDir,item.run,item.counts,item.exit_code,item.deselected);
for(const item of cloud.test_runs)appendRun(cloudDir,item.run,item.counts,item.exit_code,item.deselected);
const gate=data.gates.find(g=>g.id==='WEIP-10');
gate.status='PASS';
gate.detail='Scoped offline PASS: approval/provenance rejection, temporary RAG ingestion, transaction failure injection and preservation of older documents. Latest targeted: 29 PASS; related regression: 208 PASS, 6 deselected. Active-store integration and runtime recovery NOT_VERIFIED.';
gate.reference=ragDir+'/EXECUTION_RESULTS.json';
data.verifiedCapabilities=[
  {id:'WEIP-TEMP',name:'WEIP ↔ RAG temporary store',status:'IMPLEMENTED_VERIFIED_SCOPED',
   detail:'Validasi dokumen, penolakan retrieval, transaksi dan rollback diuji pada store sementara. Integrasi aktif tetap NOT_AUTHORIZED.',
   fingerprint:'',fingerprintScope:'Source knowledge pada laporan diperiksa cocok; bukan identitas runtime.',
   reference:ragDir+'/EXECUTION_RESULTS.json'},
  {id:'OPENROUTER-LANGGRAPH',name:'OpenRouter dan workflow LangGraph',status:'IMPLEMENTED_VERIFIED_SCOPED_OFFLINE',
   detail:'169 PASS, 0 FAIL, 0 SKIP, 3 deselected. Provider mock; Ollama tetap default. Workflow opsional nonaktif. Biaya aktual dan panggilan cloud nyata UNKNOWN.',
   fingerprint:cloud.audit.fingerprint,fingerprintScope:cloud.audit.note,
   reference:cloudDir+'/IMPLEMENTATION_REPORT.json'}
];
data.exclusionGroups=[
  {name:'WEIP regression awal dan lanjutan',detail:'6 deselected: actual_v2, dev_endpoint, consumers_correlation, empty_result, bootstrap_layers, owner_reads. Targeted selection memiliki jumlah tersendiri pada setiap run.',reference:ragDir+'/EXECUTION_RESULTS.json'},
  {name:'OpenRouter/LangGraph regression',detail:'3 deselected: runtime_instances_differ_in_real_subprocesses, bootstrap_layers_preserve_provenance_and_secrets, owner_reads_dotenv_once_and_process_environment_wins. Membutuhkan subprocess atau bootstrap di luar scope offline.',reference:cloudDir+'/IMPLEMENTATION_REPORT.json'}
];
data.capturedAt=new Date().toISOString();
// Keep the old whole-app fingerprint as a historical WEIP archive identifier.
const output='export default '+JSON.stringify(data,null,2)+';\n';
fs.writeFileSync(target,original.includes('\r\n')?output.replaceAll('\n','\r\n'):output,'utf8');
console.log(JSON.stringify({tests:data.tests.length,sources:data.sources.length,unavailableRuns:data.unavailableRuns.length}));
