import {resolve} from 'node:path';
import {test,expect} from '@playwright/test';
const headers={'X-Admin-Token':'fixture-only-review'};
for(const scenario of ['PASS','FAIL','HOLD','none','expired','different_evidence','changed_source']){
 test(`Review -> governance -> executor -> History: ${scenario}`,async({page,request})=>{
  const backend='http://127.0.0.1:9876';
  expect((await request.post(`${backend}/__fixture/reset`)).ok()).toBeTruthy();
  await page.goto('/verification');
  await page.getByLabel('Token operator',{exact:true}).fill(headers['X-Admin-Token']);
  await expect(page.getByText('Kelayakan: VALID',{exact:true})).toBeVisible();
  const run=page.getByRole('button',{name:'Jalankan tindakan yang disetujui'});
  if(scenario!=='none'){
   const decision=['FAIL','HOLD'].includes(scenario)?scenario:'PASS';
   await expect(page.getByRole('button',{name:decision,exact:true})).toBeEnabled();
   await page.getByRole('button',{name:decision,exact:true}).click();
   await expect(page.getByRole('heading',{name:`Keputusan ${decision}`,exact:true})).toBeVisible();
  }
  if(scenario==='PASS'){
   await expect(run).toBeEnabled();await run.click();
   await expect(page.getByRole('heading',{name:'Eksekusi PASS',exact:true})).toBeVisible();
  }else{
   if(['FAIL','HOLD','none'].includes(scenario))await expect(run).toBeDisabled();
   if(scenario==='expired')expect((await request.post(`${backend}/__fixture/scenario`,{data:{operation:'expire'}})).ok()).toBeTruthy();
   if(scenario==='changed_source')expect((await request.post(`${backend}/__fixture/scenario`,{data:{operation:'change_source'}})).ok()).toBeTruthy();
   const pkg=await (await request.get(`${backend}/v1/control-plane/evidence-package`)).json();
   const history=await (await request.get(`${backend}/v1/control-plane/history`,{headers})).json();
   let packageId=pkg.package_id;
   if(scenario==='changed_source')packageId=history.decisions.at(-1).package_id;
   if(scenario==='different_evidence')packageId='evp_sha256_'+'0'.repeat(64);
   const decisionId=history.decisions.at(-1)?.decision_id??'dec_'+'0'.repeat(32);
   const denied=await request.post(`${backend}/v1/control-plane/execute-reviewed`,{headers,data:{package_id:packageId,decision_id:decisionId}});
   expect(denied.status()).toBe(409);
   await page.getByRole('button',{name:'Muat ulang review'}).click();
   await expect(page.getByRole('heading',{name:'Eksekusi BLOCKED',exact:true})).toBeVisible();
  }
  const result=await (await request.get(`${backend}/__fixture/result`)).json();
  expect(result.value).toBe(scenario==='PASS'?'after':'before');
  await page.reload();await page.getByLabel('Token operator',{exact:true}).fill(headers['X-Admin-Token']);
  await expect(page.getByRole('heading',{name:`Eksekusi ${scenario==='PASS'?'PASS':'BLOCKED'}`,exact:true})).toBeVisible();
  if(scenario==='PASS')await page.screenshot({path:resolve(import.meta.dirname,'../../artifacts/v1-review-e2e/history-pass.png'),fullPage:true});
 });
}
