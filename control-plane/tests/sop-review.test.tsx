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
  state={document_id:'SOP-1',title:'PERMOHONAN DATA PRIBADI',version_id:'a'.repeat(64),status:'Menunggu pemeriksaan isi',source_available:true,source_type:'.pdf',text:'Surat Permohonan',pages:[],content_ok:false,can_approve:false,problems:[],events:[],trials:[],required_cases:['requirements','procedure','time_cost','followup','missing'],approval_requirements:[]};
  vi.stubGlobal('fetch',vi.fn(async(_url:string,options?:RequestInit)=>{
    if(fail&&options?.method==='POST')return {ok:false,status:500,json:async()=>({detail:'Penyimpanan gagal'})};
    if(String(_url).includes('/source?'))return sourceFail?{ok:false,status:503,json:async()=>({detail:'Sumber belum tersedia'})}:{ok:true,blob:async()=>new Blob(['PDF'],{type:'application/pdf'})};
    if(options?.method==='POST')state={...state,content_ok:true,status:'Isi sudah diperiksa'};
    return {ok:true,json:async()=>state};
  }));
  URL.createObjectURL=vi.fn(()=> 'blob:test');URL.revokeObjectURL=vi.fn();
});
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
it.each([
  ['Tolak dokumen','reject','Ditolak'],
  ['Tunda keputusan','defer','Ditunda'],
  ['Cabut dari Chat','revoke','Dicabut'],
])('saves %s with a reason and keeps its decision after remount',async(label,action,status)=>{
  state.status='Aktif';state.content_ok=true;state.can_approve=true;
  vi.stubGlobal('fetch',vi.fn(async(url:string,options?:RequestInit)=>{
    if(String(url).includes('/source?'))return {ok:true,blob:async()=>new Blob(['PDF'])};
    if(options?.method==='POST'){
      const body=JSON.parse(String(options.body));
      state={...state,status,publication_decision:{kind:body.action,note:body.note},events:[{event_id:'decision',kind:body.action,note:body.note,principal:'shared-admin-token',created_at:'2026-10-29'}]};
    }
    return {ok:true,json:async()=>state};
  }));
  render(<SOPReviewPanel documentId="SOP-1" token="fixture"/>);
  fireEvent.click(await screen.findByRole('button',{name:label}));
  expect(screen.getByRole('button',{name:'Simpan keputusan'})).toBeDisabled();
  fireEvent.change(screen.getByLabelText('Alasan keputusan'),{target:{value:'Periksa ulang isi dokumen'}});
  fireEvent.click(screen.getByRole('button',{name:'Simpan keputusan'}));
  await screen.findByText(status);
  const write=vi.mocked(fetch).mock.calls.find(([,options])=>options?.method==='POST');
  expect(JSON.parse(String(write?.[1]?.body))).toEqual({version_id:'a'.repeat(64),action,note:'Periksa ulang isi dokumen'});
  cleanup();render(<SOPReviewPanel documentId="SOP-1" token="fixture"/>);
  await screen.findByText(status);
  expect(screen.getByText('Alasan: Periksa ulang isi dokumen')).toBeVisible();
});
it('persists the content check after reload without approving the SOP',async()=>{
  render(<SOPReviewPanel documentId="SOP-1" token="fixture"/>);
  fireEvent.click(await screen.findByRole('button',{name:'Isi sudah sesuai'}));
  await screen.findByText(/Isi sudah Anda nyatakan sesuai/);
  expect(state.content_ok).toBe(true);
  expect(screen.getByRole('button',{name:'Setujui untuk digunakan'})).toBeDisabled();
  const write=vi.mocked(fetch).mock.calls.find(([,options])=>options?.method==='POST');
  expect(JSON.parse(String(write?.[1]?.body))).toMatchObject({version_id:'a'.repeat(64),action:'content_ok'});

  cleanup();
  render(<SOPReviewPanel documentId="SOP-1" token="fixture"/>);
  await screen.findByText(/Isi sudah Anda nyatakan sesuai/);
  expect(state.content_ok).toBe(true);
  expect(screen.getByRole('button',{name:'Setujui untuk digunakan'})).toBeDisabled();
});
it('shows revision differences without treating them as approval',async()=>{
  state.comparison={previous_version_id:'b'.repeat(64),version_id:'a'.repeat(64),changed_blocks:1,omitted_blocks:0,changes:[{block_id:'requirements',kind:'changed',pages:[1],before:'Surat Permohonan',after:'Surat Pengantar',excerpt_truncated:false}]};
  render(<SOPReviewPanel documentId="SOP-1" token="fixture"/>);
  fireEvent.click(await screen.findByText('Perubahan dari hasil baca sebelumnya'));
  expect(screen.getByText('Sebelumnya: Surat Permohonan')).toBeVisible();
  expect(screen.getByText('Sekarang: Surat Pengantar')).toBeVisible();
  expect(screen.getByRole('button',{name:'Setujui untuk digunakan'})).toBeDisabled();
});
it('shows the exact missing approval case and unverified shared-token rating origin',async()=>{
  state.status='Isi sudah diperiksa';state.content_ok=true;
  state.approval_requirements=[
    {key:'source_available',satisfied:true},
    {key:'extraction_complete',satisfied:true},
    {key:'content_checked',satisfied:true},
    {key:'case:requirements',satisfied:true},
    {key:'case:procedure',satisfied:true},
    {key:'case:time_cost',satisfied:true},
    {key:'case:followup',satisfied:true},
    {key:'case:missing',satisfied:false},
    {key:'all_trials_reviewed',satisfied:true},
    {key:'no_open_problems',satisfied:true},
  ];
  state.trials=['requirements','procedure','time_cost','followup'].map((case_id,i)=>({
    trial_id:`trial-${i}`,case_id,principal:'shared-admin-token',created_at:'2026-10-27T08:00:00Z',
    answer:{response:'Fixture answer',model:'fixture',evidence:[]},
    rating:{ok:true,principal:'shared-admin-token',created_at:'2026-10-27T09:00:00Z'},
  }));
  render(<SOPReviewPanel documentId="SOP-1" token="fixture"/>);
  const prerequisites=await screen.findByRole('region',{name:'Syarat persetujuan'});
  expect(prerequisites).toHaveTextContent(/Belum terpenuhi:.*Informasi yang tidak ada/);
  expect(prerequisites).toHaveTextContent('4 rating tersimpan memakai token admin bersama; identitas penilainya tidak tercatat.');
  expect(screen.getByRole('button',{name:'Setujui untuk digunakan'})).toBeDisabled();
});
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
  fireEvent.click(await screen.findByRole('button',{name:'Laporkan kesalahan'}));
  expect(screen.getByLabelText('Catatan wajib')).toHaveFocus();
  expect(screen.getByRole('button',{name:'Simpan catatan'})).toBeDisabled();
  fireEvent.change(screen.getByLabelText('Catatan wajib'),{target:{value:'Teks keliru'}});
  fail=true;fireEvent.click(screen.getByRole('button',{name:'Simpan catatan'}));
  await screen.findByRole('alert');
  await waitFor(()=>expect(screen.getByRole('button',{name:'Simpan catatan'})).toBeEnabled());
});
it('saves a correction category with the operator problem',async()=>{
  render(<SOPReviewPanel documentId="SOP-1" token="fixture"/>);
  fireEvent.click(await screen.findByRole('button',{name:'Laporkan kesalahan'}));
  fireEvent.change(screen.getByLabelText('Kategori masalah'),{target:{value:'extraction'}});
  fireEvent.change(screen.getByLabelText('Catatan wajib'),{target:{value:'Tabel belum terbaca'}});
  fireEvent.click(screen.getByRole('button',{name:'Simpan catatan'}));
  await waitFor(()=>expect(screen.queryByRole('region',{name:'Catatan masalah'})).not.toBeInTheDocument());
  const write=vi.mocked(fetch).mock.calls.find(([,options])=>options?.method==='POST');
  expect(JSON.parse(String(write?.[1]?.body))).toMatchObject({action:'problem',category:'extraction',note:'Tabel belum terbaca'});
});
it('explains a missing extracted page instead of leaving a blank comparison',async()=>{
  state.extraction={status:'PARTIAL'};state.pages=[{page:1,start:0,end:20},{page:2,start:21,end:40}];
  state.extracted_blocks=[{block_id:'one',type:'text',content:'Isi halaman satu',page_numbers:[1]}];
  render(<SOPReviewPanel documentId="SOP-1" token="fixture"/>);
  fireEvent.click(await screen.findByRole('button',{name:'Halaman 2'}));
  expect(await screen.findByText('Hasil baca halaman ini belum tersedia. Periksa PDF asli dan laporkan jika ada isi yang hilang.')).toBeVisible();
});
it('ends source loading on failure and offers a working retry',async()=>{
  sourceFail=true;
  render(<SOPReviewPanel documentId="SOP-1" token="fixture"/>);
  await screen.findByText('Sumber belum tersedia');
  expect(screen.queryByText('Memuat file sumber...')).not.toBeInTheDocument();
  sourceFail=false;fireEvent.click(screen.getByRole('button',{name:'Coba muat sumber lagi'}));
  await screen.findByTitle('PDF asli SOP');
});

