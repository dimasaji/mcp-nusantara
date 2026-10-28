const {chromium}=require('../control-plane/node_modules/playwright');
const fs=require('node:fs');const path=require('node:path');
(async()=>{
 const out=path.resolve('artifacts/sop-integration');
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const model=await (await page.request.get('http://127.0.0.1:8765/v1/control-plane/model-status')).json();
  if(model.provider!=='ollama')throw Error('Local provider required; no chat request made');
  await page.goto('http://127.0.0.1:5180/');
  await page.getByLabel('Pertanyaan Anda',{exact:true}).fill('Apa persyaratan permohonan data pribadi?');
  const response=page.waitForResponse(r=>r.url().endsWith('/v1/chat')&&r.request().method()==='POST',{timeout:45000});
  await page.getByRole('button',{name:'Kirim pertanyaan',exact:true}).click();
  const result=await (await response).json();
  if(!result.grounding?.grounded||!result.response?.toLowerCase().includes('surat permohonan')||!result.evidence?.some(e=>e.title==='SOP Permohonan Data Pribadi (PIAK-03)'))throw Error('Expected grounded SOP answer missing');
  if(/\bKTP\b|Kartu Keluarga/i.test(result.response))throw Error('Unsupported extra requirement');
  await page.getByText(result.response,{exact:true}).waitFor();
  await page.screenshot({path:path.join(out,'chat-ui.png'),fullPage:true});
  const report={url:page.url(),question:'Apa persyaratan permohonan data pribadi?',answer:result.response,
   grounding:result.grounding,sources:result.evidence.map(e=>({document_id:e.document_id,title:e.title})),page_errors:errors,provider_status:result.provider_status};
  fs.writeFileSync(path.join(out,'chat-ui.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
  if(errors.length)throw Error('Browser page errors observed');
 }finally{await browser.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
