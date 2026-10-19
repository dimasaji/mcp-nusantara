import {render,screen,fireEvent,waitFor} from '@testing-library/react';
import type {ReactNode} from 'react';
import {createMemoryHistory,createRootRoute,createRoute,createRouter,RouterProvider} from '@tanstack/react-router';
import {beforeEach,describe,it,expect,vi} from 'vitest';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {AdminAuthProvider} from '../src/auth';
import {OverviewPage} from '../src/overview';
import {VerificationPage} from '../src/verification';
import {ExecutionReview} from '../src/human';
import {readiness} from '../src/readiness';
import {readSnapshotFile} from './snapshot-file';
import {SystemHealthSchema} from '../src/schemas';
import type {DecisionRecord,EvidencePackage,ExecutionContext} from '../src/api';

const packageId=`evp_sha256_${'a'.repeat(64)}`;
const otherPackageId=`evp_sha256_${'b'.repeat(64)}`;
const planBinding={plan_id:'NORMAL-718d7e134aa1ee32',version:'d'.repeat(64),action:'CONTROLLED_FILE_WRITE'};
const validPackage:EvidencePackage={package_id:packageId,generated_at:'2026-10-15T00:00:00Z',
  read_scope:'MANIFEST_DECLARED_OFFLINE_ARTIFACTS_ONLY',runtime_status:'NOT_VERIFIED',pass_allowed:true,
  evidence:[{id:'current-test-run',path:'docs/reports/x/current-test-run.json',classification:'CURRENT_OFFLINE',
    validation_status:'VALID',sha256:'c'.repeat(64),bytes:10,reason:null,results_path:'docs/reports/x/results-bundle.json',
    results_sha256:'d'.repeat(64),result_artifacts:[{path:'docs/reports/x/python-results.xml',sha256:'e'.repeat(64),bytes:20}]}],
  criteria:Array.from({length:15},(_,i)=>({id:`AC${i+1}`,summary:`kriteria ${i+1}`,status:'VALID',evidence:[`src${i}.py`],tests:[`test_${i}`],reason:null})),
  blockers:[]};
const blockedPackage:EvidencePackage={...validPackage,pass_allowed:false,
  criteria:validPackage.criteria.map((c,i)=>i===0?{...c,status:'NOT_VERIFIED',reason:'TEST_SOURCE_CHANGED_AFTER_RUN'}:c),
  blockers:[{id:'AC1',reason:'TEST_SOURCE_CHANGED_AFTER_RUN'}]};
const plan:ExecutionContext={change_id:'NORMAL-718d7e134aa1ee32',expected_change:'Membuat satu salinan panduan',
  target_files:['docs/operational/published/NUSANTARA-V1-OPERATOR.md'],operation:'CONTROLLED_FILE_WRITE',
  plan_binding:planBinding,objective:'Publikasikan panduan teknis operator',risk:'LOW: satu file dokumentasi baru.',
  tests_required:['test_normal_plan_prepares_without_human_approval'],rollback:'Pindahkan file panduan baru ke arsip.',
  checked_at:'2026-10-15T00:00:00Z',source:'Developer Core / change_plan.json'};
const decision=(package_id=packageId,at=new Date().toISOString()):DecisionRecord=>({decision_id:'dec_'+'1'.repeat(32),
  package_id,decision:'PASS',reviewer_principal:'admin-token-holder',authentication:'NUSANTARA_ADMIN_TOKEN',
  timestamp:at,notes:'',test_evidence:['test_1'],blockers:[],record_hash:'f'.repeat(64),plan_binding:planBinding});
const history=(decisions:DecisionRecord[])=>({decisions,executions:[],decision_audit:'VALIDATED_HASH_CHAIN',execution_audit:'LOCAL_PERSISTED_LOG'});

/** Link needs a real router context, so render inside a memory router. */
const linkTargets=['/overview','/system','/evidence','/console','/review-execute','/verification','/review'];
function renderWith(node:ReactNode,token='test-token',entry='/verification'){
  let current:ReactNode=node;
  const root=createRootRoute({component:()=><>{current}</>});
  const router=createRouter({routeTree:root.addChildren(linkTargets.map(path=>createRoute({getParentRoute:()=>root,path,component:()=>null}))),
    history:createMemoryHistory({initialEntries:[entry]})});
  const client=new QueryClient({defaultOptions:{queries:{retry:false}}});
  const view=render(<QueryClientProvider client={client}><AdminAuthProvider initialToken={token}><RouterProvider router={router}/></AdminAuthProvider></QueryClientProvider>);
  current=node;
  return view;
}
function stubFetch(pkg:EvidencePackage,records:DecisionRecord[]=[]){
  vi.stubGlobal('fetch',vi.fn(async(input:RequestInfo|URL)=>{
    const url=String(input);
    const response=(body:unknown,status=200)=>({ok:status>=200&&status<300,status,json:async()=>body});
    if(url.includes('/evidence-package'))return response(pkg);
    if(url.includes('/execution-context'))return response(plan);
    if(url.includes('/history'))return response(history(records));
    if(url.includes('/decisions'))return response({records,audit_status:'VALIDATED_HASH_CHAIN'});
    if(url.includes('/snapshot'))return response(SystemHealthSchema.parse(readSnapshotFile()));
    return response({});
  }));
}
/** Text may legitimately appear both in a status panel and in a readiness reason. */
function seen(pattern:RegExp|string){expect(screen.getAllByText(pattern).length).toBeGreaterThan(0);}
beforeEach(()=>vi.unstubAllGlobals());

describe('five separate readiness facts',()=>{
  it('never merges evidence, plan, operator, decision and execution into one ready flag',()=>{
    const base={token:'t',packageState:{state:'READY' as const,pkg:validPackage},
      planState:{state:'READY' as const,context:plan},auditState:{state:'READY' as const,history:history([])}};
    const anonymous=readiness({...base,token:''});
    expect(anonymous.evidenceValid).toBe(true);
    expect(anonymous.planReady).toBe(true);
    expect(anonymous.operatorAuthenticated).toBe(false);
    expect(anonymous.decisionAvailable).toBe(false);
    expect(anonymous.executionReady).toBe(false);
    const authenticated=readiness(base);
    expect(authenticated.decisionAvailable).toBe(true);
    expect(authenticated.executionReady).toBe(false);
    expect(readiness({...base,auditState:{state:'READY',history:history([decision()])}}).executionReady).toBe(true);
    const otherPackage=readiness({...base,packageState:{state:'READY',pkg:{...validPackage,package_id:otherPackageId}}});
    expect(otherPackage.decisionAvailable).toBe(true);
    expect(otherPackage.executionReady).toBe(false);
    expect(authenticated.checks.map(c=>c.id)).toEqual(['EV','PLAN','AUTH','DEC','EXEC']);
  });
  it('keeps PASS blocked when evidence is invalid but FAIL and HOLD available',()=>{
    const model=readiness({token:'t',packageState:{state:'READY',pkg:blockedPackage},
      planState:{state:'READY',context:plan},auditState:{state:'READY',history:history([])}});
    expect(model.evidenceValid).toBe(false);
    expect(model.decisionAvailable).toBe(false);
    expect(model.operatorAuthenticated).toBe(true);
    expect(model.checks.find(c=>c.id==='EV')?.why).toContain('Source berubah setelah test-run');
  });
  it('expires a PASS that no longer matches the current plan',()=>{
    const old=decision(packageId,new Date(Date.now()-7_200_000).toISOString());
    expect(readiness({token:'t',packageState:{state:'READY',pkg:validPackage},planState:{state:'READY',context:plan},
      auditState:{state:'READY',history:history([old])}}).executionReady).toBe(false);
  });
  it('requires authentication, a valid timestamp, exact action and an unused decision',()=>{
    const receipt=decision();
    const base={token:'t',packageState:{state:'READY' as const,pkg:validPackage},planState:{state:'READY' as const,context:plan},auditState:{state:'READY' as const,history:history([receipt])}};
    expect(readiness(base).executionReady).toBe(true);
    const completed=readiness({...base,planState:{state:'READY',context:{...plan,completed:true}}});
    expect(completed.executionReady).toBe(false);
    expect(completed.decisionAvailable).toBe(false);
    expect(readiness({...base,token:''}).executionReady).toBe(false);
    for(const timestamp of ['invalid',new Date(Date.now()+60_000).toISOString()]){
      expect(readiness({...base,auditState:{state:'READY',history:history([{...receipt,timestamp}])}}).executionReady).toBe(false);
    }
    expect(readiness({...base,planState:{state:'READY',context:{...plan,plan_binding:{...planBinding,action:'OTHER'}}}}).executionReady).toBe(false);
    const consumed={...history([receipt]),executions:[{timestamp:receipt.timestamp,change_id:plan.change_id,package_id:packageId,decision_id:receipt.decision_id,result:'AUTHORIZED_ATTEMPT',files_changed:[],reason:null}]};
    expect(readiness({...base,auditState:{state:'READY',history:consumed}}).executionReady).toBe(false);
    expect(readiness({...base,auditState:{state:'READY',history:history([receipt,{...receipt,decision:'HOLD'}])}}).executionReady).toBe(false);
  });
});

describe('verification page',()=>{
  it('rechecks authentication when one nonempty token is replaced by another',async()=>{
    stubFetch(validPackage);
    const original=globalThis.fetch;
    vi.stubGlobal('fetch',vi.fn(async(input:RequestInfo|URL,init?:RequestInit)=>{
      if(String(input).includes('/history')&&(init?.headers as Record<string,string>)?.['X-Admin-Token']==='wrong')return {ok:false,status:403,json:async()=>({})};
      return original(input,init);
    }));
    renderWith(<VerificationPage/>);
    await waitFor(()=>expect(screen.getByRole('button',{name:'PASS'})).toBeEnabled());
    fireEvent.change(screen.getByLabelText('Token operator'),{target:{value:'wrong'}});
    await waitFor(()=>expect(screen.getByRole('button',{name:'PASS'})).toBeDisabled());
    expect(await screen.findByRole('alert')).toHaveTextContent('Akses ditolak');
    fireEvent.change(screen.getByLabelText('Token operator'),{target:{value:'new-correct-token'}});
    await waitFor(()=>expect(screen.getByRole('button',{name:'PASS'})).toBeEnabled());
  });
  it('explains what changed, what was tested and the next step',async()=>{
    stubFetch(validPackage);
    renderWith(<VerificationPage/>);
    expect(await screen.findByText('Lima status terpisah')).toBeInTheDocument();
    for(const id of ['EV','PLAN','AUTH','DEC','EXEC'])seen(new RegExp(id+': '));
    expect(await screen.findByRole('heading',{name:'1. Apa yang akan dikerjakan'})).toBeInTheDocument();
    expect(await screen.findByRole('heading',{name:'2. Apakah sudah siap'})).toBeInTheDocument();
    seen(/tidak membuktikan inferensi model/);
    expect(await screen.findByText(/Tidak ada blocker/)).toBeInTheDocument();
    expect(await screen.findByRole('button',{name:'PASS'})).toBeEnabled();
    expect(screen.getByRole('button',{name:'Jalankan tindakan yang disetujui'})).toBeDisabled();
  });
  it('states plainly when no operator token is present',async()=>{
    stubFetch(validPackage);
    renderWith(<VerificationPage/>,'');
    expect(await screen.findByText('Status operator')).toBeInTheDocument();
    seen(/Anda masih bisa membaca bukti/);
    seen(/AUTH: /);
  });
});

describe('review and execute page',()=>{
  it('shows five separate statuses, disabled reasons and persistent history',async()=>{
    stubFetch(validPackage);
    renderWith(<ExecutionReview/>,'test-token','/review-execute');
    expect(await screen.findByText('Lima status terpisah')).toBeInTheDocument();
    seen('Status operator');
    expect(await screen.findByRole('heading',{name:'3. Keputusan pengguna'})).toBeInTheDocument();
    expect(screen.getByRole('button',{name:'PASS'})).toBeEnabled();
    seen(/History dibaca dari server/);
  });
  it('locks decisions without a token and explains why',async()=>{
    stubFetch(validPackage);
    renderWith(<ExecutionReview/>,'','/review-execute');
    expect(await screen.findByText(/keputusan dan History memerlukan autentikasi/)).toBeInTheDocument();
    expect(await screen.findByRole('button',{name:'PASS'})).toBeDisabled();
    expect(await screen.findByText(/PASS belum tersedia: Masukkan token/)).toBeInTheDocument();
  });
});

describe('overview page',()=>{
  it('shows system condition, attention items and the six responsibilities',async()=>{
    stubFetch(validPackage);
    renderWith(<OverviewPage/>,'test-token','/overview');
    expect(await screen.findByText('Enam tanggung jawab Developer Core')).toBeInTheDocument();
    seen('Kondisi sistem');
    seen('Yang perlu perhatian');
    seen(/Blocker & Diagnosis/);
    seen(/Langkah berikutnya/);
  });
});

