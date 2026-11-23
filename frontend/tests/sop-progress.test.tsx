import {render,screen,fireEvent,waitFor,within,act} from '@testing-library/react';
import {beforeEach,describe,it,expect,vi} from 'vitest';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {AdminAuthProvider,useAdminAuth} from '../src/auth';
import {KnowledgeOperationsPage} from '../src/overview';
import {SOPProgressOverview,SOPProgressPanel,reviewSelectionKey} from '../src/sop-progress';
import * as api from '../src/api';
vi.mock('@tanstack/react-router',()=>({Link:({to,children,onClick}:{to:string;children:React.ReactNode;onClick?:()=>void})=><a href={to} onClick={e=>{e.preventDefault();onClick?.();}}>{children}</a>}));
vi.mock('../src/api',async original=>({...await original<typeof import('../src/api')>(),fetchKnowledgePipelineStatus:vi.fn(),retryKnowledgeDocument:vi.fn()}));
const data:api.KnowledgePipelineStatus={source:'fixture',database:'fixture.db',documents_indexed:2,pipeline_ready_documents:2,checked_at:'2026-11-08T00:00:00Z',watch:{enabled:false,folder:'inbox',updated_at:''},runs:[],
 sop_summary:{scope:'CURRENT_KNOWLEDGE',total:2,counts:{ACTIVE:1,QUEUED:0,PROCESSING:1,REVIEW_REQUIRED:0,APPROVAL_REQUIRED:0,BLOCKED:0,UNKNOWN:0},failed_sources:[{run_id:'failed-run',filename:'scan.pdf',reason:'OCR indisponible',retryable:true}]},
 documents:[
 {document_id:'akta',title:'Akta Kelahiran',status:'READY',chunks_count:3,source_verification:'NOT_VERIFIED',updated_at:'',review_status:'Aktif',workflow:{state:'ACTIVE',version_id:'a'.repeat(64),stages:{source:'SUCCEEDED',extraction:'SUCCEEDED',cleaning:'UNKNOWN',indexing:'SUCCEEDED',review:'SUCCEEDED',approval:'SUCCEEDED',availability:'SUCCEEDED'},extraction_status:'COMPLETE',cleaning_profile:null,reason:'Aktif',next_action:'chat'}},
 {document_id:'nik',title:'Layanan NIK',status:'READY',chunks_count:2,source_verification:'NOT_VERIFIED',updated_at:'',review_status:'Menunggu ekstraksi',workflow:{state:'PROCESSING',version_id:'b'.repeat(64),stages:{extraction:'RUNNING',cleaning:'WAITING'},extraction_status:'PROCESSING',cleaning_profile:null,reason:'Menunggu ekstraksi',next_action:'wait'}},
 ]};
function mount(children:React.ReactNode,token=''){
 const client=new QueryClient({defaultOptions:{queries:{retry:false}}});
 render(<QueryClientProvider client={client}><AdminAuthProvider initialToken={token}>{children}</AdminAuthProvider></QueryClientProvider>);
 return client;
}
beforeEach(()=>{vi.resetAllMocks();sessionStorage.clear();vi.mocked(api.fetchKnowledgePipelineStatus).mockResolvedValue(data);});
describe('SOP current progress',()=>{
 it('filters documents, preserves unknown cleaning and scopes active chat',()=>{
  mount(<SOPProgressPanel data={data}/>);
  expect(screen.getByText('Sedang diproses')).toBeInTheDocument();
  fireEvent.change(screen.getByRole('searchbox'),{target:{value:'Akta'}});
  expect(screen.queryByText('Layanan NIK')).toBeNull();
  const row=screen.getByText('Akta Kelahiran').closest('tr')!;
  fireEvent.click(within(row).getByText('Detail tahapan'));
  expect(within(row).getByText('Belum diverifikasi')).toBeInTheDocument();
  sessionStorage.setItem('nusantara-chat-sop-version-pending','old-trial');
  fireEvent.click(within(row).getByRole('link',{name:'Buka chat'}));
  expect(sessionStorage.getItem('nusantara-chat-document-pending')).toBe('akta');
  expect(sessionStorage.getItem('nusantara-chat-sop-version-pending')).toBeNull();
 });
 it('hands off the exact review document and reuses existing retry',()=>{
  const retry=vi.fn();mount(<SOPProgressPanel data={data} onRetry={retry}/>);
  fireEvent.click(screen.getByRole('link',{name:'Periksa dokumen'}));
  expect(sessionStorage.getItem(reviewSelectionKey)).toBe('nik');
  fireEvent.click(screen.getByText('Percobaan impor yang masih gagal (1 sumber)'));
  fireEvent.click(screen.getByRole('button',{name:'Coba proses lagi'}));
  expect(retry).toHaveBeenCalledWith('failed-run');
 });
 it('does not infer progress from an older backend',()=>{
  mount(<SOPProgressPanel data={{...data,sop_summary:undefined}}/>);
  expect(screen.getByText(/Ringkasan SOP belum disediakan backend/)).toBeInTheDocument();
  expect(screen.queryByText('Akta Kelahiran')).toBeNull();
 });
 it('clears source data after credentials change and recovers on retry',async()=>{
  function Change(){const {setToken}=useAdminAuth();return <button onClick={()=>setToken('denied')}>Ganti akses</button>}
  const client=mount(<><Change/><SOPProgressOverview/></>,'operator');
  await screen.findByText('Akta Kelahiran');
  vi.mocked(api.fetchKnowledgePipelineStatus).mockRejectedValue(new Error('Akses ditolak'));
  fireEvent.click(screen.getByText('Ganti akses'));
  await screen.findByText(/Progres SOP belum dapat dibaca: Akses ditolak/);
  expect(screen.queryByText('Akta Kelahiran')).toBeNull();
  expect(JSON.stringify(client.getQueryCache().getAll().map(q=>q.queryKey))).not.toContain('operator');
  vi.mocked(api.fetchKnowledgePipelineStatus).mockResolvedValue(data);
  fireEvent.click(screen.getByRole('button',{name:'Coba lagi'}));
  await waitFor(()=>expect(screen.getByText('Akta Kelahiran')).toBeInTheDocument());
 });
 it('does not request private inventory without a token',()=>{
  mount(<SOPProgressOverview/>);
  expect(screen.getByText(/Masukkan token operator/)).toBeInTheDocument();
  expect(api.fetchKnowledgePipelineStatus).not.toHaveBeenCalled();
 });
 it('hides late retry feedback from an earlier authorization context',async()=>{
  let rejectRetry!:(reason:Error)=>void;
  vi.mocked(api.retryKnowledgeDocument).mockImplementation(()=>new Promise((_resolve,reject)=>{rejectRetry=reject;}));
  function Change(){const {setToken}=useAdminAuth();return <button onClick={()=>setToken('other')}>Ganti konteks</button>}
  mount(<><Change/><KnowledgeOperationsPage/></>,'operator');
  await screen.findByRole('heading',{name:'Progres seluruh SOP'});
  fireEvent.click(screen.getByText('Percobaan impor yang masih gagal (1 sumber)'));
  fireEvent.click(screen.getByRole('button',{name:'Coba proses lagi'}));
  await waitFor(()=>expect(api.retryKnowledgeDocument).toHaveBeenCalledWith('failed-run','operator'));
  fireEvent.click(screen.getByRole('button',{name:'Ganti konteks'}));
  await act(async()=>{rejectRetry(new Error('PRIOR_PRIVATE_REASON'));});
  expect(screen.queryByText('PRIOR_PRIVATE_REASON')).toBeNull();
 });
});
