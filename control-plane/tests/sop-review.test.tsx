import {render,screen,fireEvent,waitFor,cleanup} from '@testing-library/react';
import {afterEach,beforeEach,expect,it,vi} from 'vitest';
import {SOPReviewPanel} from '../src/sop-review';
vi.mock('@tanstack/react-router',()=>({Link:({to,children,onClick}:{to:string;children:React.ReactNode;onClick?:()=>void})=><a href={to} onClick={e=>{e.preventDefault();onClick?.();}}>{children}</a>}));

let state:any;
let fail=false;
let sourceFail=false;
beforeEach(()=>{
  fail=false;
  sourceFail=false;
  state={document_id:'SOP-1',title:'PERMOHONAN DATA PRIBADI',version_id:'a'.repeat(64),status:'Menunggu pemeriksaan isi',source_available:true,source_type:'.pdf',text:'Surat Permohonan',pages:[],content_ok:false,can_approve:false,problems:[],events:[],trials:[],required_cases:['requirements','procedure','time_cost','followup','missing']};
  vi.stubGlobal('fetch',vi.fn(async(_url:string,options?:RequestInit)=>{
    if(fail&&options?.method==='POST')return {ok:false,status:500,json:async()=>({detail:'Penyimpanan gagal'})};
    if(String(_url).includes('/source?'))return sourceFail?{ok:false,status:503,json:async()=>({detail:'Sumber belum tersedia'})}:{ok:true,blob:async()=>new Blob(['PDF'],{type:'application/pdf'})};
    if(options?.method==='POST')state={...state,content_ok:true,status:'Isi sudah diperiksa'};
    return {ok:true,json:async()=>state};
  }));
  URL.createObjectURL=vi.fn(()=> 'blob:test');URL.revokeObjectURL=vi.fn();
});
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
it('hands an operator trial to the main chat without approving the SOP',async()=>{
  sessionStorage.clear();state.extraction={status:'COMPLETE'};
  render(<SOPReviewPanel documentId="SOP-1" token="fixture"/>);
  fireEvent.click(await screen.findByRole('link',{name:'Uji di chat utama'}));
  expect(sessionStorage.getItem('nusantara-chat-document-pending')).toBe('SOP-1');
  expect(sessionStorage.getItem('nusantara-chat-sop-version-pending')).toBe('a'.repeat(64));
  expect(state.content_ok).toBe(false);
  sessionStorage.clear();
});
it('compares Docling partial text and PDF and keeps chat blocked until complete without approving content',async()=>{
  state.extraction={status:'PARTIAL',error:'Tabel perlu pemeriksaan'};
  state.extracted_blocks=[{block_id:'#/texts/0',type:'text',content:'Surat Permohonan',page_numbers:[1]}];
  render(<SOPReviewPanel documentId="SOP-1" token="fixture"/>);
  await screen.findByText('PERMOHONAN DATA PRIBADI');
  expect(screen.getByRole('button',{name:'Coba chat SOP ini'})).toBeDisabled();
  fireEvent.click(screen.getByRole('button',{name:'Periksa isi'}));
  await screen.findByTitle('PDF asli SOP');
  expect(screen.getByText('Surat Permohonan')).toBeVisible();
  expect(screen.getByText('Halaman 1')).toBeVisible();
  expect(screen.getByText(/Masalah pembacaan SOP: Tabel perlu pemeriksaan/)).toBeVisible();
  state.extraction={status:'COMPLETE'};
  fireEvent.click(screen.getByRole('button',{name:'Muat ulang pemeriksaan'}));
  await waitFor(()=>expect(screen.getByRole('button',{name:'Coba chat SOP ini'})).toBeEnabled());
  expect(state.content_ok).toBe(false);
  expect(screen.getByRole('button',{name:'Setujui untuk digunakan'})).toBeDisabled();
});
it('requires notes and releases busy state after a failed write',async()=>{
  render(<SOPReviewPanel documentId="SOP-1" token="fixture"/>);
  fireEvent.click(await screen.findByRole('button',{name:'Periksa isi'}));
  fireEvent.click(screen.getByRole('button',{name:'Laporkan kesalahan'}));
  expect(screen.getByRole('button',{name:'Simpan catatan'})).toBeDisabled();
  fireEvent.change(screen.getByLabelText('Catatan wajib'),{target:{value:'Teks keliru'}});
  fail=true;fireEvent.click(screen.getByRole('button',{name:'Simpan catatan'}));
  await screen.findByRole('alert');
  await waitFor(()=>expect(screen.getByRole('button',{name:'Simpan catatan'})).toBeEnabled());
});
it('ends source loading on failure and offers a working retry',async()=>{
  sourceFail=true;
  render(<SOPReviewPanel documentId="SOP-1" token="fixture"/>);
  fireEvent.click(await screen.findByRole('button',{name:'Periksa isi'}));
  await screen.findByText('Sumber belum tersedia');
  expect(screen.queryByText('Memuat file sumber...')).not.toBeInTheDocument();
  sourceFail=false;fireEvent.click(screen.getByRole('button',{name:'Coba muat sumber lagi'}));
  await screen.findByTitle('PDF asli SOP');
});
