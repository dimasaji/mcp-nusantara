const {chromium}=require('../control-plane/node_modules/playwright');
const fs=require('node:fs');const path=require('node:path');const assert=require('node:assert/strict');
(async()=>{
 const out=path.resolve('artifacts/knowledge-upload-entry','repro-'+Date.now());fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  const page=await browser.newPage();const requests=[];
  page.on('request',r=>{if(r.url().includes('/v1/'))requests.push({method:r.method(),url:r.url()});});
  await page.goto('http://127.0.0.1:5180/knowledge');await page.getByRole('heading',{name:'Tambahkan dokumen',exact:true}).waitFor();
  const picker=page.getByLabel('Pilih dokumen');
  const result={url:page.url(),picker_visible:await picker.isVisible(),picker_enabled:await picker.isEnabled(),
   inline_auth:await page.getByLabel('Token operator',{exact:true}).count(),
   upload_button_enabled:await page.getByRole('button',{name:'Proses dan validasi',exact:true}).isEnabled(),requests};
  await page.screenshot({path:path.join(out,'knowledge.png'),fullPage:true});fs.writeFileSync(path.join(out,'result.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({...result,artifact:out}));
  assert(result.picker_enabled,'File picker disabled on direct knowledge entry');
 }finally{await browser.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
