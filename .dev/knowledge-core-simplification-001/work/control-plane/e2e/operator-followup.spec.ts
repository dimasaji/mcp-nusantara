import {test,expect,type Page} from '@playwright/test';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const output=resolve('../artifacts/ncp-v1-ui-followup-20261019');
const reference=resolve('../artifacts/ncp-v1-ui-local-20261019/reference/dist');
async function serveReference(page:Page){
 await page.route('**/__reference__/**',async route=>{
  const name=new URL(route.request().url()).pathname.split('/').at(-1)||'index.html';
  if(!['index.html','app.js','core.js','styles.css'].includes(name))return route.abort();
  await route.fulfill({body:readFileSync(resolve(reference,name)),contentType:name.endsWith('.js')?'text/javascript':name.endsWith('.css')?'text/css':'text/html'});
 });
}
test('same viewport reference and local comparison',async({page})=>{
 await serveReference(page);
 const report:unknown[]=[];
 for(const width of [1440,390]){
  await page.setViewportSize({width,height:width===1440?1000:844});
  for(const [ref,local] of [['workspace','workspace'],['human','approvals']]){
   await page.goto(`/__reference__/index.html#${ref}`);
   await expect(page.getByRole('heading',{name:ref==='workspace'?'AI Workspace':'Human Control',exact:true})).toBeVisible();
   const tabs=ref==='workspace'?['Aktivitas tugas','Blocker','Evidence']:[];
   await page.screenshot({path:resolve(output,`reference-${ref}-${width}.png`),fullPage:true});
   for(const tab of tabs){
    await page.locator('[data-action="workspace-tab"]').filter({hasText:tab}).first().click();
    await page.screenshot({path:resolve(output,`reference-${ref}-${tab.split(' ')[0]}-${width}.png`),fullPage:true});
   }
   report.push({surface:'reference',page:ref,width,tabs});
   await page.goto(`/${local}`);
   await expect(page.getByRole('heading',{name:ref==='workspace'?'AI Workspace':'Human Control',exact:true})).toBeVisible();
   await expect(page.locator(ref==='workspace'?'.op-task-meta':'.op-human .op-specs').first()).toContainText(/ollama|openrouter/i);
   await page.screenshot({path:resolve(output,`${process.env.NCP_CAPTURE_STAGE??'after'}-${local}-${width}.png`),fullPage:true});
  }
 }
 writeFileSync(resolve(output,'comparison-viewports.json'),JSON.stringify(report,null,2));
});

test('reference tabs, filters, task/blocker/evidence/gate and decision drawers',async({page})=>{
 test.setTimeout(90000);
 await page.emulateMedia({reducedMotion:'reduce'});
 await serveReference(page);
 const inspected:string[]=[];
 for(const width of [1440,390]){
  await page.setViewportSize({width,height:width===1440?1000:844});
  await page.goto('/__reference__/index.html#workspace');
  await page.locator('[data-action="workspace-tab"][data-id="tasks"]').click();
  await page.getByRole('button',{name:'Buka detail tugas',exact:true}).click();
  await expect(page.getByRole('dialog')).toBeVisible();inspected.push(`task drawer ${width}`);
  await page.screenshot({path:resolve(output,`reference-task-drawer-${width}.png`)});await page.keyboard.press('Escape');
  await page.locator('[data-action="workspace-tab"][data-id="blockers"]').click();
  for(const id of ['open','resolved','all']){await page.locator(`[data-action="blocker-filter"][data-id="${id}"]`).click();inspected.push(`blocker filter ${id} ${width}`);}
  const blockers=await page.locator('main .blocker-list [data-action="blocker"]').count();
  for(let i=0;i<blockers;i++){
   await page.locator('main .blocker-list [data-action="blocker"]').nth(i).click();await expect(page.getByRole('dialog')).toBeVisible();
   await page.screenshot({path:resolve(output,`reference-blocker-${i}-${width}.png`)});await page.keyboard.press('Escape');
  }
  await page.locator('[data-action="workspace-tab"][data-id="evidence"]').click();
  for(const filter of ['PASS','FAIL','HOLD','ALL']){await page.locator(`[data-action="evidence-filter"][data-id="${filter}"]`).click();inspected.push(`evidence filter ${filter} ${width}`);}
  await page.locator('tbody [data-action="evidence"]').first().click();await expect(page.getByRole('dialog')).toBeVisible();
  await page.screenshot({path:resolve(output,`reference-evidence-drawer-${width}.png`)});await page.keyboard.press('Escape');
  await page.goto('/__reference__/index.html#human');
  const gates=page.locator('.gate-item');
  for(let i=0;i<await gates.count();i++){
   await gates.nth(i).click();await expect(page.getByRole('dialog')).toBeVisible();inspected.push(`gate ${i+1} ${width}`);
   await page.screenshot({path:resolve(output,`reference-gate-${i+1}-${width}.png`)});await page.keyboard.press('Escape');
  }
  await page.getByRole('button',{name:'Tinjau & beri keputusan',exact:true}).click();
  await expect(page.locator('[data-action="select-decision"][data-id="PASS"]')).toBeDisabled();
  for(const choice of ['FAIL','HOLD']){const button=page.locator(`[data-action="select-decision"][data-id="${choice}"]`);await button.click();await expect(button).toHaveAttribute('aria-pressed','true');}
  await page.screenshot({path:resolve(output,`reference-decision-drawer-${width}.png`)});await page.keyboard.press('Escape');
  await page.getByRole('button',{name:'Lihat kebijakan',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Pengaturan & Teknis',exact:true})).toBeVisible();inspected.push(`policy link ${width}`);
 }
 writeFileSync(resolve(output,'reference-interaction-checklist.json'),JSON.stringify(inspected,null,2));
});

test('live workspace and human controls remain read only while browsing',async({page})=>{
 const mutations:string[]=[],errors:string[]=[];
 page.on('request',r=>{if(new URL(r.url()).pathname.startsWith('/v1/')&&r.method()!=='GET')mutations.push(`${r.method()} ${new URL(r.url()).pathname}`);});
 page.on('pageerror',e=>errors.push(e.message));
 for(const width of [1440,390]){
  await page.setViewportSize({width,height:width===1440?1000:844});await page.goto('/workspace');
  await page.getByRole('button',{name:'Fokus PIAK-03 ↗'}).click();await expect(page.getByRole('dialog')).toBeVisible();await page.keyboard.press('Escape');
  await page.getByRole('tab',{name:'Aktivitas tugas'}).focus();await page.keyboard.press('ArrowRight');await expect(page.getByRole('tab',{name:/Blocker/})).toHaveAttribute('aria-selected','true');
  for(const tab of ['Aktivitas tugas','Blocker','Evidence','Chat V1']){
   await page.getByRole('tab',{name:new RegExp(`^${tab}`)}).click();
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
   if(tab==='Blocker'){
    await page.getByRole('button',{name:'Selesai',exact:true}).click();await expect(page.getByText(/Riwayat penyelesaian blocker/)).toBeVisible();
    await page.getByRole('button',{name:'Terbuka',exact:true}).click();
    await page.getByRole('button',{name:/^Detail blocker/}).first().click();await expect(page.getByRole('dialog')).toBeVisible();
    await page.screenshot({path:resolve(output,`live-blocker-drawer-${width}.png`)});await page.keyboard.press('Escape');
   }
   if(tab==='Evidence'){
    await expect(page.locator('.op-evidence tbody tr').first()).toBeVisible();
    await page.locator('.op-evidence tbody .detail-trigger').first().click();await expect(page.getByRole('dialog')).toBeVisible();
    await page.screenshot({path:resolve(output,`live-evidence-drawer-${width}.png`)});await page.keyboard.press('Escape');
   }
   if(tab==='Chat V1')await expect(page.getByLabel('Pertanyaan Anda')).toBeVisible();
   await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:resolve(output,`live-workspace-${tab.split(' ')[0]}-${width}.png`),fullPage:true});
  }
  await page.goto('/approvals');
  for(const name of ['Evidence valid','Plan siap','Operator terautentikasi','Keputusan tersedia','Izin eksekusi']){
   await page.getByRole('button',{name:`${name} ↗`,exact:true}).click();await expect(page.getByRole('dialog')).toBeVisible();
   await page.keyboard.press('Escape');
  }
  await page.getByRole('button',{name:'Tinjau & beri keputusan',exact:true}).click();const drawer=page.getByRole('dialog',{name:'Tinjau keputusan Anda'});
  for(const name of ['PASS','FAIL','HOLD'])await expect(drawer.getByRole('button',{name:new RegExp(name)})).toBeDisabled();
  await expect(drawer.getByRole('button',{name:'Simpan keputusan'})).toBeDisabled();
  await page.screenshot({path:resolve(output,`live-decision-locked-${width}.png`)});await page.keyboard.press('Escape');
  await expect(page.getByRole('button',{name:'Tinjau & beri keputusan',exact:true})).toBeFocused();
  await page.getByRole('button',{name:'Lihat kebijakan ↗'}).click();await expect(page.getByRole('dialog')).toBeVisible();await page.keyboard.press('Escape');
  await page.getByRole('button',{name:'Periksa evidence',exact:true}).click();await expect(page.getByRole('dialog',{name:'Paket evidence'})).toBeVisible();await page.keyboard.press('Escape');
  for(const name of ['Keputusan','Eksekusi','Semua'])await page.getByRole('group',{name:'Filter riwayat'}).getByRole('button',{name,exact:true}).click();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 }
 expect(mutations).toEqual([]);expect(errors).toEqual([]);
 writeFileSync(resolve(output,'live-readonly-checks.json'),JSON.stringify({mutations,errors,viewport:[1440,390]},null,2));
});

for(const width of [1440,390])test(`isolated browser contract at ${width}: tasks, filters, decisions, history, rejection and lost authorization`,async({page})=>{
 await page.setViewportSize({width,height:width===1440?1000:844});
 const packageId='evp_sha256_'+'b'.repeat(64),binding={plan_id:'isolated-plan',version:'isolated-v1',action:'CONTROLLED_FILE_WRITE'};
 const plan={change_id:'isolated-plan',objective:'Tugas PIAK-03 — fixture terisolasi',expected_change:'Contoh pengujian UI, bukan tugas produksi',target_files:['fixture.txt'],operation:'write',plan_binding:binding,risk:'LOW',tests_required:['test_fixture'],rollback:'restore fixture',checked_at:'2026-10-19T10:00:00Z',source:'BROWSER_TEST_ONLY'};
 let allowed=true,authorized=true,reject=false;
 const decisions:Record<string,unknown>[]=[],posts:Record<string,unknown>[]=[];
 await page.route('**/v1/control-plane/**',async route=>{
  const request=route.request(),path=new URL(request.url()).pathname;
  let body:unknown;
  if(path.endsWith('/model-status'))body={model:'fixture-local',provider:'ollama',revision:2,process_id:1,consistency_scope:'CURRENT_PROCESS_ONLY',availability:'NOT_VERIFIED',status:'NOT_VERIFIED',selection_enabled:false,selection_source:'TEST_ONLY',last_request:null};
  else if(path.endsWith('/evidence-package'))body={package_id:packageId,generated_at:'2026-10-19T10:00:00Z',read_scope:'BROWSER_TEST_ONLY',runtime_status:'NOT_VERIFIED',pass_allowed:allowed,blockers:allowed?[]:[{id:'AC1',reason:'ARTIFACT_INVALID'}],criteria:Array.from({length:15},(_,i)=>({id:`AC${i+1}`,summary:`Prasyarat uji ${i+1}`,status:allowed?'VALID':'INVALID',evidence:['proof'],tests:['test_fixture'],reason:null})),evidence:[{id:'proof',path:'test-only/proof.json',classification:'CURRENT_OFFLINE',validation_status:'VALID',sha256:null,bytes:4,reason:null},{id:'missing',path:'test-only/missing.json',classification:'CURRENT_OFFLINE',validation_status:'MISSING',sha256:null,bytes:null,reason:'ARTIFACT_INVALID'}]};
  else if(!authorized)return route.fulfill({status:403,json:{detail:'FORBIDDEN'}});
  else if(path.endsWith('/history'))body={decisions,executions:[{timestamp:plan.checked_at,change_id:'previous-fixture',package_id:packageId,decision_id:null,result:'BLOCKED',files_changed:[],reason:'TEST_ONLY_BLOCKED'}],decision_audit:'VALIDATED_HASH_CHAIN',execution_audit:'BROWSER_TEST_ONLY'};
  else if(path.endsWith('/execution-context'))body=plan;
  else if(path.endsWith('/operations-summary'))body={scope:'BROWSER_TEST_ONLY',source:'fixture',pending_work:1,pending_review:1,reason:null,checked_at:plan.checked_at,tasks:[{id:plan.change_id,objective:plan.objective,status:'HOLD',updated_at:plan.checked_at,source:'BROWSER_TEST_ONLY'}]};
  else if(path.endsWith('/decisions')&&request.method()==='POST'){
   const submitted=request.postDataJSON();posts.push(submitted);
   if(reject)return route.fulfill({status:409,json:{detail:'EVIDENCE_PACKAGE_CHANGED'}});
   const record={package_id:packageId,decision:submitted.decision,decision_id:'dec_'+String(posts.length).padStart(32,'0'),notes:submitted.notes,plan_binding:binding,reviewer_principal:'ISOLATED_BROWSER_TEST',authentication:'TEST_ONLY',timestamp:new Date().toISOString(),test_evidence:['proof'],blockers:[],record_hash:'c'.repeat(64)};
   decisions.push(record);body=record;
  }else return route.abort();
  await route.fulfill({json:body});
 });
 await page.goto('/approvals');await page.getByRole('button',{name:'Akses operator ↗'}).click();
 await page.getByLabel('Token operator',{exact:true}).fill('isolated-browser-test');
 await expect(page.getByRole('dialog',{name:'Akses operator'}).getByText('Operator terautentikasi sebagai pemegang token admin bersama.')).toBeVisible();await page.keyboard.press('Escape');
 await page.getByRole('navigation',{name:'Navigasi operator'}).getByRole('link',{name:/AI Workspace/}).click();
 await expect(page.getByText(plan.objective).first()).toBeVisible();
 await page.getByRole('button',{name:'Buka detail tugas ↗'}).click();await expect(page.getByRole('dialog')).toContainText('fixture.txt');await page.keyboard.press('Escape');
 await page.getByRole('searchbox',{name:'Cari tugas yang dimuat'}).fill('tidak-cocok');await expect(page.getByText('Tidak ada tugas yang cocok dalam cakupan yang dibaca.')).toBeVisible();
 await page.getByRole('searchbox').fill('');await page.getByRole('button',{name:'Tugas isolated-plan ↗'}).click();await expect(page.getByRole('dialog')).toContainText('BROWSER_TEST_ONLY');await page.keyboard.press('Escape');
 await page.getByRole('tab',{name:/Evidence/}).click();await page.getByRole('group',{name:'Filter evidence'}).getByRole('button',{name:'MISSING',exact:true}).click();await expect(page.locator('tbody tr')).toHaveCount(1);
 await page.screenshot({path:resolve(output,`fixture-evidence-filter-${width}.png`),fullPage:true});
 const downloading=page.waitForEvent('download');await page.getByRole('button',{name:'Ekspor JSON'}).click();const download=await downloading;
 const downloaded=JSON.parse(readFileSync((await download.path())!,'utf8'));expect(downloaded.package.package_id).toBe(packageId);expect(downloaded.package.evidence).toHaveLength(2);
 await page.getByRole('navigation',{name:'Navigasi operator'}).getByRole('link',{name:/Human Control/}).click();
 for(const choice of ['PASS','FAIL','HOLD']){
  const prior=posts.length;await page.getByRole('button',{name:'Tinjau & beri keputusan',exact:true}).click();
  const dialog=page.getByRole('dialog',{name:'Tinjau keputusan Anda'});await dialog.getByRole('button',{name:new RegExp(choice)}).click();
  if(choice==='PASS'){await dialog.getByRole('button',{name:'Periksa evidence sebelum memutuskan'}).click();await expect(page.getByRole('dialog',{name:'Paket evidence'})).toBeVisible();await page.keyboard.press('Escape');await expect(dialog).toBeVisible();}
  expect(posts.length).toBe(prior);await dialog.getByLabel('Alasan keputusan (opsional)').fill(`Keputusan ${choice} dalam fixture`);
  await page.screenshot({path:resolve(output,`fixture-decision-${choice}-${width}.png`)});
  await dialog.getByRole('button',{name:'Simpan keputusan'}).click();await expect(dialog).not.toBeVisible();
  await expect(page.getByRole('region',{name:'History'}).getByRole('cell',{name:new RegExp(`Keputusan ${choice} dalam fixture`)})).toBeVisible();
 }
 for(const filter of ['Keputusan','Eksekusi','Semua'])await page.getByRole('group',{name:'Filter riwayat'}).getByRole('button',{name:filter,exact:true}).click();
 await page.getByRole('button',{name:/^Keputusan dec_/}).first().click();await expect(page.getByRole('dialog')).toContainText('ISOLATED_BROWSER_TEST');await page.keyboard.press('Escape');
 await page.getByRole('button',{name:'Eksekusi previous-fixture 1 ↗'}).click();await expect(page.getByRole('dialog')).toContainText('TEST_ONLY_BLOCKED');await page.keyboard.press('Escape');
 await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:resolve(output,`fixture-human-history-${width}.png`),fullPage:true});
 allowed=false;reject=true;await page.getByRole('button',{name:'Muat ulang review',exact:true}).click();
 await page.getByRole('button',{name:'Tinjau & beri keputusan',exact:true}).click();let dialog=page.getByRole('dialog',{name:'Tinjau keputusan Anda'});
 await expect(dialog.getByRole('button',{name:/PASS/})).toBeDisabled();await dialog.getByRole('button',{name:/HOLD/}).click();await dialog.getByRole('button',{name:'Simpan keputusan'}).click();
 await expect(dialog.getByRole('status')).toContainText('evidence package changed');await expect(dialog).toBeVisible();await page.keyboard.press('Escape');
 authorized=false;await page.getByRole('button',{name:'Akses operator ↗'}).click();await page.getByLabel('Token operator',{exact:true}).fill('invalid-browser-test');await page.keyboard.press('Escape');
 await page.getByRole('button',{name:'Tinjau & beri keputusan',exact:true}).click();dialog=page.getByRole('dialog',{name:'Tinjau keputusan Anda'});
 await expect(dialog.getByRole('button',{name:/HOLD/})).toBeDisabled();await expect(dialog.getByRole('button',{name:'Simpan keputusan'})).toBeDisabled();
 expect(posts).toHaveLength(4);expect(posts.every(p=>(p.plan_binding as typeof binding).version===binding.version)).toBe(true);
 writeFileSync(resolve(output,`isolated-browser-contract-${width}.json`),JSON.stringify({scope:'MOCK_API_ONLY; production mutations intercepted',decisions:posts.map(p=>p.decision),binding,unauthorizedBlocked:true,exportPackageVerified:true},null,2));
});
