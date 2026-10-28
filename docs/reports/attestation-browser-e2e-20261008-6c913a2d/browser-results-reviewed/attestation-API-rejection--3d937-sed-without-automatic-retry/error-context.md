# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: attestation.spec.ts >> API rejection intention fails closed without automatic retry
- Location: e2e\attestation.spec.ts:117:75

# Error details

```
Error: unexpected browser console error

expect(received).toEqual(expected) // deep equality

- Expected  - 1
+ Received  + 3

- Array []
+ Array [
+   "Failed to load resource: the server responded with a status of 409 (Conflict)",
+ ]
```

# Page snapshot

```yaml
- generic [ref=e3]:
  - complementary [ref=e4]:
    - link "N NUSANTARA HUMAN ACCEPTANCE CONSOLE" [ref=e5] [cursor=pointer]:
      - /url: /overview
      - generic [ref=e6]: "N"
      - generic [ref=e7]:
        - text: NUSANTARA
        - generic [ref=e8]: HUMAN ACCEPTANCE CONSOLE
    - generic [ref=e9]: INSPECT · TEST · REVIEW · DECIDE
    - navigation "Acceptance steps" [ref=e10]:
      - link "System" [ref=e11] [cursor=pointer]:
        - /url: /overview
        - generic [aria-hidden] [ref=e12]: "01"
        - generic [ref=e13]:
          - text: System
          - generic [ref=e14]: Completed
      - link "Evidence" [ref=e15] [cursor=pointer]:
        - /url: /evidence
        - generic [aria-hidden] [ref=e16]: "02"
        - generic [ref=e17]:
          - text: Evidence
          - generic [ref=e18]: Completed
      - link "Human Test" [ref=e19] [cursor=pointer]:
        - /url: /test
        - generic [aria-hidden] [ref=e20]: "03"
        - generic [ref=e21]:
          - text: Human Test
          - generic [ref=e22]: Completed
      - link "Review" [ref=e23] [cursor=pointer]:
        - /url: /review
        - generic [aria-hidden] [ref=e24]: "04"
        - generic [ref=e25]:
          - text: Review
          - generic [ref=e26]: Completed
      - link "Decision" [ref=e27] [cursor=pointer]:
        - /url: /decision
        - generic [aria-hidden] [ref=e28]: "05"
        - generic [ref=e29]:
          - text: Decision
          - generic [ref=e30]: Current
    - group [ref=e31]:
      - generic "Engineering views" [ref=e32] [cursor=pointer]
    - generic [ref=e33]:
      - text: Read-only engineering evidenceHuman decisions remain yours
      - group [ref=e34]:
        - generic "Frontend build identity" [ref=e35] [cursor=pointer]
  - main [ref=e36]:
    - generic [ref=e37]:
      - generic [ref=e38]:
        - generic [ref=e39]: HUMAN ACCEPTANCE CONSOLE / STEP 5 OF 5
        - heading "Decision" [level=1] [ref=e40]
      - button "Refresh evidence" [ref=e41] [cursor=pointer]
    - paragraph [ref=e42]: Evidence read 3:33:57 PM · API response 10 ms
    - generic [ref=e43]:
      - heading "ATTESTATION evidence" [level=2] [ref=e44]
      - generic [ref=e45]:
        - term [ref=e46]: Evidence type
        - definition [ref=e47]: SCOPED_IN_PROCESS
        - term [ref=e48]: Evidence version
        - definition [ref=e49]: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        - term [ref=e50]: Identity scope
        - definition [ref=e51]: SCOPED_LOADED_CODE — not FULL_APPLICATION_BUILD
        - term [ref=e52]: Verification state
        - definition [ref=e53]: NOT_VERIFIED
        - term [ref=e54]: Runtime identity
        - definition [ref=e55]: NOT_VERIFIED
        - term [ref=e56]: Authorization state
        - definition [ref=e57]: "Live actions: LOCKED; operator: NOT_PROVISIONED"
        - term [ref=e58]: Target
        - definition [ref=e59]: 127.0.0.1:8000
        - term [ref=e60]: Process PID / start
        - definition [ref=e61]: 123 / 134000000000000000 (Windows FILETIME numeric projection; browser precision may be limited)
        - term [ref=e62]: Runtime instance
        - definition [ref=e63]: synthetic-instance
        - term [ref=e64]: SOURCE_SNAPSHOT
        - definition [ref=e65]: synthetic-source
        - term [ref=e66]: SCOPED_LOADED_CODE
        - definition [ref=e67]: synthetic-code
        - term [ref=e68]: ACTIVE_PROCESS_BUILD
        - definition [ref=e69]: NOT_DIRECTLY_VERIFIED
        - term [ref=e70]: Source
        - definition [ref=e71]: SYNTHETIC BROWSER TEST — NOT LIVE EVIDENCE
        - term [ref=e72]: Captured
        - definition [ref=e73]: 2026-10-08T00:00:00Z
      - paragraph [ref=e74]: SOURCE_SNAPSHOT != ACTIVE_PROCESS_BUILD. No provider health or live success is inferred.
    - paragraph [ref=e75]: Automated Test Evidence ≠ Human Observation ≠ Authenticated Server Decision.
    - paragraph [ref=e76]: "R2-A8: BLOCKED / NOT_VERIFIED. Runtime Identity: NOT_VERIFIED. ARM and EXECUTE are NOT_AUTHORIZED."
    - generic [ref=e77]:
      - heading "Bounded browser intention" [level=2] [ref=e78]
      - paragraph [ref=e79]: This action creates PENDING only. It cannot APPROVE, authenticate an operator, ARM, EXECUTE or issue a permit.
      - button "Create PENDING intention" [disabled] [ref=e80] [cursor=pointer]
      - alert [ref=e81]: Intention rejected (409). No authority granted. Do not retry automatically.
      - heading "Server review states" [level=3] [ref=e82]
      - paragraph [ref=e83]: "Native confirmation: not activated. No live IPC bridge is implemented."
    - generic [ref=e84]:
      - text: Human review session · engineering evidence remains read-only.
      - generic [ref=e85]: Session results clear when this page is reloaded.
```

# Test source

```ts
  1   | import {test as base, expect, type Page} from '@playwright/test';
  2   | import {build} from 'esbuild';
  3   | import path from 'node:path';
  4   | 
  5   | // A virtual origin fulfilled entirely through Playwright; no test web server.
  6   | const origin = 'http://attestation-e2e.invalid';
  7   | if(process.env.CPLANE_ATTESTATION_E2E !== 'MOCK_ONLY' || process.env.CPLANE_E2E_LIVE)
  8   |   throw new Error('MOCK_ONLY_MODE_REQUIRED');
  9   | const scope = 'R2-A8:ATTESTATION:ONE_GENERATION';
  10  | const snapshot = () => ({projection_contract:'ATTESTATION_FOUNDATION_V1', evidence_id:'r2-a9-auth-process',
  11  |   evidence_type:'SCOPED_IN_PROCESS', source:'SYNTHETIC BROWSER TEST — NOT LIVE EVIDENCE', scope,
  12  |   created_at:'2026-10-08T00:00:00Z', status:'NOT_VERIFIED', evidence_version:'a'.repeat(64),
  13  |   live_actions:'LOCKED', operator_policy:'NOT_PROVISIONED', binding:{scope,target:'127.0.0.1:8000',
  14  |     pid:123,process_start:134000000000000000,runtime_instance:'synthetic-instance',source_snapshot:'synthetic-source',
  15  |     scoped_loaded_code:'synthetic-code',configuration_digest:'b'.repeat(64),
  16  |     endpoint:{origin:'http://127.0.0.1:11434',connection_origin:'http://127.0.0.1:11434'},profile:'ATTESTATION',
  17  |     active_process_build:'NOT_DIRECTLY_VERIFIED',runtime_identity:'NOT_VERIFIED'},reviews:[],provider_receipt:null});
  18  | type Mock = {snapshot:unknown; snapshotStatus:number; intention:unknown; intentionStatus:number;
  19  |   posts:unknown[]; blocked:string[]; expectedBlocked:string[]; requests:string[]; errors:string[]; console:string[]};
  20  | let assets:Awaited<ReturnType<typeof build>>;
  21  | const test = base.extend<{mock:Mock}>({
  22  |   mock:async ({context,page},use,testInfo) => {
  23  |     const launch = testInfo.project.use.launchOptions;
  24  |     if(process.env.CPLANE_ATTESTATION_E2E !== 'MOCK_ONLY' || testInfo.config.webServer ||
  25  |       testInfo.project.use.baseURL !== origin || testInfo.project.use.serviceWorkers !== 'block' ||
  26  |       launch?.proxy?.server !== 'http://127.0.0.1:9' || launch.proxy.bypass !== '<-loopback>' ||
  27  |       !launch.args?.includes('--host-resolver-rules=MAP * ~NOTFOUND')) throw new Error('UNSAFE_TEST_CONFIGURATION');
  28  |     assets ??= await build({absWorkingDir:path.resolve(testInfo.config.rootDir,'..'),
  29  |       entryPoints:['src/main.tsx'],bundle:true,write:false,outdir:'virtual',jsx:'automatic',
  30  |       define:{'process.env.NODE_ENV':'"production"','__CPLANE_BUILD__':JSON.stringify({version:'SYNTHETIC',
  31  |         gitCommit:'NOT_VERIFIED',timestamp:'2026-10-08T00:00:00Z',environment:'MOCK_ONLY',sourceId:'NOT_LIVE_EVIDENCE'})},logLevel:'silent'});
  32  |     const s = snapshot();
  33  |     const mock:Mock = {snapshot:s,snapshotStatus:200,intention:{review_id:'synthetic-review',scope,
  34  |       evidence_version:s.evidence_version,state:'PENDING',expires_at:'2026-10-08T00:02:00Z'},
  35  |       intentionStatus:200,posts:[],blocked:[],expectedBlocked:[],requests:[],errors:[],console:[]};
  36  |     page.on('pageerror',e=>mock.errors.push(e.message));
  37  |     page.on('console',message=>{if(message.type()==='error')mock.console.push(message.text());});
  38  |     await context.routeWebSocket(/.*/,socket=>{mock.blocked.push('WEBSOCKET '+socket.url());socket.close();});
  39  |     await context.route('**/*',async route=>{
  40  |       const request=route.request(),url=new URL(request.url()),method=request.method();
  41  |       mock.requests.push(method+' '+request.url());
  42  |       if(url.origin===origin && !url.search){
  43  |         if(url.pathname==='/v1/control-plane/snapshot' && method==='GET'){
  44  |           await route.fulfill({status:mock.snapshotStatus,json:mock.snapshot});return;
  45  |         }
  46  |         if(url.pathname==='/v1/control-plane/intention' && method==='POST'){
  47  |           const body=request.postDataJSON();
  48  |           const current=mock.snapshot as ReturnType<typeof snapshot>;
  49  |           if(JSON.stringify(body)===JSON.stringify({scope:current.scope,evidence_version:current.evidence_version})){
  50  |             mock.posts.push(body);await route.fulfill({status:mock.intentionStatus,json:mock.intention});return;
  51  |           }
  52  |         }
  53  |         if(method==='GET' && ['/overview','/evidence','/test','/review','/decision'].includes(url.pathname) && request.isNavigationRequest()){
  54  |           await route.fulfill({contentType:'text/html',body:'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><link rel="icon" href="data:,"><link rel="stylesheet" href="/main.css"></head><body><div id="root"></div><script src="/main.js"></script></body></html>'});return;
  55  |         }
  56  |         if(method==='GET' && ['/main.js','/main.css'].includes(url.pathname)){
  57  |           const file=assets.outputFiles?.find(f=>path.basename(f.path)===url.pathname.slice(1));
  58  |           if(file){await route.fulfill({contentType:url.pathname.endsWith('.js')?'text/javascript':'text/css',body:Buffer.from(file.contents)});return;}
  59  |         }
  60  |       }
  61  |       mock.blocked.push(method+' '+request.url());await route.abort('blockedbyclient');
  62  |     });
  63  |     await use(mock);
  64  |     await testInfo.attach('mock-network-evidence',{body:JSON.stringify({...mock,live:false}),contentType:'application/json'});
  65  |     expect(mock.blocked,'unexpected network request').toEqual(mock.expectedBlocked);
  66  |     expect(mock.errors,'browser runtime errors').toEqual([]);
> 67  |     if(mock.expectedBlocked.length===0)expect(mock.console,'unexpected browser console error').toEqual([]);
      |                                                                                                ^ Error: unexpected browser console error
  68  |   },
  69  | });
  70  | async function noAuthority(page:Page){
  71  |   for(const name of ['APPROVE','ARM','EXECUTE','CONFIRM APPROVAL'])
  72  |     await expect(page.getByRole('button',{name,exact:true})).toHaveCount(0);
  73  | }
  74  | async function review(page:Page,mock:Mock){
  75  |   await page.goto('/overview');await noAuthority(page);
  76  |   await expect(page.getByRole('button',{name:'Continue to Evidence',exact:true})).toBeDisabled();
  77  |   await page.getByLabel('I have read the ATTESTATION scope and limitations.').check();
  78  |   await page.getByRole('button',{name:'Continue to Evidence',exact:true}).click();
  79  |   await expect(page).toHaveURL(origin+'/evidence');await noAuthority(page);
  80  |   await page.getByLabel('I inspected the exact evidence version and identity scope.').check();
  81  |   await page.getByRole('button',{name:'Continue to Human Test',exact:true}).click();
  82  |   await expect(page).toHaveURL(origin+'/test');await noAuthority(page);
  83  |   await expect(page.getByRole('button',{name:'Continue to Review',exact:true})).toBeDisabled();
  84  |   for(const [id,result] of [['runtime','PASS'],['separate','FAIL'],['boundary','BLOCKED']])
  85  |     await page.getByRole('group',{name:'Observation '+id}).getByRole('button',{name:result,exact:true}).click();
  86  |   await page.getByRole('button',{name:'Continue to Review',exact:true}).click();
  87  |   await expect(page).toHaveURL(origin+'/review');await noAuthority(page);
  88  |   await expect(page.getByText('separate: FAIL',{exact:true})).toBeVisible();
  89  |   await expect(page.getByText('boundary: BLOCKED',{exact:true})).toBeVisible();
  90  |   await page.getByLabel('I reviewed these observations and the NOT_VERIFIED limitations.').check();
  91  |   await page.getByRole('button',{name:'Continue to Decision',exact:true}).click();
  92  |   await expect(page).toHaveURL(origin+'/decision');await noAuthority(page);expect(mock.posts).toEqual([]);
  93  | }
  94  | test('five stages render, scroll and submit only explicit PENDING intention',async({page,mock},info)=>{
  95  |   await page.setViewportSize({width:390,height:640});await review(page,mock);
  96  |   await page.evaluate(()=>window.scrollTo(0,document.documentElement.scrollHeight));
  97  |   await expect.poll(()=>page.evaluate(()=>window.scrollY)).toBeGreaterThan(0);
  98  |   await page.getByRole('button',{name:'Create PENDING intention',exact:true}).click();
  99  |   await expect(page.getByRole('status')).toContainText('PENDING — untrusted intention; no authorization granted.');
  100 |   await expect(page.getByRole('button',{name:'Create PENDING intention',exact:true})).toBeDisabled();
  101 |   expect(mock.posts).toHaveLength(1);await noAuthority(page);
  102 |   await expect(page.getByText('NOT_VERIFIED',{exact:true}).first()).toBeVisible();
  103 |   await info.attach('rendering-metrics',{body:JSON.stringify(await page.evaluate(()=>({viewportWidth:innerWidth,
  104 |     documentWidth:document.documentElement.scrollWidth,scrollY,documentHeight:document.documentElement.scrollHeight}))),contentType:'application/json'});
  105 |   await page.screenshot({path:info.outputPath('pending-mobile.png'),fullPage:true});
  106 | });
  107 | for(const path of ['/evidence','/test','/review','/decision'])test('direct '+path+' cannot bypass review',async({page,mock})=>{
  108 |   await page.goto(path);await expect(page.getByRole('region',{name:'Locked stage'})).toBeVisible();
  109 |   await noAuthority(page);expect(mock.posts).toEqual([]);
  110 | });
  111 | for(const kind of ['API failure','malformed snapshot'])test(kind+' remains unavailable',async({page,mock})=>{
  112 |   mock.snapshotStatus=kind==='API failure'?503:200;mock.snapshot=kind==='API failure'?{error:'synthetic-unavailable'}:{status:'PASS'};
  113 |   await page.goto('/decision');await expect(page.getByRole('alert')).toContainText('UNKNOWN');
  114 |   await expect(page.getByRole('alert')).toContainText('No healthy state has been inferred');
  115 |   await expect(page.getByRole('button',{name:'Create PENDING intention',exact:true})).toHaveCount(0);await noAuthority(page);
  116 | });
  117 | for(const kind of ['API rejection','invented authority','wrong evidence'])test(kind+' intention fails closed without automatic retry',async({page,mock})=>{
  118 |   await review(page,mock);
  119 |   if(kind==='API rejection')mock.intentionStatus=409;
  120 |   else mock.intention={...(mock.intention as object),...(kind==='invented authority'?{state:'APPROVED'}:{evidence_version:'c'.repeat(64)})};
  121 |   await page.getByRole('button',{name:'Create PENDING intention',exact:true}).click();
  122 |   await expect(page.getByRole('alert')).toBeVisible();await expect(page.getByRole('status')).toHaveCount(0);
  123 |   await expect(page.getByRole('button',{name:'Create PENDING intention',exact:true})).toBeDisabled();
  124 |   expect(mock.posts).toHaveLength(1);await noAuthority(page);
  125 | });
  126 | test('material context change clears pending and relocks the session',async({page,mock})=>{
  127 |   await review(page,mock);await page.getByRole('button',{name:'Create PENDING intention',exact:true}).click();
  128 |   await expect(page.getByRole('status')).toContainText('PENDING — untrusted intention');
  129 |   const s=mock.snapshot as ReturnType<typeof snapshot>;
  130 |   mock.snapshot={...s,evidence_version:'c'.repeat(64),binding:{...s.binding,runtime_instance:'synthetic-new-instance'}};
  131 |   await page.getByRole('button',{name:'Refresh evidence',exact:true}).click();
  132 |   await expect(page.getByRole('region',{name:'Locked stage'})).toBeVisible();
  133 |   await expect(page.getByRole('status')).toHaveCount(0);expect(mock.posts).toHaveLength(1);
  134 |   await page.getByRole('button',{name:'Go to System',exact:true}).click();
  135 |   await expect(page.getByLabel('I have read the ATTESTATION scope and limitations.')).not.toBeChecked();await noAuthority(page);
  136 | });
  137 | test('network boundary aborts an unlisted virtual-origin request',async({page,mock})=>{
  138 |   await page.goto('/overview');
  139 |   mock.expectedBlocked=['GET '+origin+'/unlisted-boundary-test'];
  140 |   const failed=await page.evaluate(async()=>{try{await fetch('/unlisted-boundary-test');return false;}catch{return true;}});
  141 |   expect(failed).toBe(true);expect(mock.blocked).toEqual(mock.expectedBlocked);expect(mock.posts).toEqual([]);
  142 | });
  143 | 
```