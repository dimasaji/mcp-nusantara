const {chromium}=require('../control-plane/node_modules/playwright');
const fs=require('node:fs');const path=require('node:path');const assert=require('node:assert/strict');const crypto=require('node:crypto');const {execFileSync}=require('node:child_process');
(async()=>{
 const root=path.resolve(__dirname,'..');const id=Date.now();const out=path.join(root,'artifacts/knowledge-upload-entry','browser-'+id);fs.mkdirSync(out,{recursive:true});
 const py=path.join(root,'.venv/Scripts/python.exe');
 const token=execFileSync(py,['-c',"from dotenv import dotenv_values; print(dotenv_values('.env',interpolate=False).get('NUSANTARA_ADMIN_TOKEN') or '')"],{cwd:root,encoding:'utf8'}).trim();assert(token,'Existing operator credential unavailable');
 const source=path.join(out,`browser-chosen-${id}.pdf`);
 const generator=`import sys
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject,DictionaryObject,NameObject
w=PdfWriter();p=w.add_blank_page(width=600,height=800)
font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
p[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):font})})
s=DecodedStreamObject();s.set_data(('BT /F1 10 Tf 30 750 Td (Browser upload test '+sys.argv[2]+'. This document was selected through the browser file chooser and stored in the shared knowledge index.) Tj ET').encode())
p[NameObject('/Contents')]=s
with open(sys.argv[1],'wb') as f:w.write(f)
`;
 execFileSync(py,['-c',generator,source,String(id)],{cwd:root});
 const raw=fs.readFileSync(source);const digest=crypto.createHash('sha256').update(raw).digest('hex');
 const report={url:'http://127.0.0.1:5180/knowledge',scope:'ACTIVE_ISOLATED_APPLICATION_BROWSER_UPLOAD',file_is_test_fixture:true,
   upload_method:'Click DOM file input -> browser FileChooser -> click UI upload/retry',steps:[],requests:[],page_errors:[]};
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  page.on('pageerror',e=>report.page_errors.push(e.message));
  page.on('request',r=>{if(r.url().endsWith('/v1/knowledge/pipeline/documents')){const body=r.postDataBuffer();report.requests.push({method:r.method(),url:r.url(),bytes:body?.length,sha256:body?crypto.createHash('sha256').update(body).digest('hex'):null,auth_header_present:!!r.headers()['x-admin-token']});}});
  await page.goto(report.url);await page.getByRole('heading',{name:'Tambahkan dokumen',exact:true}).waitFor();
  const picker=page.getByLabel('Pilih dokumen');const uploader=page.locator('section[aria-label="Tambahkan dokumen"]');
  assert(await picker.isEnabled());assert(await page.getByLabel('Token operator',{exact:true}).isVisible());
  const chooser=page.waitForEvent('filechooser');await picker.click();await(await chooser).setFiles(source);
  await uploader.getByText(path.basename(source),{exact:true}).waitFor();assert(await uploader.getByRole('button',{name:'Proses dan validasi',exact:true}).isDisabled());
  report.steps.push({step:'direct-entry-file-chooser',picker_enabled:true,selected_before_login:true,upload_requires_auth:true});
  await page.getByLabel('Token operator',{exact:true}).fill('rejected-fixture-token');
  let response=page.waitForResponse(r=>r.url().includes('/v1/knowledge/pipeline/status')&&r.status()===403);
  await page.getByRole('button',{name:'Verifikasi akses',exact:true}).click();await response;
  await page.getByText(/Status tidak tersedia: Akses ditolak/).waitFor();report.steps.push({step:'wrong-login',http:403,readable_error:true,file_retained:await uploader.getByText(path.basename(source),{exact:true}).isVisible()});
  async function authenticate(){await page.getByLabel('Token operator',{exact:true}).fill(token);const check=page.waitForResponse(r=>r.url().includes('/v1/knowledge/pipeline/status')&&r.status()===200);await page.getByRole('button',{name:'Verifikasi akses',exact:true}).click();await check;await page.getByText('Akses operator terverifikasi. Anda dapat mengunggah file.',{exact:true}).waitFor();}
  await authenticate();
  const before=await(await page.request.get('http://127.0.0.1:5180/v1/knowledge/pipeline/status',{headers:{'X-Admin-Token':token}})).json();
  // Real backend denial after a previously successful access check; only this
  // browser request header is changed, never the configured admin credential.
  const endpoint='**/v1/knowledge/pipeline/documents';
  await page.route(endpoint,async route=>route.continue({headers:{...await route.request().allHeaders(),'x-admin-token':'rejected-fixture-upload'}}));
  response=page.waitForResponse(r=>r.url().endsWith('/v1/knowledge/pipeline/documents')&&r.request().method()==='POST');
  await uploader.getByRole('button',{name:'Proses dan validasi',exact:true}).click();const denied=await response;assert.equal(denied.status(),403);
  await uploader.getByRole('alert').getByText(/Token operator ditolak/).waitFor();assert(await uploader.getByText(path.basename(source),{exact:true}).isVisible());
  report.steps.push({step:'upload-denied-by-real-backend',http:403,simulation:'request header only',readable_error:true,file_retained:true});
  await page.screenshot({path:path.join(out,'rejected-desktop.png'),fullPage:true});await page.unroute(endpoint);
  response=page.waitForResponse(r=>r.url().endsWith('/v1/knowledge/pipeline/documents')&&r.request().method()==='POST',{timeout:120000});
  await uploader.getByRole('button',{name:'Coba Lagi',exact:true}).click();const uploaded=await response;const ready=await uploaded.json();assert.equal(uploaded.status(),200);assert.equal(ready.status,'READY',JSON.stringify(ready));
  assert.equal(ready.source_sha256,digest);const stored=path.resolve(ready.source_path);
  const allowed=path.join(root,'artifacts/nusantara-e2e-20261016-1018/isolated-runtime/knowledge/source-documents')+path.sep;assert(stored.startsWith(allowed));assert.equal(crypto.createHash('sha256').update(fs.readFileSync(stored)).digest('hex'),digest);
  report.steps.push({step:'browser-upload-storage-processing',http:200,status:ready.status,run_id:ready.run_id,document_id:ready.document_id,source_sha256:digest,original_bytes_preserved:true});
  await page.getByText(/Dokumen berhasil disimpan dan diproses/).waitFor();assert.equal(await picker.inputValue(),'','Successful upload must clear the visible native picker consistently with UI state');await page.screenshot({path:path.join(out,'ready-desktop.png'),fullPage:true});
  await page.reload();assert(await page.getByLabel('Pilih dokumen').isEnabled());await authenticate();
  const row=page.getByRole('row').filter({hasText:path.basename(source)});await row.getByRole('cell',{name:'READY',exact:true}).waitFor();report.steps.push({step:'history-after-refresh',persisted:true,inline_reauthentication:true});
  const pipeline=await(await page.request.get('http://127.0.0.1:5180/v1/knowledge/pipeline/status',{headers:{'X-Admin-Token':token}})).json();
  const identity=await(await page.request.get('http://127.0.0.1:8766/v1/control-plane/knowledge-status',{headers:{'X-Admin-Token':token}})).json();
  assert.equal(pipeline.database,identity.database);assert.equal(pipeline.documents_indexed,before.documents_indexed+1);
  report.steps.push({step:'proxy-and-chat-store',shared_database:true,new_documents:1,history_run_found:pipeline.runs.some(r=>r.run_id===ready.run_id)});
  await page.setViewportSize({width:390,height:844});const chooseAgain=page.waitForEvent('filechooser');await page.getByLabel('Pilih dokumen').click();await(await chooseAgain).setFiles(source);
  response=page.waitForResponse(r=>r.url().endsWith('/v1/knowledge/pipeline/documents')&&r.request().method()==='POST',{timeout:120000});await uploader.getByRole('button',{name:'Proses dan validasi',exact:true}).click();const duplicate=await(await response).json();assert.equal(duplicate.status,'DUPLICATE');assert.equal(duplicate.document_id,ready.document_id);
  await page.getByText(/File tersimpan; isinya sudah ada di index Chat/).waitFor();assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth),false);await page.screenshot({path:path.join(out,'ready-mobile.png'),fullPage:true});
  report.steps.push({step:'mobile-browser-upload',width:390,status:'DUPLICATE',same_document:true,horizontal_overflow:false});
  assert.equal(report.requests.length,3);assert(report.requests.every(r=>r.sha256===digest&&r.auth_header_present));assert.deepEqual(report.page_errors,[]);
  report.result='BROWSER_UPLOAD_VERIFIED';fs.writeFileSync(path.join(out,'result.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({artifact:out,result:report.result,steps:report.steps.map(s=>s.step)}));
 }catch(e){report.result='FAILED';report.error=e.message;fs.writeFileSync(path.join(out,'result.json'),JSON.stringify(report,null,2));throw e;}finally{await browser.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
