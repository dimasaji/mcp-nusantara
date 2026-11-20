const {chromium}=require('../control-plane/node_modules/playwright');
const fs=require('node:fs');const path=require('node:path');const assert=require('node:assert/strict');const {execFileSync}=require('node:child_process');
(async()=>{
 const root=path.resolve(__dirname,'..');const out=path.join(root,'artifacts/nusantara-e2e-20261016-1018','upload-'+Date.now());fs.mkdirSync(out,{recursive:true});
 const token=execFileSync(path.join(root,'.venv/Scripts/python.exe'),['-c',"from dotenv import dotenv_values; print(dotenv_values('.env',interpolate=False).get('NUSANTARA_ADMIN_TOKEN') or '')"],{cwd:root,encoding:'utf8'}).trim();assert(token);
 execFileSync(path.join(root,'.venv/Scripts/python.exe'),['-c',"import sys; from pathlib import Path; sys.path.insert(0,'tests'); from test_knowledge_pipeline_api import pdf_bytes; Path('artifacts/nusantara-e2e-20261016-1018/fixture.pdf').write_bytes(pdf_bytes())"],{cwd:root});
 const browser=await chromium.launch({channel:'msedge',headless:true});const report={scope:'ISOLATED_REAL_APPLICATION_SYNTHETIC_PDF',human_decisions_posted:false,paid_calls:false,checks:[]};
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  await page.goto('http://127.0.0.1:5180/settings');await page.getByLabel('Token operator',{exact:true}).fill(token);
  await page.locator('a[href="/knowledge"]').first().click();await page.getByText(/dokumen ada di index Chat/).waitFor();
  await page.getByLabel('Pilih dokumen').setInputFiles(path.join(root,'artifacts/nusantara-e2e-20261016-1018/fixture.pdf'));
  let response=page.waitForResponse(r=>r.url().endsWith('/v1/knowledge/pipeline/documents')&&r.request().method()==='POST',{timeout:120000});
  await page.getByRole('button',{name:'Proses dan validasi',exact:true}).click();let result=await(await response).json();report.checks.push({step:'upload',result});assert(['READY','DUPLICATE'].includes(result.status),JSON.stringify(result));
  await page.getByRole('link',{name:'Buka Chat',exact:true}).waitFor();
  await page.screenshot({path:path.join(out,'knowledge-desktop.png'),fullPage:true});
  await page.reload();await page.getByText(/Token operator diperlukan untuk operasi/).waitFor();
  await page.locator('a[href="/settings"]').click();await page.getByLabel('Token operator',{exact:true}).fill(token);await page.locator('a[href="/knowledge"]').first().click();
  await page.getByText('fixture.pdf',{exact:true}).first().waitFor();report.checks.push({step:'history-after-refresh',persisted:true});
  await page.getByRole('link',{name:'Buka Chat',exact:true}).click();
  const model=await(await page.request.get('http://127.0.0.1:8766/v1/control-plane/model-status')).json();assert.equal(model.provider,'ollama');
  const question='Apa persyaratan layanan?';await page.getByLabel('Pertanyaan Anda').fill(question);
  response=page.waitForResponse(r=>r.url().endsWith('/v1/chat')&&r.request().method()==='POST',{timeout:120000});await page.getByRole('button',{name:'Kirim pertanyaan',exact:true}).click();
  const chat=await response;result=await chat.json();report.checks.push({step:'chat',http:chat.status(),result});assert.equal(chat.status(),200);
  assert.doesNotMatch(result.response,/\b(?:jumat|sabtu|minggu|petugas)\b/i,'Model added facts absent from the synthetic PDF');
  await page.getByText(result.response,{exact:true}).waitFor();await page.screenshot({path:path.join(out,'chat-desktop.png'),fullPage:true});
  await page.reload();await page.getByText(result.response,{exact:true}).waitFor();report.checks.push({step:'chat-history-after-refresh',persisted:true});
  await page.setViewportSize({width:390,height:844});await page.screenshot({path:path.join(out,'chat-mobile.png'),fullPage:true});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth),false);
  fs.writeFileSync(path.join(out,'result.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({artifact:out,checks:report.checks.map(c=>c.step)}));
 }catch(e){report.error=e.message;fs.writeFileSync(path.join(out,'result.json'),JSON.stringify(report,null,2));throw e;}finally{await browser.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
