import {render,screen,fireEvent,waitFor,within} from '@testing-library/react';
import {beforeEach,it,expect,vi} from 'vitest';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {AdminAuthProvider,useAdminAuth} from '../src/auth';
import {ExecutionReview} from '../src/human';
import {WorkspacePage} from '../src/workspace';
import * as api from '../src/api';
vi.mock('@tanstack/react-router',()=>({Link:({to,children}:{to:string;children:React.ReactNode})=><a href={to}>{children}</a>}));
vi.mock('../src/api',async importOriginal=>({...await importOriginal<typeof import('../src/api')>(),fetchEvidencePackage:vi.fn(),fetchExecutionContext:vi.fn(),fetchExecutionHistory:vi.fn(),fetchModelStatus:vi.fn(),fetchOperationsSummary:vi.fn(),fetchChatHistory:vi.fn(),sendUserChat:vi.fn(),saveEvidenceDecision:vi.fn(),executeReviewedAction:vi.fn()}));
const binding={plan_id:'plan-test',version:'v1',action:'CONTROLLED_FILE_WRITE'};
const pkg:api.EvidencePackage={package_id:'evp_sha256_'+'a'.repeat(64),generated_at:'2026-10-19',read_scope:'ISOLATED_TEST',runtime_status:'NOT_VERIFIED',pass_allowed:true,blockers:[],criteria:[{id:'AC1',status:'VALID',summary:'Evidence uji',reason:null,evidence:['proof'],tests:['test']}],evidence:[{id:'proof',path:'test-only/proof.json',classification:'CURRENT_OFFLINE',validation_status:'VALID',sha256:null,bytes:4,reason:null}]};
const plan:api.ExecutionContext={change_id:'plan-test',objective:'Tinjau pekerjaan uji',expected_change:'Perubahan uji terisolasi',target_files:['fixture.txt'],operation:'write',plan_binding:binding,risk:'LOW',tests_required:['test'],rollback:'restore fixture',checked_at:'2026-10-19',source:'ISOLATED_TEST'};
const history:api.ExecutionHistory={decisions:[],executions:[],decision_audit:'VALIDATED_HASH_CHAIN',execution_audit:'TEST_ONLY'};
function mount(element:React.ReactNode,token='test-only'){
 const client=new QueryClient({defaultOptions:{queries:{retry:false}}});
 render(<QueryClientProvider client={client}><AdminAuthProvider initialToken={token}>{element}</AdminAuthProvider></QueryClientProvider>);
 return client;
}
beforeEach(()=>{
 vi.resetAllMocks();
 Object.defineProperty(HTMLDialogElement.prototype,'showModal',{configurable:true,value:function(this:HTMLDialogElement){this.open=true;}});
 Object.defineProperty(HTMLDialogElement.prototype,'close',{configurable:true,value:function(this:HTMLDialogElement){this.open=false;this.dispatchEvent(new Event('close'));}});
 vi.mocked(api.fetchEvidencePackage).mockResolvedValue(pkg);
 vi.mocked(api.fetchExecutionContext).mockResolvedValue(plan);
 vi.mocked(api.fetchExecutionHistory).mockResolvedValue(history);
 vi.mocked(api.fetchModelStatus).mockResolvedValue({provider:'ollama',model:'fixture-local',revision:2,process_id:1,consistency_scope:'CURRENT_PROCESS_ONLY',availability:'NOT_VERIFIED',status:'NOT_VERIFIED',selection_enabled:false,selection_source:'TEST_ONLY',last_request:null});
 vi.mocked(api.fetchOperationsSummary).mockResolvedValue({scope:'TEST_ONLY',source:'fixture',pending_work:1,pending_review:1,reason:null,checked_at:'2026-10-19',tasks:[{id:'task-test',objective:'Telusuri bukti',status:'HOLD',updated_at:'2026-10-19',source:'fixture'}]});
 vi.mocked(api.fetchChatHistory).mockResolvedValue({session_id:'fixture',turns:[]});
 vi.mocked(api.saveEvidenceDecision).mockImplementation(async input=>({...input,package_id:input.packageId,decision_id:'dec_'+'a'.repeat(32),reviewer_principal:'test',authentication:'TEST_ONLY',timestamp:new Date().toISOString(),notes:input.notes,test_evidence:[],blockers:[],record_hash:'a'.repeat(64)}));
});
it('explains the backend work origin and approval sequence without executing',async()=>{
 vi.mocked(api.fetchExecutionContext).mockResolvedValue({...plan,plan_origin:{kind:'DEVELOPER_OPERATION',actor_identity:'NOT_RECORDED'},workflow:{
  version:'nusantara.controlled-work.v1',scope:'CONTROLLED_FILE_WRITE',source:'Developer Core / change_plan.json',approval_validity_seconds:3600,approval_executes_work:false,
  steps:[['PREPARE','Siapkan rencana'],['VERIFY','Periksa bukti'],['DECIDE','Keputusan operator'],['AUTHORIZE','Periksa izin'],['EXECUTE','Jalankan'],['AUDIT','Catat hasil']].map(([id,label])=>({id:id as api.WorkApprovalWorkflow['steps'][number]['id'],label,actor:'Penanggung jawab contoh',description:'Keterangan dari backend'})),
  decisions:[{code:'PASS',label:'Setujui',description:'Terima rencana; jalankan terpisah.'},{code:'FAIL',label:'Tolak',description:'Eksekusi tidak diizinkan.'},{code:'HOLD',label:'Tunda',description:'Lengkapi bukti terlebih dahulu.'}]
 }});
 mount(<ExecutionReview title="Human Control"/>);
 const flow=await screen.findByRole('region',{name:'Alur persetujuan pekerjaan'});
 const steps=await within(flow).findByRole('list');
 expect(within(steps).getByText('Siapkan rencana')).toBeVisible();
 expect(within(steps).getByText('Catat hasil')).toBeVisible();
 expect(flow).toHaveTextContent('Developer Core / change_plan.json');
 expect(flow).toHaveTextContent('Identitas personal pembuat belum tercatat');
 expect(flow).toHaveTextContent('Setujui tidak langsung menjalankan pekerjaan');
 expect(api.saveEvidenceDecision).not.toHaveBeenCalled();
 expect(api.executeReviewedAction).not.toHaveBeenCalled();
});
it.each(['PASS','FAIL','HOLD'] as const)('saves %s only after explicit selection and submission, retaining backend binding',async decision=>{
 mount(<ExecutionReview title="Human Control"/>);
 await screen.findAllByText('Tinjau pekerjaan uji');
 fireEvent.click(screen.getByRole('button',{name:'Tinjau & beri keputusan'}));
 const dialog=await screen.findByRole('dialog',{name:'Tinjau keputusan Anda'});
 expect(api.saveEvidenceDecision).not.toHaveBeenCalled();
 const save=within(dialog).getByRole('button',{name:'Simpan keputusan'});expect(save).toBeDisabled();
 await waitFor(()=>expect(within(dialog).getByRole('button',{name:new RegExp(decision)})).toBeEnabled());
 fireEvent.click(within(dialog).getByRole('button',{name:new RegExp(decision)}));
 fireEvent.change(within(dialog).getByLabelText('Alasan keputusan (opsional)'),{target:{value:'Dasar keputusan uji'}});
 expect(api.saveEvidenceDecision).not.toHaveBeenCalled();fireEvent.click(save);
 await waitFor(()=>expect(api.saveEvidenceDecision).toHaveBeenCalledWith({packageId:pkg.package_id,decision,notes:'Dasar keputusan uji',token:'test-only',planBinding:binding}));
 expect(api.executeReviewedAction).not.toHaveBeenCalled();
});
it('keeps PASS locked for blocked evidence, allows HOLD, and leaves server rejection visible',async()=>{
 vi.mocked(api.fetchEvidencePackage).mockResolvedValue({...pkg,pass_allowed:false,blockers:[{id:'AC1',reason:'ARTIFACT_INVALID'}]});
 vi.mocked(api.saveEvidenceDecision).mockRejectedValue(new Error('Ditolak backend (409)'));
 mount(<ExecutionReview title="Human Control"/>);await screen.findAllByText('Tinjau pekerjaan uji');
 fireEvent.click(screen.getByRole('button',{name:'Tinjau & beri keputusan'}));
 const dialog=await screen.findByRole('dialog',{name:'Tinjau keputusan Anda'});
 expect(within(dialog).getByRole('button',{name:/PASS/})).toBeDisabled();
 await waitFor(()=>expect(within(dialog).getByRole('button',{name:/HOLD/})).toBeEnabled());
 fireEvent.click(within(dialog).getByRole('button',{name:/HOLD/}));fireEvent.click(within(dialog).getByRole('button',{name:'Simpan keputusan'}));
 expect(await within(dialog).findByRole('status')).toHaveTextContent('Ditolak backend');
 expect(dialog).toBeVisible();expect(screen.getByRole('button',{name:'Jalankan tindakan yang disetujui'})).toBeDisabled();
});
it('revokes decision selection when credentials are replaced and never exposes the credential in cache keys',async()=>{
 function Change(){const {setToken}=useAdminAuth();return <button onClick={()=>setToken('rejected')}>Ganti akses</button>;}
 const client=mount(<><Change/><ExecutionReview title="Human Control"/></>);await screen.findAllByText('Tinjau pekerjaan uji');
 fireEvent.click(screen.getByRole('button',{name:'Tinjau & beri keputusan'}));const dialog=await screen.findByRole('dialog');
 await waitFor(()=>expect(within(dialog).getByRole('button',{name:/PASS/})).toBeEnabled());fireEvent.click(within(dialog).getByRole('button',{name:/PASS/}));
 vi.mocked(api.fetchExecutionHistory).mockRejectedValue(new Error('Akses ditolak'));vi.mocked(api.fetchExecutionContext).mockRejectedValue(new Error('Akses ditolak'));
 fireEvent.click(screen.getByRole('button',{name:'Ganti akses'}));
 await waitFor(()=>expect(within(dialog).getByRole('button',{name:'Simpan keputusan'})).toBeDisabled());
 expect(api.saveEvidenceDecision).not.toHaveBeenCalled();expect(JSON.stringify(client.getQueryCache().getAll().map(q=>q.queryKey))).not.toContain('test-only');
});
it('retains Chat draft across tabs and filters actual evidence without adding demo artifacts',async()=>{
 mount(<WorkspacePage/>);await screen.findAllByText('Tinjau pekerjaan uji');
 fireEvent.click(screen.getByRole('tab',{name:'Chat V1'}));fireEvent.change(screen.getByLabelText('Pertanyaan Anda'),{target:{value:'Draft PIAK-03'}});
 fireEvent.click(screen.getByRole('tab',{name:/Evidence/}));expect(await screen.findByRole('cell',{name:'proof test-only/proof.json'})).toBeVisible();
 fireEvent.click(screen.getByRole('button',{name:'Evidence proof ↗'}));expect(await screen.findByRole('dialog',{name:'Evidence proof'})).toHaveTextContent('ISOLATED_TEST');
 fireEvent.click(screen.getByRole('button',{name:'Tutup detail'}));
 fireEvent.click(screen.getByRole('tab',{name:'Chat V1'}));expect(screen.getByLabelText('Pertanyaan Anda')).toHaveValue('Draft PIAK-03');
 expect(api.sendUserChat).not.toHaveBeenCalled();
});
it('shows honest empty and failed states for workspace data and blocker history',async()=>{
 vi.mocked(api.fetchOperationsSummary).mockRejectedValue(new Error('Tugas tidak tersedia'));
 mount(<WorkspacePage/>);expect(await screen.findByText('Tugas tidak tersedia')).toBeVisible();
 fireEvent.click(screen.getByRole('tab',{name:/Blocker/}));fireEvent.click(await screen.findByRole('button',{name:'Selesai'}));
 expect(screen.getByText(/Riwayat penyelesaian blocker belum tersedia/)).toBeVisible();
 expect(api.saveEvidenceDecision).not.toHaveBeenCalled();
});

