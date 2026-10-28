# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: attestation.spec.ts >> five stages render, scroll and submit only explicit PENDING intention
- Location: e2e\attestation.spec.ts:88:1

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
  17  |   posts:unknown[]; blocked:string[]; errors:string[]; console:string[]};
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
  31  |       intentionStatus:200,posts:[],blocked:[],errors:[],console:[]};
  32  |     page.on('pageerror',e=>mock.errors.push(e.message));
  33  |     page.on('console',message=>{if(message.type()==='error')mock.console.push(message.text());});
  34  |     await context.routeWebSocket(/.*/,socket=>{mock.blocked.push('WEBSOCKET '+socket.url());socket.close();});
  35  |     await context.route('**/*',async route=>{
  36  |       const request=route.request(),url=new URL(request.url()),method=request.method();
  37  |       if(url.origin===origin && !url.search){
  38  |         if(url.pathname==='/v1/control-plane/snapshot' && method==='GET'){
  39  |           await route.fulfill({status:mock.snapshotStatus,json:mock.snapshot});return;
  40  |         }
  41  |         if(url.pathname==='/v1/control-plane/intention' && method==='POST'){
  42  |           const body=request.postDataJSON();
  43  |           const current=mock.snapshot as ReturnType<typeof snapshot>;
  44  |           if(JSON.stringify(body)===JSON.stringify({scope:current.scope,evidence_version:current.evidence_version})){
  45  |             mock.posts.push(body);await route.fulfill({status:mock.intentionStatus,json:mock.intention});return;
  46  |           }
  47  |         }
  48  |         if(method==='GET' && ['/overview','/evidence','/test','/review','/decision'].includes(url.pathname) && request.isNavigationRequest()){
  49  |           await route.fulfill({contentType:'text/html',body:'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><link rel="icon" href="data:,"><link rel="stylesheet" href="/main.css"></head><body><div id="root"></div><script src="/main.js"></script></body></html>'});return;
  50  |         }
  51  |         if(method==='GET' && ['/main.js','/main.css'].includes(url.pathname)){
  52  |           const file=assets.outputFiles?.find(f=>path.basename(f.path)===url.pathname.slice(1));
  53  |           if(file){await route.fulfill({contentType:url.pathname.endsWith('.js')?'text/javascript':'text/css',body:Buffer.from(file.contents)});return;}
  54  |         }
  55  |       }
  56  |       mock.blocked.push(method+' '+request.url());await route.abort('blockedbyclient');
  57  |     });
  58  |     await use(mock);
  59  |     await testInfo.attach('mock-network-evidence',{body:JSON.stringify({...mock,live:false}),contentType:'application/json'});
  60  |     expect(mock.blocked,'unexpected network request').toEqual([]);
  61  |     expect(mock.errors,'browser runtime errors').toEqual([]);
  62  |   },
  63  | });
  64  | async function noAuthority(page:Page){
  65  |   for(const name of ['APPROVE','ARM','EXECUTE','CONFIRM APPROVAL'])
  66  |     await expect(page.getByRole('button',{name,exact:true})).toHaveCount(0);
  67  | }
  68  | async function review(page:Page,mock:Mock){
  69  |   await page.goto('/overview');await noAuthority(page);
> 70  |   await expect(page.getByRole('button',{name:'Continue to Evidence',exact:true})).toBeDisabled();
      |                                                                                   ^ Error: expect(locator).toBeDisabled() failed
  71  |   await page.getByLabel('I have read the ATTESTATION scope and limitations.').check();
  72  |   await page.getByRole('button',{name:'Continue to Evidence',exact:true}).click();
  73  |   await expect(page).toHaveURL(origin+'/evidence');await noAuthority(page);
  74  |   await page.getByLabel('I inspected the exact evidence version and identity scope.').check();
  75  |   await page.getByRole('button',{name:'Continue to Human Test',exact:true}).click();
  76  |   await expect(page).toHaveURL(origin+'/test');await noAuthority(page);
  77  |   await expect(page.getByRole('button',{name:'Continue to Review',exact:true})).toBeDisabled();
  78  |   for(const [id,result] of [['runtime','PASS'],['separate','FAIL'],['boundary','BLOCKED']])
  79  |     await page.getByRole('group',{name:'Observation '+id}).getByRole('button',{name:result,exact:true}).click();
  80  |   await page.getByRole('button',{name:'Continue to Review',exact:true}).click();
  81  |   await expect(page).toHaveURL(origin+'/review');await noAuthority(page);
  82  |   await expect(page.getByText('separate: FAIL',{exact:true})).toBeVisible();
  83  |   await expect(page.getByText('boundary: BLOCKED',{exact:true})).toBeVisible();
  84  |   await page.getByLabel('I reviewed these observations and the NOT_VERIFIED limitations.').check();
  85  |   await page.getByRole('button',{name:'Continue to Decision',exact:true}).click();
  86  |   await expect(page).toHaveURL(origin+'/decision');await noAuthority(page);expect(mock.posts).toEqual([]);
  87  | }
  88  | test('five stages render, scroll and submit only explicit PENDING intention',async({page,mock},info)=>{
  89  |   await page.setViewportSize({width:390,height:640});await review(page,mock);
  90  |   await page.evaluate(()=>window.scrollTo(0,document.documentElement.scrollHeight));
  91  |   await expect.poll(()=>page.evaluate(()=>window.scrollY)).toBeGreaterThan(0);
  92  |   await page.getByRole('button',{name:'Create PENDING intention',exact:true}).click();
  93  |   await expect(page.getByRole('status')).toContainText('PENDING — untrusted intention; no authorization granted.');
  94  |   await expect(page.getByRole('button',{name:'Create PENDING intention',exact:true})).toBeDisabled();
  95  |   expect(mock.posts).toHaveLength(1);await noAuthority(page);
  96  |   await expect(page.getByText('NOT_VERIFIED',{exact:true}).first()).toBeVisible();
  97  |   await page.screenshot({path:info.outputPath('pending-mobile.png'),fullPage:true});
  98  | });
  99  | for(const path of ['/evidence','/test','/review','/decision'])test('direct '+path+' cannot bypass review',async({page,mock})=>{
  100 |   await page.goto(path);await expect(page.getByRole('region',{name:'Locked stage'})).toBeVisible();
  101 |   await noAuthority(page);expect(mock.posts).toEqual([]);
  102 | });
  103 | for(const kind of ['API failure','malformed snapshot'])test(kind+' remains unavailable',async({page,mock})=>{
  104 |   mock.snapshotStatus=kind==='API failure'?503:200;mock.snapshot=kind==='API failure'?{error:'synthetic-unavailable'}:{status:'PASS'};
  105 |   await page.goto('/decision');await expect(page.getByRole('alert')).toContainText('UNKNOWN');
  106 |   await expect(page.getByRole('alert')).toContainText('No healthy state has been inferred');
  107 |   await expect(page.getByRole('button',{name:'Create PENDING intention',exact:true})).toHaveCount(0);await noAuthority(page);
  108 | });
  109 | for(const kind of ['API rejection','invented authority','wrong evidence'])test(kind+' intention fails closed without automatic retry',async({page,mock})=>{
  110 |   await review(page,mock);
  111 |   if(kind==='API rejection')mock.intentionStatus=409;
  112 |   else mock.intention={...(mock.intention as object),...(kind==='invented authority'?{state:'APPROVED'}:{evidence_version:'c'.repeat(64)})};
  113 |   await page.getByRole('button',{name:'Create PENDING intention',exact:true}).click();
  114 |   await expect(page.getByRole('alert')).toBeVisible();await expect(page.getByRole('status')).toHaveCount(0);
  115 |   await expect(page.getByRole('button',{name:'Create PENDING intention',exact:true})).toBeDisabled();
  116 |   expect(mock.posts).toHaveLength(1);await noAuthority(page);
  117 | });
  118 | test('material context change clears pending and relocks the session',async({page,mock})=>{
  119 |   await review(page,mock);await page.getByRole('button',{name:'Create PENDING intention',exact:true}).click();
  120 |   await expect(page.getByRole('status')).toContainText('PENDING — untrusted intention');
  121 |   const s=mock.snapshot as ReturnType<typeof snapshot>;
  122 |   mock.snapshot={...s,evidence_version:'c'.repeat(64),binding:{...s.binding,runtime_instance:'synthetic-new-instance'}};
  123 |   await page.getByRole('button',{name:'Refresh evidence',exact:true}).click();
  124 |   await expect(page.getByRole('region',{name:'Locked stage'})).toBeVisible();
  125 |   await expect(page.getByRole('status')).toHaveCount(0);expect(mock.posts).toHaveLength(1);
  126 |   await page.getByRole('button',{name:'Go to System',exact:true}).click();
  127 |   await expect(page.getByLabel('I have read the ATTESTATION scope and limitations.')).not.toBeChecked();await noAuthority(page);
  128 | });
  129 | 
```