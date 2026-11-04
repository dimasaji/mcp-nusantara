import {render,screen,fireEvent,waitFor,cleanup} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import {SOPReviewPanel} from '../src/sop-review';
vi.mock('@tanstack/react-router',()=>({Link:({to,children,onClick}:{to:string;children:React.ReactNode;onClick?:()=>void})=><a href={to} onClick={e=>{e.preventDefault();onClick?.();}}>{children}</a>}));
afterEach(()=>{cleanup();vi.unstubAllGlobals();sessionStorage.clear();});
it('prepares system findings and hands the approved version directly to Chat without trial rating work',async()=>{
  const state={document_id:'DOC-TEST',title:'LAYANAN CONTOH',version_id:'a'.repeat(64),material_binding:'c'.repeat(64),status:'Aktif',operator_status:'Aktif untuk Chat',source_available:true,source_type:'.txt',text:'Surat Pengantar',pages:[],content_ok:true,can_approve:true,problems:[],events:[],trials:[],required_cases:['time_cost'],approval_requirements:[{key:'case:time_cost',satisfied:false}],system_summary:{passed:true,primary_issue:null,checks:[],scenarios:[]}};
  vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,json:async()=>state,blob:async()=>new Blob(['source'])})));
  URL.createObjectURL=vi.fn(()=> 'blob:fixture');URL.revokeObjectURL=vi.fn();
  render(<SOPReviewPanel documentId="DOC-TEST" token="fixture"/>);
  expect(await screen.findByText('Aktif untuk Chat')).toBeVisible();
  await waitFor(()=>expect(vi.mocked(fetch).mock.calls.some(([url,options])=>String(url).endsWith('/prepare')&&options?.method==='POST')).toBe(true));
  expect(screen.queryByText(/nilai ulang secara manual/i)).toBeNull();
  expect(screen.queryByRole('button',{name:'Jawaban sesuai'})).toBeNull();
  fireEvent.click(screen.getByRole('link',{name:'Coba chat SOP ini'}));
  expect(sessionStorage.getItem('nusantara-chat-document-pending')).toBe('DOC-TEST');
  expect(sessionStorage.getItem('nusantara-chat-approved-version-pending')).toBe('a'.repeat(64));
  expect(sessionStorage.getItem('nusantara-chat-sop-version-pending')).toBeNull();
});


it('sends approved handoff version and blocks a source handoff without operator access',async()=>{
  const {UserChat}=await import('../src/assistant');
  sessionStorage.setItem('nusantara-chat-document-pending','DOC-TEST');
  sessionStorage.setItem('nusantara-chat-approved-version-pending','a'.repeat(64));
  const calls:Record<string,unknown>[]=[];
  vi.stubGlobal('fetch',vi.fn(async(url:string,options?:RequestInit)=>({ok:true,json:async()=>{
    if(url.includes('/reviews/'))return {title:'LAYANAN CONTOH',status:'Aktif',version_id:'a'.repeat(64)};
    if(url.includes('/history'))return {turns:[]};
    if(url==='/v1/chat'){calls.push(JSON.parse(String(options?.body)));return {response:'Surat Pengantar',evidence:[],grounding:{reason:'grounded'},trust:{requires_human:false},timestamp:'fixture'};}
    return {provider:'ollama',model:'fixture'};
  }})));
  const view=render(<UserChat token="fixture"/>);
  await screen.findByText(/Dokumen aktif: LAYANAN CONTOH/);
  fireEvent.change(screen.getByLabelText('Pertanyaan Anda'),{target:{value:'Apa kelengkapannya?'}});
  fireEvent.click(screen.getByRole('button',{name:'Kirim pertanyaan'}));
  await waitFor(()=>expect(calls).toHaveLength(1));
  expect(calls[0]).toMatchObject({document_ids:['DOC-TEST'],document_version:'a'.repeat(64)});
  expect(calls[0]).not.toHaveProperty('sop_case');
  view.unmount();
  sessionStorage.setItem('nusantara-chat-document-pending','DOC-TEST');
  render(<UserChat/>);
  expect(await screen.findByText(/Sumber SOP belum tersambung/)).toBeVisible();
  fireEvent.change(screen.getByLabelText('Pertanyaan Anda'),{target:{value:'Apa kelengkapannya?'}});
  expect(screen.getByRole('button',{name:'Kirim pertanyaan'})).toBeDisabled();
});


it('keeps PDF tables and metadata controls after backend preparation',async()=>{
  const detail={document_id:'PDF-TEST',title:'LAYANAN CONTOH',version_id:'a'.repeat(64),material_binding:'c'.repeat(64),status:'Siap disetujui',source_available:true,source_type:'.pdf',text:'',pages:[{page:1,start:0,end:10}],content_ok:false,can_approve:true,problems:[],events:[],trials:[],required_cases:[],approval_requirements:[],extraction:{status:'COMPLETE'},extracted_blocks:[{block_id:'table',type:'table',content:'',page_numbers:[1],table_data:{headers:['Kelengkapan'],rows:[['Surat Pengantar']]}}]};
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>{
    if(url.includes('/source?'))return {ok:true,blob:async()=>new Blob(['PDF'])};
    if(url.endsWith('/prepare')){const {extraction,extracted_blocks,...prepared}=detail;return {ok:true,json:async()=>prepared};}
    return {ok:true,json:async()=>detail};
  }));
  URL.createObjectURL=vi.fn(()=> 'blob:fixture');URL.revokeObjectURL=vi.fn();
  render(<SOPReviewPanel documentId="PDF-TEST" token="fixture"/>);
  expect(await screen.findByRole('table',{name:'Tabel SOP halaman 1'})).toHaveTextContent('Surat Pengantar');
  expect(screen.getByLabelText('Judul resmi SOP',{exact:true})).toBeEnabled();
});
