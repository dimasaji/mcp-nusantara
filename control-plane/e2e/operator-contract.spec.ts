import {test,expect} from '@playwright/test';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';

const output=resolve('../artifacts/ncp-v1-ui');
test('operator navigation, read-only live API and responsive presentation',async({page})=>{
 mkdirSync(output,{recursive:true});
 const responses:{path:string;status:number}[]=[];
 const mutations:string[]=[];
 page.on('response',r=>{if(new URL(r.url()).pathname.startsWith('/v1/'))responses.push({path:new URL(r.url()).pathname,status:r.status()});});
 page.on('request',r=>{if(new URL(r.url()).pathname.startsWith('/v1/')&&r.method()!=='GET')mutations.push(`${r.method()} ${new URL(r.url()).pathname}`);});
 await page.goto('/dashboard');
 const nav=page.getByRole('navigation',{name:'Navigasi operator'});
 await expect(nav.getByRole('link')).toHaveCount(10);
 await expect(page.getByRole('heading',{name:'Apa yang sedang dikerjakan?'})).toBeVisible();
 await expect(page.getByRole('heading',{name:'Apa masalahnya?'})).toBeVisible();
 await expect(page.getByText(/blocker dalam paket evidence ini/)).toBeVisible();
 await page.screenshot({path:resolve(output,'desktop.png'),fullPage:true});
 // Read credentials already provisioned locally; never log, persist or change them.
 let token=process.env.NUSANTARA_ADMIN_TOKEN??'';
 if(!token){try{const line=readFileSync('../.env','utf8').split(/\r?\n/).find(x=>/^NUSANTARA_ADMIN_TOKEN=/.test(x));token=(line?.slice(line.indexOf('=')+1)??'').trim().replace(/^(['"])(.*)\1$/,'$2');}catch{/* Test may run without local credentials. */}}
 await nav.getByRole('link',{name:/Pengaturan Sistem/}).click();
 await expect(page.getByRole('heading',{name:'Pengaturan Sistem'})).toBeVisible();
 if(token)await page.getByLabel('Token operator',{exact:true}).fill(token);
 const destinations=[['Agent Workspace','Agent Workspace'],['Aktivitas Tugas','Aktivitas Tugas'],['Masalah & Blocker','Masalah & Blocker'],['Persetujuan','Persetujuan'],['Biaya & Model','Biaya & Model'],['Knowledge & RAG','Dokumen dan pemantauan'],['Governance & Permissions','Governance & Permissions'],['Detail Teknis R1–R21','Detail Teknis R1–R21']] as const;
 for(const [menu,title] of destinations){
  await nav.getByRole('link',{name:new RegExp(menu.replace('&','&'))}).click();
  await expect(page.getByRole('heading',{name:title,exact:true})).toBeVisible();
  if(menu==='Agent Workspace'){
   await expect(page.getByRole('button',{name:'Kirim tugas'})).toBeDisabled();
   await expect(page.getByText('Hermes belum terhubung',{exact:true}).last()).toBeVisible();
   await page.screenshot({path:resolve(output,'workspace.png'),fullPage:true});
  }
  if(menu==='Detail Teknis R1–R21'){
   await page.getByRole('button',{name:'Tahapan 0–21',exact:true}).click();
   await expect(page.getByRole('heading',{name:'Tahapan 0–21',exact:true})).toBeVisible();
  }
 }
 await nav.getByRole('link',{name:/Beranda Operator/}).click();
 await page.setViewportSize({width:390,height:844});
 await page.screenshot({path:resolve(output,'mobile.png'),fullPage:true});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
 await page.getByRole('navigation',{name:'Navigasi operator'}).getByRole('link',{name:/Masalah & Blocker/}).click();
 await expect(page.getByRole('heading',{name:'Masalah & Blocker',exact:true})).toBeVisible();
 expect(mutations).toEqual([]);
 writeFileSync(resolve(output,'live-api.json'),JSON.stringify({credentialProvided:!!token,responses,mutations},null,2));
});
