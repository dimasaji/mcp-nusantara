import {render,screen,fireEvent,waitFor} from '@testing-library/react';
import {createMemoryHistory,createRootRoute,createRoute,createRouter,RouterProvider} from '@tanstack/react-router';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {describe,it,expect,vi} from 'vitest';
import {AdminAuthProvider} from '../src/auth';
import {KnowledgeOperationsPage} from '../src/overview';

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

describe('general knowledge operations',()=>{
  it('lets a direct visitor choose a file and authenticate on the same page before uploading',async()=>{
    const fetch=vi.fn(async(_path:RequestInfo|URL,init?:RequestInit)=>{
      const token=(init?.headers as Record<string,string>|undefined)?.['X-Admin-Token'];
      return token==='valid-operator'?{ok:true,status:200,json:async()=>init?.method==='POST'?{...status.runs[0],status:'READY'}:status}:
        {ok:false,status:403,json:async()=>({detail:'ADMIN_TOKEN_INVALID'})};
    });vi.stubGlobal('fetch',fetch);
    renderPage('');
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
    expect(await screen.findByRole('heading',{name:'Dokumen dan pemantauan'})).toBeInTheDocument();
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
    fireEvent.click(await screen.findByRole('button',{name:'Aktifkan pemantauan'}));
    await waitFor(()=>expect(fetch).toHaveBeenCalledWith('/v1/knowledge/pipeline/watch?enabled=true',expect.objectContaining({method:'POST'})));
  });
});
