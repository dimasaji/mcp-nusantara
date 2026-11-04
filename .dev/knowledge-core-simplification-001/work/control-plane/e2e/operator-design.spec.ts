import {test,expect} from '@playwright/test';
import {writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const output=resolve('../artifacts/ncp-v1-ui-local-20261019');
test('live four-menu dashboard, drawers, access boundaries and responsive layouts',async({page})=>{
 const responses:{path:string;status:number}[]=[];
 const mutations:string[]=[];
 const errors:string[]=[];
 page.on('response',r=>{const path=new URL(r.url()).pathname;if(path.startsWith('/v1/')||path==='/health')responses.push({path,status:r.status()});});
 page.on('request',r=>{const path=new URL(r.url()).pathname;if((path.startsWith('/v1/')||path==='/health')&&r.method()!=='GET')mutations.push(`${r.method()} ${path}`);});
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/dashboard');
 const authHeaders:Record<string,string>[]=[{},{'X-Admin-Token':'invalid-ui-test-only'}];
 for(const headers of authHeaders){
  const response=await page.request.get('/v1/control-plane/history',{headers});
  expect(response.status()).toBe(403);
 }
 await expect(page.getByRole('heading',{name:'Apa yang sedang dikerjakan?'})).toBeVisible();
 await expect(page.getByText('Mode aktual · API lokal')).toBeVisible();
 await expect(page.getByRole('navigation',{name:'Navigasi operator'}).getByRole('link')).toHaveCount(4);
 await expect(page.getByRole('button',{name:'Detail health ↗'})).toBeVisible();
 await expect(page.getByText(/HTTP 200/).first()).toBeVisible();
 await page.getByRole('button',{name:'Detail health ↗'}).click();
 await expect(page.getByRole('dialog',{name:'Detail health'})).toBeVisible();
 await page.keyboard.press('Escape');
 await expect(page.getByRole('dialog')).not.toBeVisible();
 await expect(page.getByRole('button',{name:'Detail health ↗'})).toBeFocused();
 await page.evaluate(()=>window.scrollTo(0,0));
 await page.screenshot({path:resolve(output,'desktop-dashboard.png'),fullPage:true});
 for(const [path,title] of [['/workspace','AI Workspace'],['/approvals','Human Control'],['/settings','Pengaturan & Teknis']] as const){
  await page.getByRole('navigation',{name:'Navigasi operator'}).getByRole('link',{name:title,exact:false}).click();
  await expect(page.getByRole('heading',{name:title,exact:true})).toBeVisible();
  if(path==='/workspace'){
   await page.getByRole('tab',{name:'Chat V1'}).click();
   await expect(page.getByLabel('Pertanyaan Anda')).toBeVisible();
  }
  await page.screenshot({path:resolve(output,`desktop-${path.slice(1)}.png`),fullPage:true});
 }
 await page.goto('/blockers');
 const blocker=page.getByRole('button',{name:/Detail blocker/}).first();
 if(await blocker.count()){
  await blocker.click();await expect(page.getByRole('dialog')).toBeVisible();
  await expect(page.getByRole('dialog').getByText(/Task\/request ID/)).toBeVisible();
  await page.screenshot({path:resolve(output,'blocker-drawer.png')});
  await page.keyboard.press('Escape');
 }
 for(const width of [390,768]){
  await page.setViewportSize({width,height:844});
  for(const [path,title] of [['/dashboard','Beranda'],['/workspace','AI Workspace'],['/approvals','Human Control'],['/settings','Pengaturan & Teknis']] as const){
   await page.goto(path);await expect(page.getByRole('heading',{name:title,exact:true})).toBeVisible();
   if(path==='/dashboard')await expect(page.getByText(/blocker dalam paket evidence ini/)).toBeVisible();
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${path} at ${width}px`).toBe(true);
   await page.screenshot({path:resolve(output,`${width}-${path.slice(1)}.png`),fullPage:true});
  }
 }
 expect(mutations).toEqual([]);expect(errors).toEqual([]);
 writeFileSync(resolve(output,'browser-api-summary.json'),JSON.stringify({url:'http://127.0.0.1:5180',responses,mutations,errors,scope:'Live read-only; no credentials, inference or production mutations'},null,2));
});
