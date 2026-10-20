const fs=require('node:fs');const path=require('node:path');
const {chromium}=require('../control-plane/node_modules/playwright');
(async()=>{
 const out=path.resolve(__dirname,'../artifacts/chat-p0-20261019');fs.mkdirSync(out,{recursive:true});
 const approved=process.env.NCP_CHAT_BUDGET_APPROVED==='USD0.05_MAX5';
 let vite;let origin='http://127.0.0.1:5180';
 const phase=process.env.NCP_CHAT_PHASE||'initial';
 const tag=process.env.NCP_CHAT_EVIDENCE_TAG||'browser-chat';
 if(process.env.NCP_CHAT_TEMP_BACKEND){
  process.env.NUSANTARA_BACKEND_URL=process.env.NCP_CHAT_TEMP_BACKEND;
  process.chdir(path.resolve(__dirname,'../control-plane'));
  const {pathToFileURL}=require('node:url');
  const {createServer}=await import(pathToFileURL(path.resolve('node_modules/vite/dist/node/index.js')).href);
  vite=await createServer({server:{host:'127.0.0.1',port:0,strictPort:false},logLevel:'silent'});
  await vite.listen();origin=`http://127.0.0.1:${vite.httpServer.address().port}`;
 }
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const report={scope:approved?'ACTUAL_BROWSER_CHAT_APPROVED_MAX_USD_0_05_MAX_5_DISPATCH':'READ_ONLY_CHAT_PREFLIGHT',phase,url:origin+'/ui',checks:[],turns:[],errors:[]};
 const check=(name,ok)=>{report.checks.push({name,status:ok?'PASS':'FAIL'});if(!ok)throw new Error(name)};
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  page.on('pageerror',e=>report.errors.push(e.name));
  const opened=await page.goto(report.url);await page.getByRole('heading',{name:'Asisten Anda',exact:true}).waitFor();
  check('chat-url-opens',opened.status()===200);
  check('question-input-enabled',await page.getByLabel('Pertanyaan Anda').isEnabled());
  const status=await page.request.get(origin+'/v1/control-plane/model-status');
  const model=await status.json();report.model={provider:model.provider,model:model.model,revision:model.revision,process_id:model.process_id};
  check('configured-provider-unchanged',model.provider==='openrouter'&&model.model==='openai/gpt-4o-mini');
  if(!approved){await page.screenshot({path:path.join(out,'preflight.png'),fullPage:true});return;}
  const general={kind:'general',question:'Halo, siapa kamu?'};
  const sop=[{kind:'requirements',question:'Apa persyaratan permohonan data pribadi berdasarkan SOP PIAK-03?'},{kind:'procedure',question:'Bagaimana prosedurnya?'},{kind:'duration',question:'Berapa lama prosesnya?'}];
  const noPaidSop=phase==='sop-no-dispatch'&&process.env.NCP_CHAT_TEMP_BACKEND&&process.env.NCP_CHAT_NO_PAID_SERVER_GUARD==='1';
  const questions=noPaidSop?sop:phase==='live-after-fix'?[...sop,general]:phase==='canary-after-fix'?[general,...sop]:[general,{kind:'general',question:'Jelaskan rekursi dalam dua kalimat.'},...sop];
  for(const [index,{question,kind}] of questions.entries()){
   if(index>=5)throw new Error('APPROVED_REQUEST_LIMIT');
   if(phase!=='initial'&&!noPaidSop){
    if(!process.env.NCP_OPERATOR_TOKEN)throw new Error('BUDGET_OBSERVER_REQUIRED');
    const ledger=await page.request.get(origin+'/v1/control-plane/cost-summary',{headers:{'X-Admin-Token':process.env.NCP_OPERATOR_TOKEN}});
    const cost=JSON.parse((await ledger.text()).replace(/^[^{]*/,''));
    const finalRemaining=phase==='live-after-fix';
    if(finalRemaining){
      const accounting=JSON.parse(fs.readFileSync(path.join(out,'approval-accounting.json'),'utf8').replace(/^[^{]*/,''));
     if(accounting.observed_agent_dispatches!==4||accounting.remaining_agent_dispatches!==1)throw new Error('REMAINING_APPROVAL_NOT_PROVEN');
    }
    const baseline=JSON.parse(fs.readFileSync(path.join(out,finalRemaining?'cost-before-live.json':'cost-before.json'),'utf8'));
    const prior=new Set(baseline.history.map(r=>r.request_id));
    const used=cost.history.filter(r=>!prior.has(r.request_id)).length;
    const spent=Number(cost.actual_usd)+Number(cost.reserved_usd)-Number(baseline.actual_usd)-Number(baseline.reserved_usd);
    const limit=finalRemaining?1:5;
    if(!ledger.ok()||used>=limit||Math.round(spent*100)>=limit)throw new Error('APPROVED_TOTAL_BUDGET_EXHAUSTED');
    report.budgetBeforeLastRequest={dispatchesSinceApproval:used,ledgerUsdSinceApproval:spent.toFixed(2)};
   }
   await page.getByLabel('Pertanyaan Anda').fill(question);
   const waiting=page.waitForResponse(r=>new URL(r.url()).pathname==='/v1/chat'&&r.request().method()==='POST',{timeout:100000});
   await page.getByRole('button',{name:'Kirim pertanyaan',exact:true}).click();
   const response=await waiting;const request=response.request().postDataJSON();
   const body=await response.json().catch(()=>({}));
   report.turns.push({question,session_id:request.session_id,request_id:request.request_id,http:response.status(),provider:body.provider_status,model:body.model,response:body.response,grounding:body.grounding,citations:(body.evidence||[]).map(e=>({document_id:e.document_id,title:e.title,chunk:e.chunk})),error:response.ok()?undefined:body.detail});
   check('http-200-turn-'+index,response.status()===200);
   await page.locator('.turn .answer').nth(index).waitFor();
   check('answer-visible-turn-'+index,(await page.locator('.turn .answer').nth(index).innerText()).includes(body.response));
   check('request-id-turn-'+index,/^[a-f0-9]{32}$/.test(request.request_id));
   if(kind!=='general'){
    check('piak-source-turn-'+index,body.grounding?.grounded===true&&(body.evidence||[]).some(e=>e.title.includes('PIAK-03')));
    if(kind==='requirements')check('piak-requirements',/surat permohonan/i.test(body.response));
    if(kind==='procedure')check('piak-procedure',/verifikasi/i.test(body.response));
    if(kind==='duration')check('piak-duration',/3 hari kerja/i.test(body.response));
   }else if(phase!=='initial'){
    check('general-is-model-answer',body.provider_status==='openrouter'&&!/belum tersedia secara cukup/.test(body.response));
   }
   await page.screenshot({path:path.join(out,`${tag}-turn-${index}.png`),fullPage:true});
  }
  if(noPaidSop)check('sop-source-only',report.turns.every(t=>t.provider==='evidence_fast_path'));
  else check('actual-model-answered',report.turns.some(t=>t.provider==='openrouter'&&t.response));
  await page.getByText('History sesi ini',{exact:true}).click();
  const [read]=await Promise.all([page.waitForResponse(r=>new URL(r.url()).pathname==='/v1/chat/history'&&r.status()===200),page.getByRole('button',{name:'Muat ulang History',exact:true}).click()]);
  const history=await read.json();
  check('history-request-ids',report.turns.every(t=>history.turns.some(h=>h.request_id===t.request_id&&h.status==='SUCCEEDED'&&h.answer?.response===t.response)));
  await page.reload();await page.locator('.turn .answer').nth(questions.length-1).waitFor();
  check('history-after-browser-reload',await page.locator('.turn').count()===questions.length);
  check('no-browser-errors',report.errors.length===0);
  await page.screenshot({path:path.join(out,tag+'-final.png'),fullPage:true});
 }catch(e){report.failure=e.message;process.exitCode=1;}
 finally{fs.writeFileSync(path.join(out,approved?tag+'.json':'preflight.json'),JSON.stringify(report,null,2));await browser.close();if(vite){vite.httpServer?.closeAllConnections();await vite.close();}console.log(JSON.stringify({scope:report.scope,model:report.model,checks:report.checks,failure:report.failure}));}
})().catch(e=>{console.error(e.name);process.exitCode=1});
