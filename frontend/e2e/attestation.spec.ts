import {test as base, expect, type Page} from '@playwright/test';
import {build} from 'esbuild';
import path from 'node:path';

// A virtual origin fulfilled entirely through Playwright; no test web server.
const origin = 'http://attestation-e2e.invalid';
if(process.env.CPLANE_ATTESTATION_E2E !== 'MOCK_ONLY' || process.env.CPLANE_E2E_LIVE)
  throw new Error('MOCK_ONLY_MODE_REQUIRED');
const scope = 'R2-A8:ATTESTATION:ONE_GENERATION';
const snapshot = () => ({projection_contract:'ATTESTATION_FOUNDATION_V1', evidence_id:'r2-a9-auth-process',
  evidence_type:'SCOPED_IN_PROCESS', source:'SYNTHETIC BROWSER TEST — NOT LIVE EVIDENCE', scope,
  created_at:'2026-10-08T00:00:00Z', status:'NOT_VERIFIED', evidence_version:'a'.repeat(64),
  live_actions:'LOCKED', operator_policy:'NOT_PROVISIONED', binding:{scope,target:'127.0.0.1:8000',
    pid:123,process_start:134000000000000000,runtime_instance:'synthetic-instance',source_snapshot:'synthetic-source',
    scoped_loaded_code:'synthetic-code',configuration_digest:'b'.repeat(64),
    endpoint:{origin:'http://127.0.0.1:11434',connection_origin:'http://127.0.0.1:11434'},profile:'ATTESTATION',
    active_process_build:'NOT_DIRECTLY_VERIFIED',runtime_identity:'NOT_VERIFIED'},reviews:[],provider_receipt:null});
type Mock = {snapshot:unknown; snapshotStatus:number; intention:unknown; intentionStatus:number;
  posts:unknown[]; blocked:string[]; expectedBlocked:string[]; requests:string[]; errors:string[]; console:string[]; expectedConsole:string[]};
let assets:Awaited<ReturnType<typeof build>>;
const test = base.extend<{mock:Mock}>({
  mock:async ({context,page},use,testInfo) => {
    const launch = testInfo.project.use.launchOptions;
    if(process.env.CPLANE_ATTESTATION_E2E !== 'MOCK_ONLY' || testInfo.config.webServer ||
      testInfo.project.use.baseURL !== origin || testInfo.project.use.serviceWorkers !== 'block' ||
      launch?.proxy?.server !== 'http://127.0.0.1:9' || launch.proxy.bypass !== '<-loopback>' ||
      !launch.args?.includes('--host-resolver-rules=MAP * ~NOTFOUND')) throw new Error('UNSAFE_TEST_CONFIGURATION');
    assets ??= await build({absWorkingDir:path.resolve(testInfo.config.rootDir,'..'),
      entryPoints:['src/main.tsx'],bundle:true,write:false,outdir:'virtual',jsx:'automatic',
      define:{'process.env.NODE_ENV':'"production"','__CPLANE_BUILD__':JSON.stringify({version:'SYNTHETIC',
        gitCommit:'NOT_VERIFIED',timestamp:'2026-10-08T00:00:00Z',environment:'MOCK_ONLY',sourceId:'NOT_LIVE_EVIDENCE'})},logLevel:'silent'});
    const s = snapshot();
    const mock:Mock = {snapshot:s,snapshotStatus:200,intention:{review_id:'synthetic-review',scope,
      evidence_version:s.evidence_version,state:'PENDING',expires_at:'2026-10-08T00:02:00Z'},
      intentionStatus:200,posts:[],blocked:[],expectedBlocked:[],requests:[],errors:[],console:[],expectedConsole:[]};
    page.on('pageerror',e=>mock.errors.push(e.message));
    page.on('console',message=>{if(message.type()==='error')mock.console.push(message.text());});
    await context.routeWebSocket(/.*/,socket=>{mock.blocked.push('WEBSOCKET '+socket.url());socket.close();});
    await context.route('**/*',async route=>{
      const request=route.request(),url=new URL(request.url()),method=request.method();
      mock.requests.push(method+' '+request.url());
      if(url.origin===origin && !url.search){
        if(url.pathname==='/v1/control-plane/snapshot' && method==='GET'){
          await route.fulfill({status:mock.snapshotStatus,json:mock.snapshot});return;
        }
        if(url.pathname==='/v1/control-plane/intention' && method==='POST'){
          const body=request.postDataJSON();
          const current=mock.snapshot as ReturnType<typeof snapshot>;
          if(JSON.stringify(body)===JSON.stringify({scope:current.scope,evidence_version:current.evidence_version})){
            mock.posts.push(body);await route.fulfill({status:mock.intentionStatus,json:mock.intention});return;
          }
        }
        if(method==='GET' && ['/overview','/evidence','/test','/review','/decision'].includes(url.pathname) && request.isNavigationRequest()){
          await route.fulfill({contentType:'text/html',body:'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><link rel="icon" href="data:,"><link rel="stylesheet" href="/main.css"></head><body><div id="root"></div><script src="/main.js"></script></body></html>'});return;
        }
        if(method==='GET' && ['/main.js','/main.css'].includes(url.pathname)){
          const file=assets.outputFiles?.find(f=>path.basename(f.path)===url.pathname.slice(1));
          if(file){await route.fulfill({contentType:url.pathname.endsWith('.js')?'text/javascript':'text/css',body:Buffer.from(file.contents)});return;}
        }
      }
      mock.blocked.push(method+' '+request.url());await route.abort('blockedbyclient');
    });
    await use(mock);
    await testInfo.attach('mock-network-evidence',{body:JSON.stringify({...mock,live:false}),contentType:'application/json'});
    expect(mock.blocked,'unexpected network request').toEqual(mock.expectedBlocked);
    expect(mock.errors,'browser runtime errors').toEqual([]);
    expect(mock.console,'unexpected browser console error').toEqual(mock.expectedConsole);
  },
});
async function noAuthority(page:Page){
  for(const name of ['APPROVE','ARM','EXECUTE','CONFIRM APPROVAL'])
    await expect(page.getByRole('button',{name,exact:true})).toHaveCount(0);
}
async function review(page:Page,mock:Mock){
  await page.goto('/overview');await noAuthority(page);
  await expect(page.getByRole('button',{name:'Continue to Evidence',exact:true})).toBeDisabled();
  await page.getByLabel('I have read the ATTESTATION scope and limitations.').check();
  await page.getByRole('button',{name:'Continue to Evidence',exact:true}).click();
  await expect(page).toHaveURL(origin+'/evidence');await noAuthority(page);
  await page.getByLabel('I inspected the exact evidence version and identity scope.').check();
  await page.getByRole('button',{name:'Continue to Human Test',exact:true}).click();
  await expect(page).toHaveURL(origin+'/test');await noAuthority(page);
  await expect(page.getByRole('button',{name:'Continue to Review',exact:true})).toBeDisabled();
  for(const [id,result] of [['runtime','PASS'],['separate','FAIL'],['boundary','BLOCKED']])
    await page.getByRole('group',{name:'Observation '+id}).getByRole('button',{name:result,exact:true}).click();
  await page.getByRole('button',{name:'Continue to Review',exact:true}).click();
  await expect(page).toHaveURL(origin+'/review');await noAuthority(page);
  await expect(page.getByText('separate: FAIL',{exact:true})).toBeVisible();
  await expect(page.getByText('boundary: BLOCKED',{exact:true})).toBeVisible();
  await page.getByLabel('I reviewed these observations and the NOT_VERIFIED limitations.').check();
  await page.getByRole('button',{name:'Continue to Decision',exact:true}).click();
  await expect(page).toHaveURL(origin+'/decision');await noAuthority(page);expect(mock.posts).toEqual([]);
}
test('five stages render, scroll and submit only explicit PENDING intention',async({page,mock},info)=>{
  await page.setViewportSize({width:390,height:640});await review(page,mock);
  await page.evaluate(()=>window.scrollTo(0,document.documentElement.scrollHeight));
  await expect.poll(()=>page.evaluate(()=>window.scrollY)).toBeGreaterThan(0);
  await page.getByRole('button',{name:'Create PENDING intention',exact:true}).click();
  await expect(page.getByRole('status')).toContainText('PENDING — untrusted intention; no authorization granted.');
  await expect(page.getByRole('button',{name:'Create PENDING intention',exact:true})).toBeDisabled();
  expect(mock.posts).toHaveLength(1);await noAuthority(page);
  await expect(page.getByText('NOT_VERIFIED',{exact:true}).first()).toBeVisible();
  await info.attach('rendering-metrics',{body:JSON.stringify(await page.evaluate(()=>({viewportWidth:innerWidth,
    documentWidth:document.documentElement.scrollWidth,scrollY,documentHeight:document.documentElement.scrollHeight}))),contentType:'application/json'});
  await page.screenshot({path:info.outputPath('pending-mobile.png'),fullPage:true});
});
for(const path of ['/evidence','/test','/review','/decision'])test('direct '+path+' cannot bypass review',async({page,mock})=>{
  await page.goto(path);await expect(page.getByRole('region',{name:'Locked stage'})).toBeVisible();
  await noAuthority(page);expect(mock.posts).toEqual([]);
});
for(const kind of ['API failure','malformed snapshot'])test(kind+' remains unavailable',async({page,mock})=>{
  mock.snapshotStatus=kind==='API failure'?503:200;mock.snapshot=kind==='API failure'?{error:'synthetic-unavailable'}:{status:'PASS'};
  if(kind==='API failure')mock.expectedConsole=['Failed to load resource: the server responded with a status of 503 (Service Unavailable)'];
  await page.goto('/decision');await expect(page.getByRole('alert')).toContainText('UNKNOWN');
  await expect(page.getByRole('alert')).toContainText('No healthy state has been inferred');
  await expect(page.getByRole('button',{name:'Create PENDING intention',exact:true})).toHaveCount(0);await noAuthority(page);
});
for(const kind of ['API rejection','invented authority','wrong evidence'])test(kind+' intention fails closed without automatic retry',async({page,mock})=>{
  await review(page,mock);
  if(kind==='API rejection'){
    mock.intentionStatus=409;
    mock.expectedConsole=['Failed to load resource: the server responded with a status of 409 (Conflict)'];
  }
  else mock.intention={...(mock.intention as object),...(kind==='invented authority'?{state:'APPROVED'}:{evidence_version:'c'.repeat(64)})};
  await page.getByRole('button',{name:'Create PENDING intention',exact:true}).click();
  await expect(page.getByRole('alert')).toBeVisible();await expect(page.getByRole('status')).toHaveCount(0);
  await expect(page.getByRole('button',{name:'Create PENDING intention',exact:true})).toBeDisabled();
  expect(mock.posts).toHaveLength(1);await noAuthority(page);
});
test('material context change clears pending and relocks the session',async({page,mock})=>{
  await review(page,mock);await page.getByRole('button',{name:'Create PENDING intention',exact:true}).click();
  await expect(page.getByRole('status')).toContainText('PENDING — untrusted intention');
  const s=mock.snapshot as ReturnType<typeof snapshot>;
  mock.snapshot={...s,evidence_version:'c'.repeat(64),binding:{...s.binding,runtime_instance:'synthetic-new-instance'}};
  await page.getByRole('button',{name:'Refresh evidence',exact:true}).click();
  await expect(page.getByRole('region',{name:'Locked stage'})).toBeVisible();
  await expect(page.getByRole('status')).toHaveCount(0);expect(mock.posts).toHaveLength(1);
  await page.getByRole('button',{name:'Go to System',exact:true}).click();
  await expect(page.getByLabel('I have read the ATTESTATION scope and limitations.')).not.toBeChecked();await noAuthority(page);
});
test('network boundary aborts an unlisted virtual-origin request',async({page,mock})=>{
  await page.goto('/overview');
  mock.expectedBlocked=['GET '+origin+'/unlisted-boundary-test'];
  mock.expectedConsole=['Failed to load resource: net::ERR_BLOCKED_BY_CLIENT.Inspector'];
  const failed=await page.evaluate(async()=>{try{await fetch('/unlisted-boundary-test');return false;}catch{return true;}});
  expect(failed).toBe(true);expect(mock.blocked).toEqual(mock.expectedBlocked);expect(mock.posts).toEqual([]);
});
