import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState,normalizeState,openBlockers,isReady,getGates,resolveBlocker,setRoute,decide,execute,allEvidence,searchRecords,escapeHtml,exportSnapshot} from '../dist/core.js';
const at='2026-10-19T09:00:00Z';
test('baseline: evidence complete while chat plan, decision, and execution remain held',()=>{
 const s=initialState();assert.deepEqual(getGates(s).map(g=>g.status),['PASS','HOLD','PASS','HOLD','BLOCKED']);assert.equal(openBlockers(s).length,2);
});
test('PASS and execution cannot bypass unresolved prerequisites',()=>{
 const s=initialState();assert.throws(()=>decide(s,'PASS','Sudah ditinjau',at),/belum tersedia/);assert.throws(()=>execute(s,at),/ditahan/);assert.equal(s.decision,'HOLD');
});
test('full local path: blocker -> evidence -> resolution -> human PASS -> simulated execution',()=>{
 const s=initialState();assert.ok(allEvidence(s).some(e=>e.id==='ev-chat'&&e.status==='FAIL'));
 resolveBlocker(s,'chat',at);assert.equal(isReady(s),true);assert.ok(allEvidence(s).some(e=>e.id==='ev-fixed'));
 assert.equal(getGates(s)[4].status,'BLOCKED');decide(s,'PASS','Alur dan sumber contoh telah ditinjau',at);assert.equal(getGates(s)[4].status,'READY');
 execute(s,at);assert.equal(getGates(s)[4].status,'PASS');assert.equal(s.events.length,3);assert.equal(openBlockers(s)[0].id,'credit');
});
test('FAIL and HOLD always inhibit execution',()=>{
 const s=initialState();resolveBlocker(s,'chat',at);for(const d of ['FAIL','HOLD']){decide(s,d,'Perlu pemeriksaan lanjutan',at);assert.throws(()=>execute(s,at),/ditahan/);assert.equal(s.executed,false);}
});
test('cloud route also requires available credit; local route does not',()=>{
 const s=initialState();resolveBlocker(s,'chat',at);setRoute(s,'cloud',at);assert.equal(isReady(s),false);
 assert.throws(()=>decide(s,'PASS','Coba persetujuan tanpa saldo',at),/belum tersedia/);resolveBlocker(s,'credit',at);assert.equal(isReady(s),true);
 decide(s,'PASS','Saldo dan alur contoh sudah ditinjau',at);execute(s,at);assert.equal(s.executed,true);
});
test('changing route invalidates prior human decision and simulated execution',()=>{
 const s=initialState();resolveBlocker(s,'chat',at);decide(s,'PASS','Bukti contoh sesuai lingkup',at);execute(s,at);setRoute(s,'cloud',at);
 assert.equal(s.executed,false);assert.equal(s.decision,'HOLD');assert.throws(()=>execute(s,at),/ditahan/);
});
test('decision reason is required, bounded, trimmed, and decision values validated',()=>{
 const s=initialState();assert.throws(()=>decide(s,'HOLD','    ',at),/minimal/);assert.throws(()=>decide(s,'HOLD','a'.repeat(501),at),/maksimal/);assert.throws(()=>decide(s,'MAYBE','Perlu tinjauan',at),/valid/);
 decide(s,'FAIL','  Butuh bukti lanjutan.  ',at);assert.equal(s.reason,'Butuh bukti lanjutan.');
});
test('invalid or corrupted saved data cannot restore a PASS that bypasses gates',()=>{
 assert.deepEqual(normalizeState(null),initialState());assert.deepEqual(normalizeState({version:999}),initialState());
 const s=normalizeState({version:1,resolved:['bad','chat','chat'],route:'cloud',decision:'PASS',executed:true,events:[{title:'x',time:'not-a-date'}]});
 assert.deepEqual(s.resolved,['chat']);assert.equal(s.decision,'HOLD');assert.equal(s.executed,false);assert.deepEqual(s.events,[]);
});
test('saved approved demo can be restored without changing its meaning',()=>{
 const s=initialState();resolveBlocker(s,'chat',at);decide(s,'PASS','Telah meninjau evidence contoh',at);execute(s,at);
 assert.deepEqual(normalizeState(JSON.parse(JSON.stringify(s))),s);
});
test('operator report is distinct from synthetic evidence and scoped accurately',()=>{
 const e=allEvidence(initialState()).find(e=>e.id==='ev-reported');assert.equal(e.source,'operator');assert.equal(e.status,'PASS');assert.match(e.body,/belum diverifikasi/);assert.match(e.body,/browserErrors: \[\]/);assert.match(e.body,/bukan pernyataan seluruh runtime/);
});
test('search covers blockers, evidence, SOP, gates, and routes including empty results',()=>{
 const s=initialState();assert.ok(searchRecords(s,'503').some(r=>r.action==='blocker'));assert.ok(searchRecords(s,'PIAK-03').some(r=>r.action==='sop'));assert.ok(searchRecords(s,'gate').some(r=>r.action==='gate'));assert.ok(searchRecords(s,'biaya').some(r=>r.id==='models'));assert.equal(searchRecords(s,'zzz-no-match-123').length,0);
});
test('user-controlled text escapes HTML special characters',()=>{
 assert.equal(escapeHtml('<img src=x onerror="x"> & \'a\''),'&lt;img src=x onerror=&quot;x&quot;&gt; &amp; &#39;a&#39;');
});
test('exports identify demo provenance and contain complete gate and evidence context',()=>{
 const e=exportSnapshot(initialState());assert.match(e.data_source,/NOT_LIVE_RUNTIME/);assert.equal(e.gates.length,5);assert.equal(e.blockers.length,2);assert.ok(e.evidence.some(r=>r.source==='operator'));
});
test('history is bounded; repeat resolve and execute do not duplicate events',()=>{
 const s=initialState();resolveBlocker(s,'chat',at);resolveBlocker(s,'chat',at);assert.equal(s.events.length,1);
 for(let i=0;i<40;i++)decide(s,'HOLD',`Peninjauan contoh nomor ${i}`,at);assert.equal(s.events.length,30);
 decide(s,'PASS','Prasyarat dan bukti lengkap',at);execute(s,at);const first=JSON.stringify(s);execute(s,at);assert.equal(JSON.stringify(s),first);
});
