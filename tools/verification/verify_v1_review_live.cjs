// Read-only verification of the actual UI and backend. Never posts decisions or actions.
const {chromium}=require('../control-plane/node_modules/playwright');
const fs=require('node:fs');const path=require('node:path');const {execFileSync}=require('node:child_process');
(async()=>{
 const root=path.resolve(__dirname,'..'),out=path.join(root,'artifacts/v1-verification');fs.mkdirSync(out,{recursive:true});
 const token=process.env.NUSANTARA_ADMIN_TOKEN||execFileSync(path.join(root,'.venv/Scripts/python.exe'),['-c',"from dotenv import dotenv_values; print(dotenv_values('.env', interpolate=False).get('NUSANTARA_ADMIN_TOKEN') or '')"],{cwd:root,encoding:'utf8'}).trim();
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1050}});
  const failures=[];page.on('pageerror',e=>failures.push(e.message));
  const initial=await page.goto('http://127.0.0.1:5180/verification');
  if(initial.status()!==200)throw Error('UI did not respond');
  const h=page.getByRole('heading',{name:'Verifikasi dan keputusan'});await h.waitFor();
  await page.getByRole('button',{name:'PASS',exact:true}).waitFor();
  if(!await page.getByRole('button',{name:'PASS',exact:true}).isDisabled())throw Error('Anonymous PASS enabled');
  const packageResponse=await page.request.get('http://127.0.0.1:8765/v1/control-plane/evidence-package');
  const pkg=await packageResponse.json();if(!pkg.pass_allowed||pkg.blockers.length)throw Error('Evidence is not valid');
  let contextStatus=null,historyStatus=null,before=null,after=null;
  if(token){
   const headers={'X-Admin-Token':token};
   const context=await page.request.get('http://127.0.0.1:8765/v1/control-plane/execution-context',{headers});contextStatus=context.status();const plan=await context.json();
   const history=await page.request.get('http://127.0.0.1:8765/v1/control-plane/history',{headers});historyStatus=history.status();before=await history.json();
   if(contextStatus!==200||historyStatus!==200)throw Error('Authenticated backend context unavailable');
   await page.getByLabel('Token operator',{exact:true}).fill(token);
   await page.getByText('Operator terautentikasi sebagai pemegang token admin bersama.',{exact:true}).waitFor();
   await page.getByRole('button',{name:'PASS',exact:true}).waitFor();
   const {expect}=require('../control-plane/node_modules/@playwright/test');
   if(plan.completed)await expect(page.getByRole('button',{name:'PASS',exact:true})).toBeDisabled();
   else await expect(page.getByRole('button',{name:'PASS',exact:true})).toBeEnabled();
   const details=page.getByText('Detail teknis pemeriksaan dan evidence',{exact:true});
   const technical=details.locator('..');if(await technical.getAttribute('open')!==null)throw Error('Technical details should start collapsed');
   await page.screenshot({path:path.join(out,'verification-live.png'),fullPage:true});
   after=await (await page.request.get('http://127.0.0.1:8765/v1/control-plane/history',{headers})).json();
   if(JSON.stringify(before)!==JSON.stringify(after))throw Error('Read-only check changed History');
  }
  await page.reload();await h.waitFor();
  const fresh=await (await page.request.get('http://127.0.0.1:5180/v1/control-plane/evidence-package')).json();
  if(fresh.package_id!==pkg.package_id||!fresh.pass_allowed)throw Error('Proxy or reload uses stale evidence');
  if(failures.length)throw Error('Browser page errors: '+failures.join('; '));
  const result={url:page.url(),ui_status:initial.status(),context_status:contextStatus,history_status:historyStatus,package_id:pkg.package_id,
   valid_criteria:pkg.criteria.filter(c=>c.status==='VALID').length,blockers:pkg.blockers,history_unchanged:true,
   human_decision_clicked:false,execution_clicked:false,decision_count:after?.decisions.length??null,reload_validated:true,page_errors:failures};
  fs.writeFileSync(path.join(out,'live-validation.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
 }finally{await browser.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
