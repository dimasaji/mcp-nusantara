const {chromium}=require('../control-plane/node_modules/playwright');
const fs=require('node:fs');
const path=require('node:path');
const {execFileSync}=require('node:child_process');
const assert=require('node:assert/strict');

(async()=>{
 const root=path.resolve(__dirname,'..');
 const output=path.join(root,'artifacts/knowledge-pipeline-runtime','browser-'+new Date().toISOString().replace(/[:.]/g,'-'));
 fs.mkdirSync(output,{recursive:true});
 const token=process.env.NUSANTARA_ADMIN_TOKEN||execFileSync(path.join(root,'.venv/Scripts/python.exe'),['-c',"from dotenv import dotenv_values; print(dotenv_values('.env', interpolate=False).get('NUSANTARA_ADMIN_TOKEN') or '')"],{cwd:root,encoding:'utf8'}).trim();
 assert(token,'Configured operator credential unavailable');
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];const mutations=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(r.method()==='POST'&&/decisions|execute-reviewed/.test(r.url()))mutations.push(r.url());});
  const health=await(await page.request.get('http://127.0.0.1:8765/health')).json();assert.equal(health.status,'ok');
  const model=await(await page.request.get('http://127.0.0.1:8765/v1/control-plane/model-status')).json();assert.equal(model.provider,'ollama');
  let response=await page.goto('http://127.0.0.1:5180/dashboard');assert.equal(response.status(),200);
  await page.getByRole('heading',{name:'Dokumen dan pemantauan'}).waitFor();
  assert.doesNotMatch(await page.locator('body').innerText(),/PIAK-03|SampleDashboard/);
  const pipelinePath='http://127.0.0.1:8765/v1/knowledge/pipeline/status';
  const noAuth=await page.request.get(pipelinePath);assert.equal(noAuth.status(),403);
  const headers={'X-Admin-Token':token};
  const pipelineResponse=await page.request.get(pipelinePath,{headers});
  const pipeline=await pipelineResponse.json();
  assert.equal(pipelineResponse.status(),200,`pipeline status returned HTTP ${pipelineResponse.status()}: ${JSON.stringify(pipeline).slice(0,300)}`);
  assert.equal(pipeline.source,'Chat RAG SQLite store');assert.equal(pipeline.watch.enabled,false);
  const knowledge=await page.request.get('http://127.0.0.1:8765/v1/control-plane/knowledge-status',{headers});
  assert.equal(knowledge.status(),200);const active=await knowledge.json();assert.equal(pipeline.database,active.database);
  const historyUrl='http://127.0.0.1:8765/v1/control-plane/history';
  const before=await(await page.request.get(historyUrl,{headers})).json();
  await page.getByRole('link',{name:/Review & Human Decision Gate/}).click();
  await page.getByLabel('Token operator',{exact:true}).fill(token);
  await page.getByText('Operator terautentikasi sebagai pemegang token admin bersama.',{exact:true}).waitFor();
  await page.locator('a[href="/dashboard"]').first().click();
  await page.waitForURL('**/dashboard');
  await page.getByText(/dokumen ada di index Chat/).waitFor({timeout:10000});
  await page.getByRole('link',{name:'Chat',exact:true}).click();
  await page.getByRole('heading',{name:'Asisten Anda'}).waitFor();
  await page.getByLabel('Pertanyaan Anda',{exact:true}).fill('Halo');
  const chatResponse=page.waitForResponse(r=>r.url().endsWith('/v1/chat')&&r.request().method()==='POST',{timeout:60000});
  await page.getByRole('button',{name:'Kirim pertanyaan',exact:true}).click();
  const chat=await chatResponse;assert.equal(chat.status(),200);const answer=await chat.json();
  await page.getByText(answer.response,{exact:true}).waitFor();
  const after=await(await page.request.get(historyUrl,{headers})).json();
  assert.deepEqual(after,before);assert.deepEqual(mutations,[]);assert.deepEqual(errors,[]);
  await page.screenshot({path:path.join(output,'chat.png'),fullPage:true});
  const result={url:'http://127.0.0.1:5180/dashboard',frontend_status:200,backend_health:health.status,
    model_provider:model.provider,knowledge_status:knowledge.status,shared_chat_store:pipeline.database===active.database,
    pipeline_auth_required:noAuth.status===403,watch_enabled:pipeline.watch.enabled,
    history_read_without_decision:true,history_unchanged:true,chat_status:chat.status(),chat_answer_visible:true,
    pii_or_sample_menu_visible:false,human_decision_posted:false,execution_posted:false,page_errors:errors};
  fs.writeFileSync(path.join(output,'validation.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({...result,artifact:path.relative(root,output)}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
