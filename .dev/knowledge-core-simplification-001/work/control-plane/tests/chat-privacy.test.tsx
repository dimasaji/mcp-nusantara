import {act,fireEvent,render,screen} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import {UserChat} from '../src/assistant';
import {fetchChatHistory,sendUserChat} from '../src/api';

vi.mock('@tanstack/react-router',()=>({Link:({to,children}:{to:string;children:React.ReactNode})=><a href={to}>{children}</a>}));
afterEach(()=>{vi.unstubAllGlobals();localStorage.clear();sessionStorage.clear();});
const status={model:'fixture',provider:'ollama',revision:0,process_id:1,consistency_scope:'CURRENT_PROCESS_ONLY',availability:'NOT_VERIFIED',status:'NOT_VERIFIED',selection_enabled:true,selection_source:'BOOTSTRAP',last_request:null};
const answer={session_id:'session',response:'Internal operator response',model:'fixture',provider_status:'ollama',latency_ms:1,timestamp:'now',trust:{supports_claim:false,confidence:0,risk_level:'low',requires_human:false,evidence_count:1,evidence_available:true},grounding:{enabled:true,grounded:true,reason:'grounded'},understanding:{intent:'general'},problem:{goal:null},evidence:[{document_id:'source',title:'Source',chunk:'PRIVATE_RAW_SOURCE',score:.9}]};

it('sends the operator credential only for document-scoped chat and matching history and strips source chunks',async()=>{
  const fetch=vi.fn(async(path:string)=>({ok:true,json:async()=>path==='/v1/chat/history'?{session_id:'session',turns:[]}:answer}));
  vi.stubGlobal('fetch',fetch);
  const result=await sendUserChat('Query','session','a'.repeat(32),undefined,90000,{token:'operator-fixture',documentIds:['source']});
  await fetchChatHistory('session','operator-fixture');
  expect((fetch.mock.calls[0] as unknown as [string,RequestInit])[1].headers).toMatchObject({'X-Admin-Token':'operator-fixture'});
  expect((fetch.mock.calls[1] as unknown as [string,RequestInit])[1].headers).toMatchObject({'X-Admin-Token':'operator-fixture'});
  expect(result.evidence[0].chunk).toBe('');
});

it('keeps general chat public even when an operator token is present in the upload panel',async()=>{
  const fetch=vi.fn(async(path:string)=>({ok:true,json:async()=>path==='/v1/chat/history'?{session_id:'session',turns:[]}:answer}));
  vi.stubGlobal('fetch',fetch);
  render(<UserChat token="operator-fixture"/>);
  fireEvent.change(screen.getByLabelText('Pertanyaan Anda'),{target:{value:'Pertanyaan umum'}});
  fireEvent.click(screen.getByRole('button',{name:'Kirim pertanyaan'}));
  await screen.findByText('Internal operator response');
  const chat=fetch.mock.calls.find(([path])=>path==='/v1/chat') as unknown as [string,RequestInit];
  expect(chat[1].headers).not.toHaveProperty('X-Admin-Token');
  const histories=fetch.mock.calls.filter(([path])=>path==='/v1/chat/history') as unknown as [string,RequestInit][];
  expect(histories.every(([,init])=>!(init.headers as Record<string,string>)['X-Admin-Token'])).toBe(true);
});

it('keeps operator token entry out of the chat upload popover',()=>{
  const view=render(<UserChat/>);
  fireEvent.click(view.container.querySelector('.chat-upload summary')!);
  expect(screen.queryByLabelText('Token operator')).not.toBeInTheDocument();
  expect(screen.queryByRole('button',{name:'Verifikasi akses'})).not.toBeInTheDocument();
  expect(screen.getByRole('link',{name:'Buka Knowledge untuk mengatur akses'})).toHaveAttribute('href','/knowledge');
});

it('uses the operator token from Control Plane automatically when the upload popover opens',async()=>{
  const pipeline={source:'fixture',database:'fixture.db',documents_indexed:0,pipeline_ready_documents:0,documents:[],watch:{enabled:false,folder:'',updated_at:''},runs:[],checked_at:'now'};
  const fetch=vi.fn(async(path:string)=>({ok:true,json:async()=>path==='/v1/control-plane/model-status'?status:path==='/v1/knowledge/pipeline/status'?pipeline:{session_id:'fixture',turns:[]}}));
  vi.stubGlobal('fetch',fetch);
  const view=render(<UserChat token="operator-fixture"/>);
  fireEvent.click(document.querySelector('.chat-upload summary')!);
  expect((await screen.findAllByText('Knowledge siap. Pilih dokumen untuk diunggah atau ditanyakan.')).length).toBeGreaterThan(0);
  const verification=fetch.mock.calls.find(([path])=>path==='/v1/knowledge/pipeline/status') as unknown as [string,RequestInit];
  expect(verification[1].headers).toMatchObject({'X-Admin-Token':'operator-fixture'});
  expect(screen.queryByRole('button',{name:'Verifikasi akses'})).not.toBeInTheDocument();
  view.unmount();
});

it('quarantines legacy titles and removes operator messages when switching to public',async()=>{
  localStorage.setItem('nusantara-chat-session-titles',JSON.stringify({'old':'PRIVATE_OLD_TITLE'}));
  let posts=0;
  vi.stubGlobal('fetch',vi.fn(async(path:string)=>({ok:true,json:async()=>{
    if(path==='/v1/chat'){posts++;return answer;}
    if(path==='/v1/chat/history')return {session_id:'session',turns:[]};
    return status;
  }})));
  const view=render(<UserChat token="operator-fixture"/>);
  fireEvent.change(screen.getByLabelText('Pertanyaan Anda'),{target:{value:'Private operator question'}});
  fireEvent.click(screen.getByRole('button',{name:'Kirim pertanyaan'}));
  expect(await screen.findByText('Internal operator response')).toBeInTheDocument();
  expect(localStorage.getItem('nusantara-chat-p0-operator-titles')).toBeNull();
  view.rerender(<UserChat/>);
  await act(async()=>{await Promise.resolve();});
  expect(screen.queryByText('Internal operator response')).not.toBeInTheDocument();
  expect(screen.queryByText('PRIVATE_OLD_TITLE')).not.toBeInTheDocument();
  expect(posts).toBe(1);
});
