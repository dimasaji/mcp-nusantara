# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: attestation.spec.ts >> five stages render, scroll and submit only explicit PENDING intention
- Location: e2e\attestation.spec.ts:87:1

# Error details

```
Error: expect(locator).toBeDisabled() failed

Locator: getByRole('button', { name: 'Continue to Evidence', exact: true })
Expected: disabled
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeDisabled" getByRole('button', { name: 'Continue to Evidence', exact: true }) with timeout 5000ms
  - waiting for getByRole('button', { name: 'Continue to Evidence', exact: true })

```

```yaml
- strong: Something went wrong!
- button "Show Error"
```

# Test source

```ts
  1   | import {test as base, expect, type Page} from '@playwright/test';
  2   | import {build} from 'esbuild';
  3   | import path from 'node:path';
  4   | 
  5   | // A virtual origin fulfilled entirely through Playwright; no test web server.
  6   | const origin = 'http://attestation-e2e.invalid';
  7   | const scope = 'R2-A8:ATTESTATION:ONE_GENERATION';
  8   | const snapshot = () => ({projection_contract:'ATTESTATION_FOUNDATION_V1', evidence_id:'r2-a9-auth-process',
  9   |   evidence_type:'SCOPED_IN_PROCESS', source:'SYNTHETIC BROWSER TEST — NOT LIVE EVIDENCE', scope,
  10  |   created_at:'2026-10-08T00:00:00Z', status:'NOT_VERIFIED', evidence_version:'a'.repeat(64),
  11  |   live_actions:'LOCKED', operator_policy:'NOT_PROVISIONED', binding:{scope,target:'127.0.0.1:8000',
  12  |     pid:123,process_start:134000000000000000,runtime_instance:'synthetic-instance',source_snapshot:'synthetic-source',
  13  |     scoped_loaded_code:'synthetic-code',configuration_digest:'b'.repeat(64),
  14  |     endpoint:{origin:'http://127.0.0.1:11434',connection_origin:'http://127.0.0.1:11434'},profile:'ATTESTATION',
  15  |     active_process_build:'NOT_DIRECTLY_VERIFIED',runtime_identity:'NOT_VERIFIED'},reviews:[],provider_receipt:null});
  16  | type Mock = {snapshot:unknown; snapshotStatus:number; intention:unknown; intentionStatus:number;
  17  |   posts:unknown[]; blocked:string[]; errors:string[]};
  18  | let assets:Awaited<ReturnType<typeof build>>;
  19  | const test = base.extend<{mock:Mock}>({
  20  |   mock:async ({context,page},use,testInfo) => {
  21  |     const launch = testInfo.project.use.launchOptions;
  22  |     if(process.env.CPLANE_ATTESTATION_E2E !== 'MOCK_ONLY' || testInfo.config.webServer ||
  23  |       testInfo.project.use.baseURL !== origin || testInfo.project.use.serviceWorkers !== 'block' ||
  24  |       launch?.proxy?.server !== 'http://127.0.0.1:9') throw new Error('UNSAFE_TEST_CONFIGURATION');
  25  |     assets ??= await build({absWorkingDir:path.resolve(testInfo.config.rootDir,'..'),
  26  |       entryPoints:['src/main.tsx'],bundle:true,write:false,outdir:'virtual',jsx:'automatic',
  27  |       define:{'process.env.NODE_ENV':'"production"'},logLevel:'silent'});
  28  |     const s = snapshot();
  29  |     const mock:Mock = {snapshot:s,snapshotStatus:200,intention:{review_id:'synthetic-review',scope,
  30  |       evidence_version:s.evidence_version,state:'PENDING',expires_at:'2026-10-08T00:02:00Z'},
  31  |       intentionStatus:200,posts:[],blocked:[],errors:[]};
  32  |     page.on('pageerror',e=>mock.errors.push(e.message));
  33  |     await context.routeWebSocket(/.*/,socket=>{mock.blocked.push('WEBSOCKET '+socket.url());socket.close();});
  34  |     await context.route('**/*',async route=>{
  35  |       const request=route.request(),url=new URL(request.url()),method=request.method();
  36  |       if(url.origin===origin && !url.search){
  37  |         if(url.pathname==='/v1/control-plane/snapshot' && method==='GET'){
  38  |           await route.fulfill({status:mock.snapshotStatus,json:mock.snapshot});return;
  39  |         }
  40  |         if(url.pathname==='/v1/control-plane/intention' && method==='POST'){
  41  |           const body=request.postDataJSON();
  42  |           const current=mock.snapshot as ReturnType<typeof snapshot>;
  43  |           if(JSON.stringify(body)===JSON.stringify({scope:current.scope,evidence_version:current.evidence_version})){
  44  |             mock.posts.push(body);await route.fulfill({status:mock.intentionStatus,json:mock.intention});return;
  45  |           }
  46  |         }
  47  |         if(method==='GET' && ['/overview','/evidence','/test','/review','/decision'].includes(url.pathname) && request.isNavigationRequest()){
  48  |           await route.fulfill({contentType:'text/html',body:'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><link rel="icon" href="data:,"><link rel="stylesheet" href="/main.css"></head><body><div id="root"></div><script src="/main.js"></script></body></html>'});return;
  49  |         }
  50  |         if(method==='GET' && ['/main.js','/main.css'].includes(url.pathname)){
  51  |           const file=assets.outputFiles?.find(f=>path.basename(f.path)===url.pathname.slice(1));
  52  |           if(file){await route.fulfill({contentType:url.pathname.endsWith('.js')?'text/javascript':'text/css',body:Buffer.from(file.contents)});return;}
  53  |         }
  54  |       }
  55  |       mock.blocked.push(method+' '+request.url());await route.abort('blockedbyclient');
  56  |     });
  57  |     await use(mock);
  58  |     await testInfo.attach('mock-network-evidence',{body:JSON.stringify({posts:mock.posts,blocked:mock.blocked,errors:mock.errors,live:false}),contentType:'application/json'});
  59  |     expect(mock.blocked,'unexpected network request').toEqual([]);
  60  |     expect(mock.errors,'browser runtime errors').toEqual([]);
  61  |   },
  62  | });
  63  | async function noAuthority(page:Page){
  64  |   for(const name of ['APPROVE','ARM','EXECUTE','CONFIRM APPROVAL'])
  65  |     await expect(page.getByRole('button',{name,exact:true})).toHaveCount(0);
  66  | }
  67  | async function review(page:Page,mock:Mock){
  68  |   await page.goto('/overview');await noAuthority(page);
> 69  |   await expect(page.getByRole('button',{name:'Continue to Evidence',exact:true})).toBeDisabled();
      |                                                                                   ^ Error: expect(locator).toBeDisabled() failed
  70  |   await page.getByLabel('I have read the ATTESTATION scope and limitations.').check();
  71  |   await page.getByRole('button',{name:'Continue to Evidence',exact:true}).click();
  72  |   await expect(page).toHaveURL(origin+'/evidence');await noAuthority(page);
  73  |   await page.getByLabel('I inspected the exact evidence version and identity scope.').check();
  74  |   await page.getByRole('button',{name:'Continue to Human Test',exact:true}).click();
  75  |   await expect(page).toHaveURL(origin+'/test');await noAuthority(page);
  76  |   await expect(page.getByRole('button',{name:'Continue to Review',exact:true})).toBeDisabled();
  77  |   for(const [id,result] of [['runtime','PASS'],['separate','FAIL'],['boundary','BLOCKED']])
  78  |     await page.getByRole('group',{name:'Observation '+id}).getByRole('button',{name:result,exact:true}).click();
  79  |   await page.getByRole('button',{name:'Continue to Review',exact:true}).click();
  80  |   await expect(page).toHaveURL(origin+'/review');await noAuthority(page);
  81  |   await expect(page.getByText('separate: FAIL',{exact:true})).toBeVisible();
  82  |   await expect(page.getByText('boundary: BLOCKED',{exact:true})).toBeVisible();
  83  |   await page.getByLabel('I reviewed these observations and the NOT_VERIFIED limitations.').check();
  84  |   await page.getByRole('button',{name:'Continue to Decision',exact:true}).click();
  85  |   await expect(page).toHaveURL(origin+'/decision');await noAuthority(page);expect(mock.posts).toEqual([]);
  86  | }
  87  | test('five stages render, scroll and submit only explicit PENDING intention',async({page,mock},info)=>{
  88  |   await page.setViewportSize({width:390,height:640});await review(page,mock);
  89  |   await page.evaluate(()=>window.scrollTo(0,document.documentElement.scrollHeight));
  90  |   await expect.poll(()=>page.evaluate(()=>window.scrollY)).toBeGreaterThan(0);
  91  |   await page.getByRole('button',{name:'Create PENDING intention',exact:true}).click();
  92  |   await expect(page.getByRole('status')).toContainText('PENDING — untrusted intention; no authorization granted.');
  93  |   await expect(page.getByRole('button',{name:'Create PENDING intention',exact:true})).toBeDisabled();
  94  |   expect(mock.posts).toHaveLength(1);await noAuthority(page);
  95  |   await expect(page.getByText('NOT_VERIFIED',{exact:true}).first()).toBeVisible();
  96  |   await page.screenshot({path:info.outputPath('pending-mobile.png'),fullPage:true});
  97  | });
  98  | for(const path of ['/evidence','/test','/review','/decision'])test('direct '+path+' cannot bypass review',async({page,mock})=>{
  99  |   await page.goto(path);await expect(page.getByRole('region',{name:'Locked stage'})).toBeVisible();
  100 |   await noAuthority(page);expect(mock.posts).toEqual([]);
  101 | });
  102 | for(const kind of ['API failure','malformed snapshot'])test(kind+' remains unavailable',async({page,mock})=>{
  103 |   mock.snapshotStatus=kind==='API failure'?503:200;mock.snapshot=kind==='API failure'?{error:'synthetic-unavailable'}:{status:'PASS'};
  104 |   await page.goto('/decision');await expect(page.getByRole('alert')).toContainText('UNKNOWN');
  105 |   await expect(page.getByRole('alert')).toContainText('No healthy state has been inferred');
  106 |   await expect(page.getByRole('button',{name:'Create PENDING intention',exact:true})).toHaveCount(0);await noAuthority(page);
  107 | });
  108 | for(const kind of ['API rejection','invented authority','wrong evidence'])test(kind+' intention fails closed without automatic retry',async({page,mock})=>{
  109 |   await review(page,mock);
  110 |   if(kind==='API rejection')mock.intentionStatus=409;
  111 |   else mock.intention={...(mock.intention as object),...(kind==='invented authority'?{state:'APPROVED'}:{evidence_version:'c'.repeat(64)})};
  112 |   await page.getByRole('button',{name:'Create PENDING intention',exact:true}).click();
  113 |   await expect(page.getByRole('alert')).toBeVisible();await expect(page.getByRole('status')).toHaveCount(0);
  114 |   await expect(page.getByRole('button',{name:'Create PENDING intention',exact:true})).toBeDisabled();
  115 |   expect(mock.posts).toHaveLength(1);await noAuthority(page);
  116 | });
  117 | test('material context change clears pending and relocks the session',async({page,mock})=>{
  118 |   await review(page,mock);await page.getByRole('button',{name:'Create PENDING intention',exact:true}).click();
  119 |   await expect(page.getByRole('status')).toContainText('PENDING — untrusted intention');
  120 |   const s=mock.snapshot as ReturnType<typeof snapshot>;
  121 |   mock.snapshot={...s,evidence_version:'c'.repeat(64),binding:{...s.binding,runtime_instance:'synthetic-new-instance'}};
  122 |   await page.getByRole('button',{name:'Refresh evidence',exact:true}).click();
  123 |   await expect(page.getByRole('region',{name:'Locked stage'})).toBeVisible();
  124 |   await expect(page.getByRole('status')).toHaveCount(0);expect(mock.posts).toHaveLength(1);
  125 |   await page.getByRole('button',{name:'Go to System',exact:true}).click();
  126 |   await expect(page.getByLabel('I have read the ATTESTATION scope and limitations.')).not.toBeChecked();await noAuthority(page);
  127 | });
  128 | 
```