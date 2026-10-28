import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdirSync,writeFileSync,readFileSync} from 'node:fs';
import {initialState,STORAGE_KEY} from '../dist/core.js';

// Lightweight DOM adapter for programmatic render/action checks. This is not browser QA.
class Element {
 constructor(id){this.id=id;this.innerHTML='';this.textContent='';this.value='';this.open=false;this.isConnected=true;this.tagName='DIV';this.dataset={};this.attrs={};this.events={};this.classes=new Set();this.classList={add:x=>this.classes.add(x),remove:x=>this.classes.delete(x),toggle:(x,on)=>{const next=on??!this.classes.has(x);next?this.classes.add(x):this.classes.delete(x);return next;}};}
 setAttribute(k,v){this.attrs[k]=v;}
 addEventListener(k,f){this.events[k]=f;}
 focus(){document.activeElement=this;}
 querySelector(sel){return get(sel);}
 showModal(){this.open=true;}
 close(){this.open=false;this.events.close?.();}
 click(){}
 getBoundingClientRect(){return {left:0,top:0,right:600,bottom:900};}
}
const elements=new Map(),listeners=new Map(),get=id=>{if(!elements.has(id))elements.set(id,new Element(id));return elements.get(id);};
const stored=new Map();
globalThis.localStorage={getItem:k=>stored.get(k)||null,setItem:(k,v)=>stored.set(k,v)};
globalThis.location={hash:''};
globalThis.history={replaceState:(a,b,url)=>{location.hash=url;}};
globalThis.window={scrollTo(){},addEventListener(){}};
globalThis.document={getElementById:get,querySelectorAll:()=>[],createElement:()=>new Element('created'),addEventListener:(name,fn)=>listeners.set(name,fn),body:new Element('body'),activeElement:new Element('initial')};
globalThis.setTimeout=()=>0;globalThis.clearTimeout=()=>{};
const {handleAction,retrievalAnswer}=await import('../dist/app.js');
const main=()=>get('main').innerHTML,detail=()=>get('dialog-content').innerHTML;
const data=()=>JSON.parse(stored.get(STORAGE_KEY)||JSON.stringify(initialState()));
const action=(a,id)=>handleAction(a,id);
const submitDecision=reason=>{get('decision-reason').value=reason;listeners.get('submit')({target:{id:'decision-form'},preventDefault(){}});};
mkdirSync('qa/rendered',{recursive:true});
const snapshot=name=>writeFileSync(`qa/rendered/${name}.html`,readFileSync('dist/index.html','utf8').replace('<main id="main" tabindex="-1"></main>',`<main id="main" tabindex="-1">${main()}</main>`));

test('UI render/action main flows (DOM adapter, no browser)',async t=>{
 await t.test('initial homepage contains four questions, demo source, and held gates',()=>{for(const s of ['Apa yang dikerjakan?','Apa masalahnya?','Perlu persetujuan?','Berapa biayanya?','Data contoh','BLOCKED'])assert.ok(main().includes(s),s);snapshot('beranda');});
 await t.test('all four pages and settings sections render without errors',async()=>{
  for(const id of ['beranda','workspace','human','settings']){await action('nav',id);assert.match(main(),/Data contoh/);snapshot(id);}
  for(const id of ['knowledge','models','health','governance','system']){await action('tab',id);assert.ok(main().length>2000);snapshot(id);}
 });
 await t.test('blocker opens evidence, impact, hypothesis, and specific next steps',async()=>{await action('blocker','chat');assert.ok(get('detail-dialog').open);for(const x of ['HIPOTESIS','ev-chat','Dampak pada alur','Langkah penelusuran'])assert.ok(detail().includes(x));await action('evidence','ev-chat');assert.match(detail(),/http_status: 503/);});
 await t.test('operator report clearly identifies source and verification limit',async()=>{await action('evidence','ev-reported');assert.match(detail(),/LAPORAN OPERATOR/);assert.match(detail(),/belum diverifikasi/);assert.match(detail(),/browserErrors: \[\]/);});
 await t.test('approval dialog disables PASS before verification',async()=>{await action('approval');assert.match(detail(),/data-id="PASS"[^>]*disabled/);});
 await t.test('resolve blocker -> review PASS -> execution updates gates and persistence',async()=>{
  await action('resolve-confirm','chat');assert.match(detail(),/tidak menjalankan pengujian nyata/);await action('resolve','chat');
  assert.ok(data().resolved.includes('chat'));await action('approval');assert.doesNotMatch(detail(),/data-id="PASS"[^>]*disabled/);
  await action('select-decision','PASS');submitDecision('Evidence contoh dan lingkup lokal telah ditinjau.');assert.equal(data().decision,'PASS');
  assert.match(main(),/Siap disimulasikan/);await action('execute');assert.equal(data().executed,true);assert.match(main(),/Simulasi selesai/);snapshot('human-complete');
 });
 await t.test('changing route invalidates human approval and returns execution to BLOCKED',async()=>{await action('tab','models');await action('route','cloud');assert.equal(data().decision,'HOLD');assert.equal(data().executed,false);await action('gate','plan');assert.match(detail(),/Tertunda/);await action('route','local');});
 await t.test('FAIL and HOLD decisions are recorded with escaped user text',async()=>{await action('approval');await action('select-decision','FAIL');submitDecision('<script>alert("test")</script> perlu bukti');assert.equal(data().decision,'FAIL');assert.ok(main().includes('&lt;script&gt;'));assert.ok(!main().includes('<script>alert'));await action('approval');await action('select-decision','HOLD');submitDecision('Menunggu evidence tambahan');assert.equal(data().decision,'HOLD');});
 await t.test('evidence filters show only selected outcome and maintain counts',async()=>{await action('evidence-list');await action('evidence-filter','FAIL');assert.match(main(),/Jejak percakapan PIAK-03/);assert.doesNotMatch(main(),/Browser Qwen · laporan operator/);await action('evidence-filter','ALL');snapshot('evidence');});
 await t.test('global search handles both matches and empty results',async()=>{await action('search');get('global-query').value='503';listeners.get('input')({target:{id:'global-query',value:'503'}});assert.match(get('global-results').innerHTML,/Chat berhenti/);listeners.get('input')({target:{id:'global-query',value:'no-match-xyz'}});assert.match(get('global-results').innerHTML,/Tidak ditemukan/);});
 await t.test('retrieval supports known source questions and refuses unsupported detail',async()=>{await action('retrieval');await action('sample-query','Apa syaratnya?');assert.match(get('retrieval-result').innerHTML,/Surat Permohonan/);assert.match(get('retrieval-result').innerHTML,/PIAK-03/);assert.match(retrievalAnswer('Berapa lama?')[0],/3 Hari Kerja/);assert.equal(retrievalAnswer('Apakah bisa online?')[1],null);assert.equal(retrievalAnswer('Berapa biayanya?')[1],null);});
 await t.test('system reset restores baseline without altering operator report',async()=>{await action('reset');assert.match(detail(),/kondisi awal/);await action('reset-confirm');assert.deepEqual(data(),initialState());await action('nav','beranda');assert.match(main(),/02/);await action('evidence','ev-reported');assert.match(detail(),/browserErrors/);});
});
