import {render,screen,fireEvent,waitFor,within} from '@testing-library/react';
import {createMemoryHistory,createRootRoute,createRoute,createRouter,RouterProvider} from '@tanstack/react-router';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {afterEach,beforeEach,describe,it,expect,vi} from 'vitest';
import {AdminAuthProvider} from '../src/auth';
import {KnowledgeOperationsPage} from '../src/overview';
import {webcrypto} from 'node:crypto';

const status={source:'Chat RAG SQLite store',database:'data/knowledge/nusantara_knowledge.db',documents_indexed:2,pipeline_ready_documents:1,
  watch:{enabled:false,folder:'data/knowledge/inbox',updated_at:''},checked_at:'2026-10-15T00:00:00Z',runs:[
    {run_id:'kpr_ready',filename:'manual.txt',source_sha256:'a'.repeat(64),status:'READY',reason:null,document_id:'DOC-SHA256-a',created_at:'2026-10-15T00:00:00Z'},
    {run_id:'kpr_failed',filename:'scan.pdf',source_sha256:'b'.repeat(64),status:'FAILED',reason:'OCR_NOT_AVAILABLE_FOR_SCANNED_PDF',document_id:null,created_at:'2026-10-14T00:00:00Z'}]};

function renderPage(token='operator-test'){
  const root=createRootRoute({component:KnowledgeOperationsPage});
  const route=createRoute({getParentRoute:()=>root,path:'/knowledge',component:KnowledgeOperationsPage});
  const router=createRouter({routeTree:root.addChildren([route]),history:createMemoryHistory({initialEntries:['/knowledge']})});
  const client=new QueryClient({defaultOptions:{queries:{retry:false}}});
  return render(<QueryClientProvider client={client}><AdminAuthProvider initialToken={token}><RouterProvider router={router}/></AdminAuthProvider></QueryClientProvider>);
}

beforeEach(()=>{vi.stubGlobal('scrollTo',vi.fn());});
afterEach(()=>vi.unstubAllGlobals());
describe('general knowledge operations',()=>{
  it('opens chat with the selected document and clears an earlier trial version',async()=>{
    sessionStorage.clear();
    sessionStorage.setItem('nusantara-chat-sop-version-pending','b'.repeat(64));
    vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,status:200,json:async()=>({...status,documents:[{
      document_id:'approved-pdf',title:'PDF layanan',review_status:'Aktif',updated_at:''}]})})));
    renderPage();
    await screen.findByRole('heading',{name:'PDF layanan',level:2});
    fireEvent.click(screen.getByText('Tambahkan dokumen baru'));
    fireEvent.click(screen.getByRole('link',{name:'Buka Chat'}));
    expect(sessionStorage.getItem('nusantara-chat-document-pending')).toBe('approved-pdf');
    expect(sessionStorage.getItem('nusantara-chat-sop-version-pending')).toBeNull();
    sessionStorage.clear();
  });
  it('puts the stored SOP task first and keeps optional operations collapsed',async()=>{
    vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,status:200,json:async()=>({...status,documents:[{
      document_id:'official-pdf',title:'PERMOHONAN DATA PRIBADI',status:'READY',chunks_count:4,
      source_verification:'NOT_VERIFIED',updated_at:'',review_status:'Menunggu pemeriksaan isi'}]})})));
    renderPage();
    const task=await screen.findByRole('region',{name:'Dokumen yang diperiksa'});
    expect(within(task).getByRole('heading',{name:'PERMOHONAN DATA PRIBADI'})).toBeVisible();
    expect(within(task).getByRole('button',{name:'Periksa isi'})).toBeVisible();
    expect(screen.getByText('Dokumen sudah tersimpan. Anda tidak perlu mengunggah ulang.')).toBeVisible();
    for(const name of ['Tambahkan dokumen baru','Riwayat proses sebelumnya','Pengaturan dan informasi teknis']){
      expect(screen.getByText(name).closest('details')).not.toHaveAttribute('open');
    }
  });
  it('uses an existing matching file without uploading it again, including a renamed copy',async()=>{
    vi.stubGlobal('crypto',webcrypto);
    const fetch=vi.fn(async()=>({ok:true,status:200,json:async()=>({...status,documents:[{
      document_id:'existing-doc',title:'Dokumen tersedia',status:'READY',chunks_count:1,
      source_verification:'NOT_VERIFIED',updated_at:'',source_sha256:'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'}]})}));
    vi.stubGlobal('fetch',fetch);renderPage();
    fireEvent.click(await screen.findByText('Tambahkan dokumen baru'));
    const file=new File(['abc'],'nama-lain.txt');
    Object.defineProperty(file,'arrayBuffer',{value:async()=>new TextEncoder().encode('abc').buffer});
    fireEvent.change(await screen.findByLabelText('Pilih dokumen'),{target:{files:[file]}});
    await waitFor(()=>expect(screen.getByRole('button',{name:'Proses dan validasi'})).toBeEnabled());
    fireEvent.click(screen.getByRole('button',{name:'Proses dan validasi'}));
    expect(await screen.findByText('File identik sudah tersedia. Gunakan dokumen tersimpan; tidak perlu unggah ulang.')).toBeInTheDocument();
    expect(fetch.mock.calls.some(call=>(call as unknown as [unknown,RequestInit])[1]?.method==='POST')).toBe(false);
    fireEvent.click(screen.getByRole('link',{name:'Tanyakan dokumen tersimpan'}));
    expect(sessionStorage.getItem('nusantara-chat-document-pending')).toBe('existing-doc');
  });
  it('summarizes identical duplicate attempts while keeping failures and full history available',async()=>{
    const duplicate={...status.runs[0],filename:'SOP contoh.txt',status:'DUPLICATE',reason:'File identik sudah terindeks di Chat.'};
    const runs=[{...duplicate,run_id:'dup2'},{...duplicate,run_id:'dup1'},status.runs[1],status.runs[0]];
    vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,status:200,json:async()=>({...status,runs})})));
    renderPage();
    fireEvent.click(await screen.findByText('Riwayat proses sebelumnya'));
    const history=await screen.findByRole('region',{name:'History knowledge'});
    await waitFor(()=>expect(within(history).getAllByText('SOP contoh.txt')).toHaveLength(1));
    expect(within(history).getByText(/2 percobaan identik/)).toBeInTheDocument();
    expect(within(history).getByText('scan.pdf')).toBeInTheDocument();
    fireEvent.click(within(history).getByRole('button',{name:'Tampilkan semua catatan (4)'}));
    expect(within(history).getAllByText('SOP contoh.txt')).toHaveLength(2);
    expect(within(history).getByText('dup1')).toBeInTheDocument();
    expect(within(history).getByText('dup2')).toBeInTheDocument();
  });
  it('lets a direct visitor choose a file and authenticate on the same page before uploading',async()=>{
    const fetch=vi.fn(async(_path:RequestInfo|URL,init?:RequestInit)=>{
      const token=(init?.headers as Record<string,string>|undefined)?.['X-Admin-Token'];
      return token==='valid-operator'?{ok:true,status:200,json:async()=>init?.method==='POST'?{...status.runs[0],status:'READY'}:status}:
        {ok:false,status:403,json:async()=>({detail:'ADMIN_TOKEN_INVALID'})};
    });vi.stubGlobal('fetch',fetch);
    renderPage('');
    fireEvent.click(await screen.findByText('Tambahkan dokumen baru'));
    const picker=await screen.findByLabelText('Pilih dokumen');expect(picker).toBeEnabled();
    const file=new File(['Source for browser upload regression.'],'chosen.txt',{type:'text/plain'});
    Object.defineProperty(file,'arrayBuffer',{value:async()=>new ArrayBuffer(40)});
    fireEvent.change(picker,{target:{files:[file]}});
    expect(screen.getByText(/chosen.txt/)).toBeInTheDocument();
    expect(screen.getByRole('button',{name:'Proses dan validasi'})).toBeDisabled();
    fireEvent.change(screen.getByLabelText('Token operator',{exact:true}),{target:{value:'wrong-token'}});
    fireEvent.click(screen.getByRole('button',{name:'Verifikasi akses'}));
    expect((await screen.findAllByText(/Akses ditolak/)).length).toBeGreaterThan(0);
    expect(screen.getByText(/chosen.txt/)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Token operator',{exact:true}),{target:{value:'valid-operator'}});
    fireEvent.click(screen.getByRole('button',{name:'Verifikasi akses'}));
    await waitFor(()=>expect(screen.getByRole('button',{name:'Proses dan validasi'})).toBeEnabled());
    fireEvent.click(screen.getByRole('button',{name:'Proses dan validasi'}));
    expect(await screen.findByText(/Dokumen berhasil disimpan dan diproses/)).toBeInTheDocument();
    expect(fetch.mock.calls.filter(([,init])=>init?.method==='POST')).toHaveLength(1);
  });
  it('keeps a failed upload selected for retry and offers Chat after success',async()=>{
    let attempts=0;
    vi.stubGlobal('fetch',vi.fn(async(_input:RequestInfo|URL,init?:RequestInit)=>({ok:true,status:200,
      json:async()=>init?.method==='POST'?{...status.runs[0],status:++attempts===1?'FAILED':'READY',reason:attempts===1?'INDEXING_FAILED':null}:status})));
    renderPage();
    fireEvent.click(await screen.findByText('Tambahkan dokumen baru'));
    const input=await screen.findByLabelText('Pilih dokumen');
    const file=new File(['document content'],'manual.txt',{type:'text/plain'});
    Object.defineProperty(file,'arrayBuffer',{value:async()=>new ArrayBuffer(16)});
    fireEvent.change(input,{target:{files:[file]}});
    fireEvent.click(screen.getAllByRole('button',{name:'Proses dan validasi'})[0]);
    const retry=await screen.findByRole('button',{name:'Coba Lagi'});
    expect(retry).toBeEnabled();fireEvent.click(retry);
    expect(await screen.findByRole('link',{name:'Buka Chat'})).toHaveAttribute('href','/');
    expect(attempts).toBe(2);
  });
  it('shows real pipeline summary, failure reason and source authority boundary',async()=>{
    vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,status:200,json:async()=>status})));
    renderPage();
    expect(await screen.findByRole('heading',{name:'Pemeriksaan SOP'})).toBeInTheDocument();
    fireEvent.click(screen.getByText('Pengaturan dan informasi teknis'));
    fireEvent.click(screen.getByText('Riwayat proses sebelumnya'));
    expect(await screen.findByText('1 dokumen lulus pipeline')).toBeInTheDocument();
    expect(await screen.findByText('2 dokumen ada di index Chat')).toBeInTheDocument();
    expect(screen.getByText('scan.pdf')).toBeInTheDocument();
    expect(screen.getByText(/PDF tampaknya hasil pemindaian/)).toBeInTheDocument();
    expect(screen.getByText(/tidak mengesahkan otoritas atau menetapkan dokumen sebagai revisi resmi/)).toBeInTheDocument();
    expect(screen.queryByText(/PIAK-03/)).not.toBeInTheDocument();
    expect(screen.queryByRole('button',{name:'PASS'})).not.toBeInTheDocument();
  });

  it('activates the configured inbox with operator authentication and refreshes status',async()=>{
    const fetch=vi.fn(async(_input:RequestInfo|URL,init?:RequestInit)=>({ok:true,status:200,
      json:async()=>init?.method==='POST'?{enabled:true,folder:'data/knowledge/inbox',updated_at:'2026-10-15T00:01:00Z'}:status}));
    vi.stubGlobal('fetch',fetch);
    renderPage();
    fireEvent.click(await screen.findByText('Pengaturan dan informasi teknis'));
    fireEvent.click(await screen.findByRole('button',{name:'Aktifkan pemantauan'}));
    await waitFor(()=>expect(fetch).toHaveBeenCalledWith('/v1/knowledge/pipeline/watch?enabled=true',expect.objectContaining({method:'POST'})));
  });
});
