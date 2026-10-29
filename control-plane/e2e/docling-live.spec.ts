import {test,expect} from '@playwright/test';
import {createHash} from 'node:crypto';
import {mkdirSync,writeFileSync} from 'node:fs';

test.use({channel:'chromium',headless:true,viewport:{width:1360,height:1000},trace:'off',video:'off'});
test('real stored SOP: PDF, extraction, nine chat turns, citations and unchanged approval',async({page,request})=>{
  test.skip(process.env.NUSANTARA_DOCLING_LIVE!=='1','Explicit live run only');
  test.setTimeout(900000);
  page.setDefaultTimeout(20000);
  const origin='http://127.0.0.1:5180';
  const token=process.env.NUSANTARA_ADMIN_TOKEN;
  expect(token,'Configured operator credential').toBeTruthy();
  const id='DOC-SHA256-d9ae50f88383d4162181fca7761aaba122b6a4d77e908d5cae927d5b2ba7454b';
  const base=`${origin}/v1/knowledge/pipeline/reviews/${id}`;
  const headers={'X-Admin-Token':token!};
  const beforeResponse=await request.get(base,{headers});expect(beforeResponse.ok()).toBeTruthy();
  const before=await beforeResponse.json();
  const pdf=await request.get(`${base}/source?version_id=${before.version_id}`,{headers});
  expect(createHash('sha256').update(await pdf.body()).digest('hex')).toBe(before.source_sha256);
  mkdirSync('../artifacts/docling-ui',{recursive:true});
  const runStamp=Date.now();
  const screenshots={extraction:`../artifacts/docling-ui/extraction-${runStamp}.png`,citation:`../artifacts/docling-ui/citation-${runStamp}.png`};
  // Only the local application is allowed; no mocked backend responses.
  await page.route('**/*',route=>{
    const url=new URL(route.request().url());
    return ['127.0.0.1','localhost'].includes(url.hostname)||['blob:','data:','chrome-extension:'].includes(url.protocol)?route.continue():route.abort();
  });
  await page.goto(origin+'/knowledge');
  await page.getByLabel('Token operator',{exact:true}).fill(token!);
  await page.getByRole('button',{name:'Verifikasi akses',exact:true}).click();
  await expect(page.getByText('Akses operator terverifikasi. Anda dapat mengunggah file.')).toBeVisible();
  console.log('PASS UI operator access');
  await page.getByRole('button',{name:'Periksa isi',exact:true}).first().click();
  const panel=page.locator('section[aria-label="Pemeriksaan SOP"]');
  await expect(panel.getByRole('heading',{name:'PERMOHONAN DATA PRIBADI',exact:true})).toBeVisible();
  await expect(panel).toContainText(id);
  console.log('PASS UI selected official SOP');
  await panel.getByText('Perbaikan pembacaan dan detail teknis',{exact:true}).click();
  // Verify the real reprocessing action and poll the actual backend job.
  const reuse=process.env.NUSANTARA_UI_REUSE_EXTRACTION==='1';
  if(!reuse){
    const processing=page.waitForResponse(r=>r.url()===base+'/process'&&r.request().method()==='POST');
    await panel.getByRole('button',{name:'Proses ulang dengan Docling',exact:true}).click();
    expect((await processing).ok()).toBeTruthy();
  }
  await expect.poll(async()=>{const d=await(await request.get(base,{headers})).json();return d.extraction.status;},
                    {timeout:660000,intervals:[3000]}).toBe('COMPLETE');
  await panel.getByRole('button',{name:'Muat ulang pemeriksaan',exact:true}).click();
  await expect(panel.getByText(/Ekstraksi Docling: COMPLETE/)).toBeVisible();
  const converted=await (await request.get(base,{headers})).json();
  if(!reuse)expect(converted.extraction.job_id).not.toBe(before.extraction.job_id);
  console.log('PASS UI extraction COMPLETE');
  await expect(panel.getByRole('table',{name:'Tabel SOP halaman 1',exact:true})).toBeVisible();
  await expect(panel.getByAltText('PDF asli SOP halaman 1',{exact:true})).toBeVisible();
  await expect.poll(()=>panel.getByAltText('PDF asli SOP halaman 1',{exact:true}).evaluate((img:HTMLImageElement)=>img.complete&&img.naturalWidth>0)).toBeTruthy();
  await panel.getByRole('button',{name:'Halaman 2',exact:true}).click();
  await expect(panel.getByRole('table',{name:'Tabel SOP halaman 2',exact:true})).toBeVisible();
  await panel.getByRole('heading',{name:'PERMOHONAN DATA PRIBADI',exact:true}).scrollIntoViewIfNeeded();
  await page.screenshot({path:screenshots.extraction,fullPage:false,timeout:15000});
  console.log('PASS UI source PDF and two tables');
  await panel.getByRole('button',{name:'Coba chat SOP ini',exact:true}).click();
  const cases=[
    ['Apa persyaratannya?','requirements','surat permohonan',[1]],
    ['Bawa apa saja?','requirements','surat permohonan',[1]],
    ['Bagaimana prosesnya?','procedure','menyampaikan',[1,2]],
    ['Berapa lama?','time_cost','3 hari kerja',[2]],
    ['Berapa biayanya?','time_cost','belum tercantum',[1,2]],
    ['Apa hasil layanannya?','procedure','berkas data',[2]],
    ['Lalu bagaimana?','followup','menyampaikan',[1,2]],
    ['Apakah SOP ini menyebutkan nomor WhatsApp petugas?','missing','belum tercantum',[1,2]],
    ['Apa persyaratannya?','requirements','surat permohonan',[1]],
  ] as const;
  const results:unknown[]=[];
  for(const [question,kind,expected,pages] of cases){
    console.log(`Testing UI: ${question}`);
    await expect(panel.getByLabel('Jenis percobaan',{exact:true})).toBeEnabled({timeout:90000});
    await panel.getByLabel('Jenis percobaan',{exact:true}).selectOption(kind);
    await panel.getByLabel('Pertanyaan SOP',{exact:true}).fill(question);
    const pending=page.waitForResponse(r=>r.url()===origin+'/v1/chat'&&r.request().method()==='POST',{timeout:240000});
    await panel.getByRole('button',{name:'Kirim pertanyaan SOP',exact:true}).click();
    const response=await pending;expect(response.ok()).toBeTruthy();
    const answer=await response.json();
    results.push({question,answer});writeFileSync('../artifacts/docling-ui/answers.json',JSON.stringify(results,null,2));
    expect(answer.grounding.grounded,question).toBeTruthy();
    expect(answer.response.toLowerCase()).toContain(expected);
    expect(answer.evidence.every((e:{document_id:string})=>e.document_id===id)).toBeTruthy();
    expect([...new Set(answer.evidence.flatMap((e:{pages:number[]})=>e.pages))].sort()).toEqual([...pages]);
    expect(answer.evidence.every((e:{block_ids?:string[]})=>e.block_ids?.length)).toBeTruthy();
    const trial=panel.locator('article').filter({has:page.getByText(question,{exact:true})}).last();
    await expect(trial).toContainText(answer.response,{timeout:30000});
    await expect(panel.getByLabel('Jenis percobaan',{exact:true})).toBeEnabled({timeout:90000});
    await expect(panel.getByRole('alert')).toHaveCount(0);
    console.log(`PASS live UI: ${question} | ${answer.provider_status} | pages ${pages.join(',')}`);
  }
  await panel.getByRole('button',{name:'Buka halaman 2',exact:true}).last().click();
  await expect(panel.getByAltText('PDF asli SOP halaman 2',{exact:true})).toBeVisible();
  await expect.poll(()=>panel.getByAltText('PDF asli SOP halaman 2',{exact:true}).evaluate((img:HTMLImageElement)=>img.complete&&img.naturalWidth>0)).toBeTruthy();
  await panel.getByAltText('PDF asli SOP halaman 2',{exact:true}).scrollIntoViewIfNeeded();
  await page.screenshot({path:screenshots.citation,fullPage:false,timeout:15000});
  writeFileSync('../artifacts/docling-ui/screenshots.json',JSON.stringify(screenshots,null,2));
  const after=await (await request.get(base,{headers})).json();
  expect(after.extraction.job_id).toBe(converted.extraction.job_id);
  expect(after.content_ok).toBe(before.content_ok);expect(after.approval).toEqual(before.approval);
});

