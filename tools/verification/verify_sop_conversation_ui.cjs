const {chromium}=require('../control-plane/node_modules/playwright');
const fs=require('node:fs');const path=require('node:path');const assert=require('node:assert/strict');
(async()=>{
 const out=path.resolve('artifacts/sop-conversation/browser-'+new Date().toISOString().replace(/[:.]/g,'-'));
 fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  const model=await(await page.request.get('http://127.0.0.1:8765/v1/control-plane/model-status')).json();
  assert.equal(model.provider,'ollama','Local provider required; no paid request allowed');
  await page.goto('http://127.0.0.1:5180/');
  const turns=[];const sessions=[];
  for(const question of ['Mau minta data pribadi, bawa apa?','Kalau prosesnya?','Berapa lama?','Bisa online?']){
   await page.getByLabel('Pertanyaan Anda',{exact:true}).fill(question);
   const pending=page.waitForResponse(r=>r.url().endsWith('/v1/chat')&&r.request().method()==='POST',{timeout:45000});
   await page.getByRole('button',{name:'Kirim pertanyaan',exact:true}).click();
   const response=await pending;assert.equal(response.status(),200);
   const result=await response.json();sessions.push(response.request().postDataJSON().session_id);
   await page.getByText(result.response,{exact:true}).last().waitFor();
   assert(result.grounding.grounded);assert(result.evidence.some(e=>e.title.includes('PIAK-03')));
   turns.push({question,result});
  }
  assert.equal(new Set(sessions).size,1);
  assert.match(turns[0].result.response,/surat permohonan/i);
  assert.doesNotMatch(turns[0].result.response,/\bKTP\b|Kartu Keluarga|sudah|telah|kami/i);
  assert.match(turns[2].result.response,/3 hari kerja/i);
  assert.match(turns[2].result.response,/SOP|tercantum|menurut|sumber/i);
  assert.equal(turns[3].result.grounding.reason,'grounded_abstention');
  assert.match(turns[3].result.response,/belum tersedia/i);
  const source=page.locator('.citation').last();
  await source.locator('summary').click();assert(await source.locator('blockquote').isVisible());
  await page.screenshot({path:path.join(out,'conversation.png'),fullPage:true});
  fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify({url:page.url(),model:model.model,provider:model.provider,turns,same_session:true,source_quote_open:true,page_errors:errors},null,2));
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({artifact:out,turns:turns.map(t=>({question:t.question,response:t.result.response,origin:t.result.provider_status,grounding:t.result.grounding})),same_session:true,source_quote_open:true,page_errors:errors}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
