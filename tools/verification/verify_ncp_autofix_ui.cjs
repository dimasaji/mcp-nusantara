const {chromium}=require('../control-plane/node_modules/playwright');
const fs=require('node:fs');const path=require('node:path');
(async()=>{
 const origin=process.env.NCP_UI_ORIGIN||'http://127.0.0.1:5180';
 const out=path.resolve(process.env.NCP_EVIDENCE_DIR||'artifacts/NCP-V1-AUTOFIX-HUMAN-001/20261019-104353/browser-baseline');
 fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const report={scope:'ACTUAL_UI_READ_ONLY',origin,pages:[],errors:[],failedRequests:[]};
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  page.on('pageerror',e=>report.errors.push(e.message));
  page.on('response',r=>{if(r.url().startsWith(origin+'/v1/')&&r.status()>=400)report.failedRequests.push({path:new URL(r.url()).pathname,status:r.status()});});
  for(const route of ['/dashboard','/workspace','/approvals','/settings','/technical']){
   const response=await page.goto(origin+route);await page.locator('h1').first().waitFor();
   await page.waitForLoadState('networkidle');
   const details=await page.evaluate(()=>({
    headings:[...document.querySelectorAll('h1,h2')].map(e=>e.textContent.trim()),
    buttons:[...document.querySelectorAll('button')].map(e=>({text:e.textContent.trim(),disabled:e.disabled})),
    links:[...document.querySelectorAll('main a')].map(e=>({text:e.textContent.trim(),href:e.getAttribute('href')})),
    alerts:[...document.querySelectorAll('[role=alert]')].map(e=>e.textContent.trim()),
    overflow:document.documentElement.scrollWidth>window.innerWidth
   }));
   report.pages.push({route,http:response.status(),...details});
   await page.screenshot({path:path.join(out,route.slice(1)+'.png'),fullPage:true});
  }
  await page.goto(origin+'/workspace');
  await page.getByRole('link',{name:'Buka Chat AI V1',exact:true}).click();
  await page.getByRole('heading',{name:'Asisten Anda',exact:true}).waitFor();
  report.chatNavigation={from:'/workspace',to:new URL(page.url()).pathname,status:new URL(page.url()).pathname==='/ui'?'PASS':'FAIL'};
  fs.writeFileSync(path.join(out,'ui.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({artifact:out,pages:report.pages.map(p=>({route:p.route,http:p.http,headings:p.headings,disabled:p.buttons.filter(b=>b.disabled).map(b=>b.text),alerts:p.alerts,overflow:p.overflow})),errors:report.errors,failedRequests:report.failedRequests}));
  if(report.errors.length||report.chatNavigation.status!=='PASS'||report.pages.some(p=>p.http!==200||p.overflow))process.exitCode=1;
 }finally{await browser.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
