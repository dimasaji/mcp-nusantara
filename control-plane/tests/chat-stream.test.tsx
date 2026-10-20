import {act,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import {sendUserChat} from '../src/api';
import {UserChat} from '../src/assistant';
vi.mock('@tanstack/react-router',()=>({Link:({children}:{children:React.ReactNode})=><span>{children}</span>}));
afterEach(()=>{vi.useRealTimers();vi.unstubAllGlobals();});
const answer={session_id:'session',response:'Jawaban final.',model:'fixture',provider_status:'ollama',latency_ms:1,timestamp:'now',trust:{supports_claim:false,confidence:0,risk_level:'low',requires_human:false,evidence_count:0,evidence_available:false},grounding:{enabled:true,grounded:false,reason:'no_evidence'},understanding:{intent:'general'},problem:{goal:null},evidence:[]};

it('delivers a split UTF-8 delta before final projection and does not fabricate chunks',async()=>{
  let output!:ReadableStreamDefaultController<Uint8Array>;
  const encoder=new TextEncoder();
  vi.stubGlobal('fetch',vi.fn(async()=>new Response(new ReadableStream({start(c){output=c;}}),{headers:{'Content-Type':'application/x-ndjson'}})));
  const delta=vi.fn();const result=sendUserChat('question','session','a'.repeat(32),undefined,90000,{onDelta:delta});
  const bytes=encoder.encode(JSON.stringify({type:'delta',text:'Satu é'})+'\n');
  output.enqueue(bytes.slice(0,bytes.length-3));output.enqueue(bytes.slice(bytes.length-3));
  await waitFor(()=>expect(delta).toHaveBeenCalledWith('Satu é'));
  output.enqueue(encoder.encode(JSON.stringify({type:'final',answer})+'\n'));output.close();
  await expect(result).resolves.toEqual(answer);expect(delta).toHaveBeenCalledTimes(1);
});

it('allows stop then another send and never sends twice on repeated submit',async()=>{
  localStorage.clear();sessionStorage.clear();let posts=0;
  vi.stubGlobal('fetch',vi.fn(async(path:string,options:RequestInit={})=>{
    if(path==='/v1/chat'){
      posts++;
      if(posts===1)return new Promise((_,reject)=>options.signal?.addEventListener('abort',()=>reject(new DOMException('aborted','AbortError'))));
      return {ok:true,json:async()=>answer};
    }
    return {ok:true,json:async()=>path.endsWith('/history')?{session_id:'session',turns:[]}:{model:'fixture',provider:'ollama',revision:0,process_id:1,consistency_scope:'CURRENT_PROCESS_ONLY',availability:'NOT_VERIFIED',status:'NOT_VERIFIED',selection_enabled:true,selection_source:'BOOTSTRAP',last_request:null}};
  }));
  const view=render(<UserChat/>);await act(async()=>{await Promise.resolve();});
  fireEvent.change(screen.getByLabelText('Pertanyaan Anda'),{target:{value:'question'}});
  const form=screen.getByLabelText('Pertanyaan Anda').closest('form')!;
  fireEvent.submit(form);fireEvent.submit(form);expect(posts).toBe(1);
  fireEvent.click(screen.getByRole('button',{name:'Berhenti'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('dihentikan');
  fireEvent.click(screen.getByRole('button',{name:'Kirim pertanyaan'}));
  expect(await screen.findByText('Jawaban final.')).toBeInTheDocument();expect(posts).toBe(2);
  view.unmount();
});
