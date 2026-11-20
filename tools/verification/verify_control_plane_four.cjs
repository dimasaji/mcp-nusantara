// Real Vite proxy + browser + real Backend. No route mocks or human decisions.
const fs=require('node:fs');const path=require('node:path');const {pathToFileURL}=require('node:url');
const {chromium}=require('../control-plane/node_modules/playwright');
(async()=>{
 const root=path.resolve(__dirname,'..'),out=path.join(root,'artifacts/control-plane-four-20261019');
 process.chdir(path.join(root,'control-plane'));
 const {createServer}=await import(pathToFileURL(path.join(process.cwd(),'node_modules/vite/dist/node/index.js')).href);
 const live=process.env.NCP_LIVE_ORIGIN;const prefix=live?'live-':'';
 const vite=live?{close:async()=>{}}:await createServer({server:{host:'127.0.0.1',port:0,strictPort:false},logLevel:'silent'});
 if(!live)await vite.listen();const origin=live||`http://127.0.0.1:${vite.httpServer.address().port}`;
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const report={scope:live?'LIVE_AFTER_APPROVED_RESTART_READ_ONLY_NO_GENERATION':'REAL_BROWSER_REAL_BACKEND_TEMPORARY_LISTENERS',origin,checks:[],api:[],errors:[]};
 const check=(name,ok)=>{report.checks.push({name,status:ok?'PASS':'FAIL'});if(!ok)throw new Error(name)};
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  if(live)await page.addInitScript(session=>{sessionStorage.setItem('nusantara-chat-session',session);localStorage.setItem('nusantara-chat-sessions',JSON.stringify([session]));},process.env.NCP_CHAT_SESSION);
  page.on('pageerror',e=>report.errors.push(e.name));
  page.on('response',r=>{if(r.url().startsWith(origin+'/v1/')||r.url()===origin+'/health')report.api.push({path:new URL(r.url()).pathname,http:r.status()})});
  await page.goto(origin+'/settings');await page.getByRole('heading',{name:'Pengaturan & Teknis',exact:true}).waitFor();
  await page.getByLabel('Token operator',{exact:true}).fill(process.env.NCP_OPERATOR_TOKEN);
  await page.getByText(/Dokumen terindeks: \d+/).waitFor();await page.getByText(/Backend: ok/).waitFor();
  await page.getByRole('button',{name:'Muat model tersedia',exact:true}).click();
  await page.getByLabel('Pilih model tersedia',{exact:true}).waitFor();
  check('model-catalog-read-without-selection',await page.getByLabel('Pilih model tersedia',{exact:true}).locator('option').count()>0);
  check('four-primary-menus',await page.locator('aside nav a').count()===4);
  const counts=await page.request.get(origin+'/v1/knowledge/pipeline/status',{headers:{'X-Admin-Token':process.env.NCP_OPERATOR_TOKEN}});
  const knowledge=await counts.json();check('knowledge-actual-count',await page.getByText(`Dokumen terindeks: ${knowledge.documents_indexed}`,{exact:true}).isVisible());
  await page.getByRole('button',{name:'Periksa health',exact:true}).click();
  await page.screenshot({path:path.join(out,prefix+'settings.png'),fullPage:true});
  await page.locator('aside').getByRole('link',{name:'Beranda',exact:true}).click();
  await page.getByRole('heading',{name:'Beranda',exact:true}).waitFor();
  const ledger=await page.request.get(origin+'/v1/control-plane/cost-summary',{headers:{'X-Admin-Token':process.env.NCP_OPERATOR_TOKEN}});
  const money=await ledger.json();check('ledger-existing-available',money.status==='AVAILABLE');
  await page.getByText(new RegExp(`Aktual USD ${money.actual_usd.replace('.','\\.')}`)).waitFor();
  await page.getByRole('button',{name:'Perbarui Beranda',exact:true}).click();await page.waitForLoadState('networkidle');
  check('home-real-data',true);await page.screenshot({path:path.join(out,prefix+'home.png'),fullPage:true});
  await page.locator('aside').getByRole('link',{name:'AI Workspace',exact:true}).click();
  await page.getByRole('heading',{name:'AI Workspace',exact:true}).waitFor();
  await page.getByRole('heading',{name:'Status tugas V1',exact:true}).waitFor();
  check('workspace-chat-enabled',await page.getByLabel('Pertanyaan Anda').isEnabled());
  // Live mode restores the dedicated diagnostic session after restart. It never
  // sends a new Chat that could dispatch paid generation on the active service.
  if(!live){
   await page.getByLabel('Pertanyaan Anda').fill('Apa persyaratan permohonan data pribadi berdasarkan SOP PIAK-03?');
   await page.getByRole('button',{name:'Kirim pertanyaan',exact:true}).click();
  }
  await page.locator('.turn .answer').first().waitFor({timeout:90000});
  check('workspace-grounded-chat',await page.locator('.turn .answer').first().innerText().then(t=>/surat permohonan/i.test(t)&&/PIAK-03/.test(t)));
  await page.getByText('History sesi ini',{exact:true}).click();
  const [historyResponse]=await Promise.all([
   page.waitForResponse(r=>new URL(r.url()).pathname==='/v1/chat/history'&&r.status()===200),
   page.getByRole('button',{name:'Muat ulang History'}).click()
  ]);
  const history=await historyResponse.json();
  check('workspace-history',history.turns.some(t=>t.status==='SUCCEEDED'&&t.answer?.grounding?.grounded&&t.answer.evidence.some(e=>e.title.includes('PIAK-03'))));
  const summary=await page.request.get(origin+'/v1/control-plane/operations-summary',{headers:{'X-Admin-Token':process.env.NCP_OPERATOR_TOKEN}});
  const operations=await summary.json();
  check('workspace-task-source',summary.ok()&&operations.scope==='CONTROLLED_EXECUTION_ONLY');
  if(operations.tasks.length)await page.getByText(operations.tasks[0].id,{exact:true}).first().waitFor();
  await page.screenshot({path:path.join(out,prefix+'workspace.png'),fullPage:true});
  await page.locator('aside').getByRole('link',{name:'Human Control',exact:true}).click();
  await page.getByRole('heading',{name:'Human Control',exact:true}).waitFor();await page.waitForLoadState('networkidle');
  await page.waitForFunction(()=>[...document.querySelectorAll('button')].some(b=>b.textContent==='Muat ulang review'&&!b.disabled),null,{timeout:60000});
  check('human-unapproved-execution-disabled',await page.getByRole('button',{name:'Jalankan tindakan yang disetujui',exact:true}).isDisabled());
  const denied=await page.request.post(origin+'/v1/control-plane/execute-reviewed',{data:{package_id:'evp_sha256_'+'0'.repeat(64),decision_id:'dec_'+'0'.repeat(32)}});
  check('backend-enforces-authentication',denied.status()===403);
  await page.screenshot({path:path.join(out,prefix+'human.png'),fullPage:true});
  check('no-browser-errors',report.errors.length===0);
 }catch(e){report.failure=e.message;process.exitCode=1;}
 finally{fs.writeFileSync(path.join(out,prefix+'e2e.json'),JSON.stringify(report,null,2));await browser.close();await vite.close();}
 console.log(JSON.stringify({checks:report.checks,failure:report.failure,errors:report.errors}));
})().catch(e=>{fs.writeFileSync(path.resolve(__dirname,'../artifacts/control-plane-four-20261019/harness-error.json'),JSON.stringify({name:e.name,message:e.message.replace(/\b(?:sk-|Bearer )[A-Za-z0-9_-]+/g,'REDACTED')}));process.exit(1)});
