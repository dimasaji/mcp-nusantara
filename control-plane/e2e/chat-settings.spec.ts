import {test,expect} from '@playwright/test';

// UI contract only: every backend request is intercepted. This is not live LLM evidence.
for(const width of [1280,390,320]){
  test(`chat first and Control Plane inside Settings at ${width}px`,async({page})=>{
    await page.setViewportSize({width,height:900});
    const calls:{path:string;method:string}[]=[];
    await page.route('**/v1/**',async route=>{
      const request=route.request();const path=new URL(request.url()).pathname;
      calls.push({path,method:request.method()});
      if(path==='/v1/control-plane/model-status')return route.fulfill({json:{
        model:'fixture-local',provider:'ollama',revision:0,process_id:42,
        consistency_scope:'CURRENT_PROCESS_ONLY',availability:'NOT_VERIFIED',status:'NOT_VERIFIED',
        selection_enabled:true,selection_source:'BOOTSTRAP',last_request:null,
      }});
      if(path==='/v1/chat/history')return route.fulfill({json:{session_id:request.headers()['x-chat-session']??'fixture',turns:[]}});
      if(path==='/v1/chat'){
        const input=request.postDataJSON();
        return route.fulfill({json:{session_id:input.session_id,response:'Jawaban fixture untuk menguji tampilan.',model:'fixture-local',
          provider_status:'ollama',latency_ms:1,timestamp:'2026-10-22T00:00:00Z',
          trust:{supports_claim:false,confidence:0,risk_level:'low',requires_human:false,evidence_count:0,evidence_available:false},
          grounding:{enabled:false,grounded:true,reason:'UI fixture'},understanding:{intent:'general'},problem:{goal:null},evidence:[],
        }});
      }
      if(path==='/v1/control-plane/evidence-package')return route.fulfill({json:{
        package_id:'evp_sha256_'+'a'.repeat(64),generated_at:'2026-10-22T00:00:00Z',read_scope:'FIXTURE_ONLY',
        runtime_status:'NOT_VERIFIED',pass_allowed:false,evidence:[],criteria:[],blockers:[],
      }});
      return route.fulfill({status:503,json:{detail:'UI fixture: unavailable'}});
    });
    await page.route('**/health',route=>route.fulfill({json:{status:'ok',service:'ui-fixture',version:'fixture'}}));
    await page.goto('/');
    await expect(page.getByRole('heading',{name:'Asisten Anda'})).toBeVisible();
    await expect(page.getByRole('heading',{name:'Riwayat percakapan'})).toBeVisible();
    await expect(page.getByRole('navigation',{name:'Control Plane',exact:true})).toHaveCount(0);
    await expect(page.getByRole('link',{name:'Buka Control Panel'})).toHaveCount(0);
    await expect(page.getByRole('link',{name:'Pengaturan',exact:true})).toBeVisible();
    await expect(page.getByLabel('Sesi pada perangkat ini')).toBeVisible();
    const controlsOverlap=await page.locator('aside').evaluate(sidebar=>{
      const bounds=Array.from(sidebar.querySelectorAll('.app-brand,button,select,.settings-entry')).map(element=>element.getBoundingClientRect());
      return bounds.some((a,index)=>bounds.slice(index+1).some(b=>
        Math.min(a.right,b.right)>Math.max(a.left,b.left)+1&&Math.min(a.bottom,b.bottom)>Math.max(a.top,b.top)+1));
    });
    expect(controlsOverlap).toBe(false);
    expect(calls.every(call=>['/v1/chat/history','/v1/control-plane/model-status'].includes(call.path))).toBe(true);
    await page.getByLabel('Pertanyaan Anda').fill('Pertanyaan fixture');
    await page.getByRole('button',{name:'Kirim pertanyaan'}).click();
    await expect(page.getByText('Jawaban fixture untuk menguji tampilan.')).toBeVisible();
    await expect(page.getByText('Model yang menjawab: fixture-local')).not.toBeVisible();
    await page.getByText('Detail jawaban',{exact:true}).click();
    await expect(page.getByText('Model yang menjawab: fixture-local')).toBeVisible();
    const currentSession=await page.evaluate(()=>sessionStorage.getItem('nusantara-chat-session'));
    await page.getByRole('button',{name:'+ New Chat'}).click();
    expect(await page.evaluate(()=>sessionStorage.getItem('nusantara-chat-session'))).not.toBe(currentSession);
    await expect(page.getByText('Jawaban fixture untuk menguji tampilan.')).toHaveCount(0);
    await page.getByRole('link',{name:'Pengaturan',exact:true}).click();
    await expect(page.getByRole('heading',{name:'Pengaturan',exact:true})).toBeVisible();
    await page.getByRole('navigation',{name:'Pengaturan NUSANTARA'}).getByRole('link',{name:/Control Plane/}).click();
    await expect(page.getByRole('heading',{name:'Beranda',exact:true})).toBeVisible();
    await expect(page.getByRole('navigation',{name:'Control Plane',exact:true})).toBeVisible();
    await expect(page.locator('aside').getByRole('link',{name:'Pengaturan',exact:true})).toHaveAttribute('aria-current','page');
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
    await page.getByRole('link',{name:'Kembali ke chat',exact:true}).click();
    await expect(page.getByRole('heading',{name:'Asisten Anda'})).toBeVisible();
    expect(calls.filter(call=>call.method!=='GET')).toEqual([{path:'/v1/chat',method:'POST'}]);
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  });
}
