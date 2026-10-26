import {test,expect} from '@playwright/test';
import {mkdirSync,writeFileSync} from 'node:fs';

test.use({channel:'chromium',headless:true,viewport:{width:1360,height:1000},trace:'off',video:'off'});
test('operator can try an unapproved SOP in the real main chat while approval stays unchanged',async({page,request})=>{
  test.skip(process.env.NUSANTARA_DOCLING_LIVE!=='1','Explicit live run only');
  test.setTimeout(600000);page.setDefaultTimeout(30000);
  const origin='http://127.0.0.1:5180';const token=process.env.NUSANTARA_ADMIN_TOKEN!;
  expect(!!token,'Configured operator credential').toBeTruthy();
  const id='DOC-SHA256-d9ae50f88383d4162181fca7761aaba122b6a4d77e908d5cae927d5b2ba7454b';
  const base=`${origin}/v1/knowledge/pipeline/reviews/${id}`;
  const headers={'X-Admin-Token':token};
  const before=await(await request.get(base,{headers})).json();
  expect(before.extraction.status).toBe('COMPLETE');
  await page.addInitScript(()=>{
    const original=window.fetch.bind(window);
    (window as any).__chatBodies=[];
    window.fetch=async(...args)=>{
      const response=await original(...args);
      if(response.url.endsWith('/v1/chat')){
        response.clone().text().then(text=>(window as any).__chatBodies.push(text));
      }
      return response;
    };
  });
  await page.goto(origin+'/knowledge');
  await page.getByLabel('Token operator',{exact:true}).fill(token);
  await page.getByRole('button',{name:'Verifikasi akses',exact:true}).click();
  await expect(page.getByText('Akses operator terverifikasi. Anda dapat mengunggah file.')).toBeVisible();
  await page.getByRole('button',{name:'Periksa isi',exact:true}).first().click();
  const panel=page.locator('section[aria-label="Pemeriksaan SOP"]');
  await expect(panel).toContainText(id);
  await panel.getByRole('link',{name:'Uji di chat utama',exact:true}).click();
  await expect(page).toHaveURL(origin+'/');
  await expect(page.getByText(/Mode uji operator/)).toBeVisible();
  await expect(page.getByText(/Dokumen aktif: PERMOHONAN DATA PRIBADI/)).toBeVisible();
  const results:unknown[]=[];let session='';
  for(const [question,value,sourcePage] of [['Apa persyaratannya?','surat permohonan',1],['Bawa apa saja?','surat permohonan',1],['Berapa lama?','3 hari kerja',2]] as const){
    await page.getByLabel('Pertanyaan Anda',{exact:true}).fill(question);
    const pending=page.waitForResponse(r=>r.url()===origin+'/v1/chat'&&r.request().method()==='POST',{timeout:270000});
    await page.getByRole('button',{name:'Kirim pertanyaan',exact:true}).click();
    const response=await pending;expect(response.ok()).toBeTruthy();
    const body=response.request().postDataJSON();
    expect(body.document_ids).toEqual([id]);expect(body.sop_version).toBe(before.version_id);
    if(session)expect(body.session_id).toBe(session);session=body.session_id;
    await expect.poll(()=>page.evaluate(()=>(window as any).__chatBodies.length),{timeout:270000}).toBe(results.length+1);
    const captured=await page.evaluate(()=>(window as any).__chatBodies.at(-1) as string);
    const events=captured.trim().split('\n').map(line=>JSON.parse(line));
    const answer=events.find(e=>e.type==='final')?.answer;
    expect(answer,'Grounded final chat event').toBeTruthy();
    expect(answer.grounding.grounded).toBeTruthy();expect(answer.response.toLowerCase()).toContain(value);
    expect(answer.evidence[0].pages).toContain(sourcePage);expect(answer.evidence[0].document_id).toBe(id);
    await expect(page.getByText(answer.response,{exact:true}).first()).toBeVisible();
    results.push({question,answer});console.log(`PASS main chat: ${question} | page ${sourcePage}`);
  }
  const after=await(await request.get(base,{headers})).json();
  expect(after.content_ok).toBe(before.content_ok);expect(after.approval).toEqual(before.approval);
  expect(after.extraction.job_id).toBe(before.extraction.job_id);
  mkdirSync('../artifacts/docling-main-chat',{recursive:true});
  writeFileSync('../artifacts/docling-main-chat/answers.json',JSON.stringify(results,null,2));
  await page.screenshot({path:`../artifacts/docling-main-chat/main-${Date.now()}.png`,timeout:15000});
});
