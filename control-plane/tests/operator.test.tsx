import {render,screen,fireEvent,waitFor} from '@testing-library/react';
import {describe,it,expect,vi,beforeEach} from 'vitest';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {AdminAuthProvider,useAdminAuth} from '../src/auth';
import {OperatorHome,WorkspacePage,WorkspaceTasks,CostsPage,TasksPage,BlockersPage,operatorMenus} from '../src/operator';
import * as api from '../src/api';
import {HumanNavigation} from '../src/human';
vi.mock('@tanstack/react-router',()=>({Link:({to,children}:{to:string;children:React.ReactNode})=><a href={to}>{children}</a>}));
vi.mock('../src/api',()=>({fetchRuntimeHealth:vi.fn(),fetchOperationsSummary:vi.fn(),fetchCostSummary:vi.fn(),fetchEvidencePackage:vi.fn(),fetchExecutionHistory:vi.fn(),fetchExecutionContext:vi.fn(),fetchModelStatus:vi.fn(),fetchSnapshot:vi.fn(),fetchChatHistory:vi.fn(),sendUserChat:vi.fn(),ChatSendError:class extends Error{}}));
const binding={plan_id:'plan-fixture',version:'v1',action:'CONTROLLED_FILE_WRITE'};
const pkg:api.EvidencePackage={package_id:'evp_sha256_'+'a'.repeat(64),generated_at:'2026-10-16',read_scope:'FIXTURE_ONLY',runtime_status:'NOT_VERIFIED',pass_allowed:false,evidence:[],criteria:[],blockers:[{id:'missing-proof',reason:'Evidence runtime belum lengkap'}]};
function mount(children:React.ReactNode,token=''){
 const client=new QueryClient({defaultOptions:{queries:{retry:false}}});
 render(<QueryClientProvider client={client}><AdminAuthProvider initialToken={token}>{children}</AdminAuthProvider></QueryClientProvider>);
 return client;
}
beforeEach(()=>{
 vi.resetAllMocks();
 vi.mocked(api.fetchRuntimeHealth).mockResolvedValue({status:'ok',service:'fixture-backend',version:'test',httpStatus:200});
 vi.mocked(api.fetchChatHistory).mockResolvedValue({session_id:'fixture',turns:[]});
 vi.mocked(api.fetchEvidencePackage).mockResolvedValue(pkg);
 vi.mocked(api.fetchModelStatus).mockResolvedValue({model:'fixture-local',provider:'ollama',revision:0,process_id:1,consistency_scope:'CURRENT_PROCESS_ONLY',availability:'NOT_VERIFIED',status:'NOT_VERIFIED',selection_enabled:false,selection_source:'BOOTSTRAP',last_request:null});
 vi.mocked(api.fetchExecutionHistory).mockResolvedValue({decisions:[],executions:[],decision_audit:'VALIDATED_HASH_CHAIN',execution_audit:'LOCAL_PERSISTED_LOG'});
 vi.mocked(api.fetchExecutionContext).mockResolvedValue({change_id:'fixture-task',objective:'Periksa hasil',expected_change:'hasil',target_files:[],operation:'write',plan_binding:binding,risk:'LOW',tests_required:[],rollback:'restore',checked_at:'2026-10-16',source:'fixture'});
 vi.mocked(api.fetchSnapshot).mockRejectedValue(new Error('Snapshot offline'));
});
describe('Operator contract boundaries',()=>{
 it('filters only loaded backend tasks and reports empty search without dispatch',async()=>{
  vi.mocked(api.fetchOperationsSummary).mockResolvedValue({scope:'TEST_ONLY',source:'fixture',pending_work:1,pending_review:0,reason:null,checked_at:'2026-10-19',tasks:[{id:'PIAK-03',objective:'Tinjau evidence',status:'HOLD',updated_at:'2026-10-19',source:'fixture'}]});
  mount(<WorkspaceTasks/>,'test-only');
  await screen.findByText('PIAK-03');
  fireEvent.change(screen.getByRole('searchbox'),{target:{value:'tidak-cocok'}});
  expect(screen.getByText('Tidak ada tugas yang cocok dalam cakupan yang dibaca.')).toBeInTheDocument();
  expect(screen.queryByText('PIAK-03')).toBeNull();
  expect(api.fetchOperationsSummary).toHaveBeenCalledTimes(1);
  expect(api.sendUserChat).not.toHaveBeenCalled();
 });
 it('opens the existing Chat route from human navigation',()=>{
  mount(<HumanNavigation/>);
  expect(screen.getByRole('link',{name:'Chat'})).toHaveAttribute('href','/ui');
 });
 it('reads authenticated ledger amounts and distinguishes budget from provider balance',async()=>{
  vi.mocked(api.fetchCostSummary).mockResolvedValue({status:'AVAILABLE',source:'CostLedger',reason:'Token belum dicatat ledger.',checked_at:'2026-10-16',
   actual_usd:'0.01',reserved_usd:'0.03',remaining_budget_usd:'0.96',budget_usd:'1.00',per_request_cap_usd:'0.10',
   period:{scope:'LEDGER_LIFETIME',start:null,end:null},history:[]});
  mount(<CostsPage/>,'cost-fixture');
  expect(await screen.findByText('USD 0.96')).toBeInTheDocument();
  expect(api.fetchCostSummary).toHaveBeenCalledWith('cost-fixture');
  expect(screen.getByText(/Sisa anggaran ledger bukan saldo OpenRouter/)).toBeInTheDocument();
 });
 it('has four menu destinations and four exact operator cards without fabricated totals',async()=>{
  expect(operatorMenus).toHaveLength(4);expect(new Set(operatorMenus.map(([to])=>to)).size).toBe(4);
  mount(<OperatorHome/>);
  for(const name of ['Apa yang sedang dikerjakan?','Apa masalahnya?','Apa yang perlu saya setujui?','Berapa biayanya?'])expect(screen.getByRole('heading',{name})).toBeInTheDocument();
  expect(await screen.findByText(/1 blocker dalam paket/)).toBeInTheDocument();
  expect(screen.getByText(/jumlah tugas aktif dan progres global belum disediakan/)).toBeInTheDocument();
  expect(api.fetchExecutionHistory).not.toHaveBeenCalled();
 });
 it('provides existing Chat in Workspace without enabling autonomous task execution',async()=>{
  mount(<WorkspacePage/>);
  fireEvent.click(screen.getByRole('tab',{name:'Chat V1'}));
  expect(screen.getByLabelText('Pertanyaan Anda')).toBeEnabled();
  expect(screen.getByRole('tab',{name:'Aktivitas tugas'})).toBeInTheDocument();
  expect(screen.queryByRole('button',{name:'Kirim tugas'})).toBeNull();
  await screen.findByText('Ollama · fixture-local');
  expect(api.sendUserChat).not.toHaveBeenCalled();
  expect(api.fetchExecutionContext).not.toHaveBeenCalled();
 });
 it('reads model status only and keeps all ledger values unavailable',async()=>{
  mount(<CostsPage/>);await screen.findByText(/Provider: ollama/);
  expect(screen.getAllByText('Belum tersedia melalui API')).toHaveLength(5);
  expect(api.fetchModelStatus).toHaveBeenCalledTimes(1);
  expect(api.fetchExecutionHistory).not.toHaveBeenCalled();
 });
 it('shows authorized backend task results and rejects old cached data after credential changes',async()=>{
  function Token(){const {setToken}=useAdminAuth();return <button onClick={()=>setToken('rejected-fixture')}>Ganti token</button>}
  const client=mount(<><Token/><TasksPage/></>,'valid-fixture');
  await screen.findByText(/fixture-task/);
  vi.mocked(api.fetchExecutionContext).mockRejectedValue(new Error('Akses ditolak'));
  vi.mocked(api.fetchExecutionHistory).mockRejectedValue(new Error('History ditolak'));
  fireEvent.click(screen.getByRole('button',{name:'Ganti token'}));
  await screen.findByText('Akses ditolak');
  expect(screen.queryByText(/fixture-task/)).toBeNull();
  expect(JSON.stringify(client.getQueryCache().getAll().map(q=>q.queryKey))).not.toContain('valid-fixture');
 });
 it('preserves blocker provenance and recovers from failed package reads',async()=>{
  vi.mocked(api.fetchEvidencePackage).mockRejectedValueOnce(new Error('Paket offline'));
  mount(<BlockersPage/>);await screen.findByText('Paket offline');
  const buttons=screen.getAllByRole('button',{name:'Coba lagi'});fireEvent.click(buttons[buttons.length-1]);
  await waitFor(()=>expect(screen.getByText('Evidence runtime belum lengkap')).toBeInTheDocument());
  expect(screen.getByText(/Penyebab belum diketahui; alasan backend/)).toBeInTheDocument();
  expect(screen.getByText('/v1/control-plane/evidence-package')).toBeInTheDocument();
 });
});

