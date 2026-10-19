import {render,screen,fireEvent,waitFor} from '@testing-library/react';
import {vi,it,expect,beforeEach} from 'vitest';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {SettingsPage} from '../src/settings';
import {AdminAuthProvider} from '../src/auth';
import * as api from '../src/api';
vi.mock('@tanstack/react-router',()=>({Link:({to,children}:{to:string;children:React.ReactNode})=><a href={to}>{children}</a>}));
vi.mock('../src/api',()=>({fetchModelStatus:vi.fn(),fetchKnowledgePipelineStatus:vi.fn(),fetchRuntimeHealth:vi.fn(),fetchAvailableModels:vi.fn(),selectOperatorModel:vi.fn()}));
function mount(token=''){render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><AdminAuthProvider initialToken={token}><SettingsPage/></AdminAuthProvider></QueryClientProvider>)}
beforeEach(()=>{
 vi.resetAllMocks();
 vi.mocked(api.fetchModelStatus).mockResolvedValue({model:'fixture',provider:'ollama',revision:0,process_id:1,consistency_scope:'CURRENT_PROCESS_ONLY',availability:'NOT_VERIFIED',status:'NOT_VERIFIED',selection_enabled:true,selection_source:'BOOTSTRAP',last_request:null});
 vi.mocked(api.fetchRuntimeHealth).mockResolvedValue({status:'ok',service:'nusantara-core',version:'0.1.0',httpStatus:200});
 vi.mocked(api.fetchKnowledgePipelineStatus).mockResolvedValue({source:'fixture',database:'fixture.db',documents_indexed:7,pipeline_ready_documents:3,watch:{enabled:false,folder:'inbox',updated_at:'now'},runs:[],checked_at:'now'});
});
it('reads health without credentials and keeps privileged knowledge gated',async()=>{
 mount();expect(await screen.findByText(/nusantara-core: ok/)).toBeInTheDocument();
 expect(api.fetchKnowledgePipelineStatus).not.toHaveBeenCalled();
 expect(screen.getByRole('button',{name:'Muat model tersedia'})).toBeDisabled();
});
it('shows actual API values and refreshes knowledge without uploading or changing models',async()=>{
 mount('fixture-token');expect(await screen.findByText('Dokumen terindeks: 7')).toBeInTheDocument();
 expect(screen.getByText('Dokumen pipeline siap: 3')).toBeInTheDocument();
 fireEvent.click(screen.getByRole('button',{name:'Perbarui Knowledge'}));
 expect(api.selectOperatorModel).not.toHaveBeenCalled();
 expect(api.fetchKnowledgePipelineStatus).toHaveBeenCalledWith('fixture-token');
});
it('does not substitute zero or PASS when knowledge fails',async()=>{
 vi.mocked(api.fetchKnowledgePipelineStatus).mockRejectedValue(new Error('Knowledge offline'));
 mount('fixture-token');expect(await screen.findByText('Knowledge offline')).toBeInTheDocument();
 expect(screen.queryByText('Dokumen terindeks: 0')).toBeNull();
});
it('shows the HTTP result and loading state for a manual health check',async()=>{
 const success={status:'ok',service:'nusantara-core',version:'0.1.0',httpStatus:200} as Awaited<ReturnType<typeof api.fetchRuntimeHealth>>;
 let finishRefresh:(value:typeof success)=>void=()=>{};
 const refresh=new Promise<typeof success>(resolve=>{finishRefresh=resolve;});
 vi.mocked(api.fetchRuntimeHealth).mockResolvedValueOnce(success).mockReturnValueOnce(refresh);
 mount();
 expect(await screen.findByText('GET /health - HTTP 200')).toBeInTheDocument();
 fireEvent.click(screen.getByRole('button',{name:'Periksa health'}));
 await waitFor(()=>expect(screen.getByRole('button',{name:'Memeriksa…'})).toBeDisabled());
 finishRefresh(success);
 expect(await screen.findByRole('button',{name:'Periksa health'})).toBeEnabled();
});
it('announces a refresh in progress in the health panel',async()=>{
 const success={status:'ok',service:'nusantara-core',version:'0.1.0',httpStatus:200} as Awaited<ReturnType<typeof api.fetchRuntimeHealth>>;
 let finishRefresh:(value:typeof success)=>void=()=>{};
 const refresh=new Promise<typeof success>(resolve=>{finishRefresh=resolve;});
 vi.mocked(api.fetchRuntimeHealth).mockResolvedValueOnce(success).mockReturnValueOnce(refresh);
 mount();
 expect(await screen.findByText('GET /health - HTTP 200')).toBeInTheDocument();
 fireEvent.click(screen.getByRole('button',{name:'Periksa health'}));
 try{
  expect(await screen.findByRole('status')).toHaveTextContent('Memeriksa GET /health pada Backend…');
  expect(screen.getByRole('button',{name:'Memeriksa…'})).toBeDisabled();
 }
 finally{finishRefresh(success);}
});
it('updates the last-check time when the same healthy response is returned again',async()=>{
 const success={status:'ok',service:'nusantara-core',version:'0.1.0',httpStatus:200} as Awaited<ReturnType<typeof api.fetchRuntimeHealth>>;
 vi.mocked(api.fetchRuntimeHealth).mockResolvedValue(success);
 mount();
 expect(await screen.findByText('GET /health - HTTP 200')).toBeInTheDocument();
 const firstCheckedAt=await screen.findByText(/Pemeriksaan terakhir:/);
 const firstValue=firstCheckedAt.textContent;
 await new Promise(resolve=>setTimeout(resolve,5));
 fireEvent.click(screen.getByRole('button',{name:'Periksa health'}));
 await waitFor(()=>expect(screen.getByText(/Pemeriksaan terakhir:/).textContent).not.toBe(firstValue));
 expect(api.fetchRuntimeHealth).toHaveBeenCalledTimes(2);
 expect(screen.getByText('GET /health - HTTP 200')).toBeInTheDocument();
});
it('replaces stale health success with a clear HTTP error after refresh fails',async()=>{
 const success={status:'ok',service:'nusantara-core',version:'0.1.0',httpStatus:200} as Awaited<ReturnType<typeof api.fetchRuntimeHealth>>;
 vi.mocked(api.fetchRuntimeHealth).mockResolvedValueOnce(success).mockRejectedValueOnce(new Error('GET /health gagal (HTTP 503).'));
 mount();
 expect(await screen.findByText('GET /health - HTTP 200')).toBeInTheDocument();
 const firstCheckedAt=screen.getByText(/Pemeriksaan terakhir:/).textContent;
 await new Promise(resolve=>setTimeout(resolve,5));
 fireEvent.click(screen.getByRole('button',{name:'Periksa health'}));
 expect(await screen.findByRole('alert')).toHaveTextContent('GET /health gagal (HTTP 503).');
 await waitFor(()=>expect(screen.getByText(/Pemeriksaan terakhir:/).textContent).not.toBe(firstCheckedAt));
 expect(screen.queryByText('GET /health - HTTP 200')).toBeNull();
 expect(screen.queryByText(/nusantara-core: ok/)).toBeNull();
});
