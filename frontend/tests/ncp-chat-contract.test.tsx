import {render,screen,fireEvent,cleanup,waitFor} from '@testing-library/react';
import {afterEach,it,expect,vi} from 'vitest';
import {UserChat} from '../src/assistant';
vi.mock('@tanstack/react-router',()=>({Link:({to,children}:{to:string;children:React.ReactNode})=><a href={to}>{children}</a>}));
afterEach(()=>{cleanup();vi.unstubAllGlobals();localStorage.clear();sessionStorage.clear();});
it.each(['deterministic_response','not_evaluated'])('does not attach a verification warning to %s',async reason=>{
  const answer={session_id:'fixture',response:'Halo, saya siap membantu.',model:'llama3.2:1b',provider_status:'local_rule',latency_ms:0,timestamp:'2026-10-22',trust:{supports_claim:false,confidence:0,risk_level:'high',requires_human:true,evidence_count:0,evidence_available:false},grounding:{enabled:true,grounded:reason==='deterministic_response',reason},understanding:{intent:'greeting'},problem:{goal:null},evidence:[]};
  vi.stubGlobal('fetch',vi.fn(async(path:string)=>({ok:true,json:async()=>path==='/v1/chat'?answer:path==='/v1/chat/history'?{session_id:'fixture',turns:[]}:{model:'llama3.2:1b',provider:'ollama',revision:0,status:'NOT_VERIFIED',availability:'NOT_VERIFIED',selection_enabled:false}})));
  render(<UserChat/>);
  fireEvent.change(screen.getByLabelText('Pertanyaan Anda'),{target:{value:'Halo'}});
  fireEvent.click(screen.getByRole('button',{name:'Kirim pertanyaan'}));
  expect(await screen.findByText(answer.response)).toBeInTheDocument();
  expect(screen.queryByText('Jawaban ini membutuhkan verifikasi.')).not.toBeInTheDocument();
  expect(document.querySelector('.verification-note')).toBeNull();
  expect(screen.getByText('Detail jawaban').closest('details')).not.toHaveAttribute('open');
});
it('preserves the question and links a safe provider retry without duplicate messages',async()=>{
  const calls:{request_id:string;retry_of?:string}[]=[];
  const answer={session_id:'fixture',response:'Model sudah pulih.',model:'llama3.2:1b',provider_status:'ollama',latency_ms:1,timestamp:'2026-10-22',trust:{supports_claim:false,confidence:0,risk_level:'high',requires_human:true,evidence_count:0,evidence_available:false},grounding:{enabled:true,grounded:false,reason:'not_evaluated'},understanding:{intent:'general'},problem:{goal:null},evidence:[]};
  vi.stubGlobal('fetch',vi.fn(async(path:string,options?:RequestInit)=>{
    if(path==='/v1/chat'){
      calls.push(JSON.parse(options!.body as string));
      return calls.length===1?{ok:false,status:503,headers:new Headers({'X-Chat-Retry-Safe':'pre-provider'}),json:async()=>({detail:'PROVIDER_UNAVAILABLE'})}:{ok:true,json:async()=>answer};
    }
    return {ok:true,json:async()=>path==='/v1/chat/history'?{session_id:'fixture',turns:[]}:{model:'llama3.2:1b',provider:'ollama',revision:0,status:'NOT_VERIFIED',availability:'NOT_VERIFIED',selection_enabled:false}};
  }));
  render(<UserChat/>);
  fireEvent.change(screen.getByLabelText('Pertanyaan Anda'),{target:{value:'Jelaskan pelangi'}});
  fireEvent.click(screen.getByRole('button',{name:'Kirim pertanyaan'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('Model belum tersedia');
  expect(screen.getByLabelText('Pertanyaan Anda')).toHaveValue('Jelaskan pelangi');
  await waitFor(()=>expect(screen.getByRole('button',{name:'Kirim pertanyaan'})).toBeEnabled());
  fireEvent.click(screen.getByRole('button',{name:'Kirim pertanyaan'}));
  expect(await screen.findByText(answer.response)).toBeInTheDocument();
  expect(calls).toHaveLength(2);
  expect(calls[1].retry_of).toBe(calls[0].request_id);
  expect(calls[1].request_id).not.toBe(calls[0].request_id);
  expect(document.querySelectorAll('.question')).toHaveLength(1);
});
