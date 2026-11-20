const {chromium}=require('../control-plane/node_modules/playwright');
const fs=require('node:fs');const path=require('node:path');
(async()=>{
 const out=path.resolve('artifacts/nusantara-e2e-20261016-1018/live-'+Date.now());fs.mkdirSync(out,{recursive:true});
 const frontend=process.env.V1_TEST_FRONTEND||'http://127.0.0.1:5180';const backend=process.env.V1_TEST_BACKEND||'http://127.0.0.1:8000';
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const report={scope:process.env.V1_TEST_FRONTEND?'ISOLATED_APPLICATION_READ_ONLY':'ACTIVE_APPLICATION_READ_ONLY',urls:[frontend,backend],checks:[],errors:[]};
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  page.on('pageerror',e=>report.errors.push(e.message));
  for(const route of ['/dashboard','/workspace','/tasks','/blockers','/approvals','/costs','/knowledge','/settings','/technical','/ui']){
   const response=await page.goto(frontend+route);await page.locator('h1').first().waitFor();
   report.checks.push({route,status:response.status(),title:await page.locator('h1').first().innerText()});
   if(['/dashboard','/knowledge','/ui'].includes(route))await page.screenshot({path:path.join(out,route.slice(1)+'-desktop.png'),fullPage:true});
  }
  await page.setViewportSize({width:390,height:844});
  for(const route of ['/dashboard','/knowledge','/ui']){
   await page.goto(frontend+route);await page.locator('h1').first().waitFor();
   const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth);
   report.checks.push({route,viewport:390,overflow});await page.screenshot({path:path.join(out,route.slice(1)+'-mobile.png'),fullPage:true});
  }
  for(const endpoint of ['/health','/v1/control-plane/model-status','/v1/control-plane/cost-summary','/v1/knowledge/pipeline/status']){
   const r=await page.request.get(backend+endpoint);
   report.checks.push({endpoint,http:r.status(),body:await r.json().catch(()=>null)});
  }
  fs.writeFileSync(path.join(out,'checks.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({artifact:out,errors:report.errors,checks:report.checks.length}));
  if(report.errors.length||report.checks.some(c=>c.overflow))process.exitCode=1;
 }finally{await browser.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
