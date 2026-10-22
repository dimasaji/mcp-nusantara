import {act,render,screen,fireEvent,waitFor} from '@testing-library/react';
import {afterEach,describe,it,expect,vi} from 'vitest';
import {UserChat,OperatorConsole} from '../src/assistant';
import {AdminAuthProvider} from '../src/auth';
import {fetchModelStatus,fetchAvailableModels,selectOperatorModel,sendUserChat} from '../src/api';
vi.mock('@tanstack/react-router',()=>({Link:({to,children}:{to:string;children:React.ReactNode})=><a href={to}>{children}</a>}));
afterEach(()=>{vi.useRealTimers();vi.restoreAllMocks();vi.unstubAllGlobals();});
const status={model:'fixture-a',provider:'ollama',revision:0,process_id:42,consistency_scope:'CURRENT_PROCESS_ONLY',availability:'NOT_VERIFIED',status:'NOT_VERIFIED',selection_enabled:true,selectable_providers:['ollama','openrouter'] as ('ollama'|'openrouter')[],selection_source:'BOOTSTRAP',last_request:null};
const answer={session_id:'session',response:'Jawaban aman dari Hermes.',model:'fixture-a',provider_status:'ollama',latency_ms:2,timestamp:'2026-10-09',trust:{supports_claim:true,confidence:.9,risk_level:'low',requires_human:false,evidence_count:0,evidence_available:false},grounding:{enabled:true,grounded:true,reason:'grounded'},understanding:{intent:'general'},problem:{goal:null},evidence:[]};
describe('V1 user and operator surfaces',()=>{
  it('keeps the same focused composer DOM while typing each character',async()=>{
    vi.stubGlobal('fetch',vi.fn(async(path:string)=>({ok:true,json:async()=>path==='/v1/chat/history'?{session_id:'fixture',turns:[]}:status})));
    const view=render(<UserChat/>);
    await act(async()=>{await Promise.resolve();});
    const input=screen.getByLabelText('Pertanyaan Anda');input.focus();
    for(const value of ['s','sa','sat','satu']){
      fireEvent.change(input,{target:{value}});
      expect(screen.getByLabelText('Pertanyaan Anda')).toBe(input);
      expect(input).toHaveFocus();
    }
    view.unmount();
  });
  it('ignores a delayed manual History response after changing sessions',async()=>{
    localStorage.clear();sessionStorage.clear();let reads=0;let release:(value:unknown)=>void=()=>{};
    vi.stubGlobal('fetch',vi.fn(async(path:string)=>({ok:true,json:async()=>{
      if(path!=='/v1/chat/history')return status;
      if(++reads===2)return new Promise(resolve=>{release=resolve;});
      return {session_id:'fixture',turns:[]};
    }})));
    const view=render(<UserChat/>);await act(async()=>{await Promise.resolve();});
    fireEvent.click(screen.getByRole('button',{name:'Muat ulang History'}));
    await act(async()=>{await Promise.resolve();});
    fireEvent.click(screen.getByRole('button',{name:/Chat baru/}));
    await act(async()=>{release({session_id:'fixture',turns:[{question:'Sesi lama',answer:{...answer,response:'Rahasia sesi lama'},error:null,status:'SUCCEEDED',timestamp:'earlier'}]});});
    expect(screen.queryByText('Rahasia sesi lama')).not.toBeInTheDocument();
    view.unmount();localStorage.clear();sessionStorage.clear();
  });
  it('merges delayed persisted history with new messages and reopens earlier sessions',async()=>{
    localStorage.clear();sessionStorage.clear();
    let resolveHistory:(value:unknown)=>void=()=>{};
    let reads=0;
    vi.stubGlobal('fetch',vi.fn(async(path:string)=>{
      if(path==='/v1/chat/history'){
        if(++reads===1)return {ok:true,json:()=>new Promise(resolve=>{resolveHistory=resolve;})};
        return {ok:true,json:async()=>({session_id:'fixture',turns:[]})};
      }
      return {ok:true,json:async()=>path==='/v1/chat'?answer:status};
    }));
    const view=render(<UserChat/>);
    await act(async()=>{await Promise.resolve();});
    fireEvent.change(screen.getByLabelText('Pertanyaan Anda'),{target:{value:'Pesan baru'}});
    fireEvent.click(screen.getByRole('button',{name:'Kirim pertanyaan'}));
    await screen.findByText(answer.response);
    await act(async()=>{resolveHistory({session_id:'fixture',turns:[{question:'Pesan tersimpan',answer:{...answer,response:'Jawaban tersimpan',timestamp:'earlier'},error:null,status:'SUCCEEDED',timestamp:'earlier'}]});});
    expect(await screen.findByText('Jawaban tersimpan')).toBeInTheDocument();
    expect(screen.getByText(answer.response)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button',{name:/Chat baru/}));
    expect(JSON.parse(localStorage.getItem('nusantara-chat-p0-public-sessions')!)).toHaveLength(2);
    view.unmount();localStorage.clear();sessionStorage.clear();
  });
  it('shows citation metadata without exposing the supporting raw quotation',async()=>{
    const evidence=[{document_id:'sop-private',title:'SOP Permohonan Data Pribadi (PIAK-03)',chunk:'Persyaratan permohonan data pribadi: Surat Permohonan.',score:.9}];
    vi.stubGlobal('fetch',vi.fn(async(path:string)=>({ok:true,json:async()=>path==='/v1/chat'?{...answer,response:'Silakan siapkan Surat Permohonan.',evidence,provider_status:'evidence_fast_path'}:status})));
    render(<UserChat/>);
    fireEvent.change(screen.getByLabelText('Pertanyaan Anda'),{target:{value:'Mau minta data pribadi, bawa apa?'}});
    fireEvent.click(screen.getByRole('button',{name:'Kirim pertanyaan'}));
    const source=await screen.findByText('SOP Permohonan Data Pribadi (PIAK-03)');
    const details=source.closest('details')!;
    expect(details).not.toHaveAttribute('open');
    fireEvent.click(screen.getByText('Sumber (1)'));
    await waitFor(()=>expect(details.parentElement).toHaveAttribute('open'));
    fireEvent.click(source);
    await waitFor(()=>expect(details).toHaveAttribute('open'));
    expect(screen.queryByText(evidence[0].chunk)).not.toBeInTheDocument();
    expect(screen.getByText('Referensi: sop-private')).toBeVisible();
    expect(screen.getByText('Silakan siapkan Surat Permohonan.')).toBeInTheDocument();
  });
  it.each([false,true])('releases a stalled chat at 90 seconds and preserves manual retry when fetch honors abort: %s',async(honorsAbort)=>{
    vi.useFakeTimers();
    const fetch=vi.fn((path:string,options?:RequestInit)=>{
      if(path!=='/v1/chat')return Promise.resolve({ok:true,json:async()=>path==='/v1/control-plane/model-status'?{...status,provider:'openrouter'}:status});
      return new Promise<never>((_,reject)=>{
        if(honorsAbort)options?.signal?.addEventListener('abort',()=>reject(new DOMException('Aborted','AbortError')),{once:true});
      });
    });vi.stubGlobal('fetch',fetch);
    render(<UserChat/>);
    await act(async()=>{await Promise.resolve();});
    fireEvent.change(screen.getByLabelText('Pertanyaan Anda'),{target:{value:'Pertanyaan tetap tersedia'}});
    fireEvent.click(screen.getByRole('button',{name:'Kirim pertanyaan'}));
    expect(screen.getByRole('button',{name:'Memproses…'})).toBeDisabled();
    await act(async()=>{await vi.advanceTimersByTimeAsync(89999);});
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(screen.getByRole('button',{name:'Memproses…'})).toBeDisabled();
    await act(async()=>{await vi.advanceTimersByTimeAsync(1);});
    expect(screen.getByRole('alert')).toHaveTextContent('Batas waktu 90 detik');
    expect(screen.getByRole('alert')).toHaveTextContent('Backend mungkin masih memproses');
    expect(screen.getByRole('alert')).toHaveTextContent('tidak menjamin pembatalan di server');
    expect(screen.getByLabelText('Pertanyaan Anda')).toHaveValue('Pertanyaan tetap tersedia');
    expect(screen.getByRole('button',{name:'Kirim pertanyaan'})).toBeEnabled();
    expect(screen.getByRole('button',{name:/Chat baru/})).toBeEnabled();
    const first=fetch.mock.calls.filter(([path])=>path==='/v1/chat');
    expect(first).toHaveLength(1);expect(first[0][1]?.signal?.aborted).toBe(true);
    expect(vi.getTimerCount()).toBe(0);
    await act(async()=>{await vi.advanceTimersByTimeAsync(60000);});
    expect(fetch.mock.calls.filter(([path])=>path==='/v1/chat')).toHaveLength(1);
    fireEvent.click(screen.getByRole('button',{name:'Kirim pertanyaan'}));
    const chats=fetch.mock.calls.filter(([path])=>path==='/v1/chat');
    expect(chats).toHaveLength(2);
    expect(JSON.parse(chats[1][1]?.body as string)).toEqual(JSON.parse(chats[0][1]?.body as string));
    expect(chats[1][1]?.signal).not.toBe(chats[0][1]?.signal);
    expect(chats[1][1]?.signal?.aborted).toBe(false);
    expect(fetch.mock.calls.every(([path])=>path==='/v1/chat'||path==='/v1/chat/history'||path==='/v1/control-plane/model-status')).toBe(true);
    await act(async()=>{await vi.advanceTimersByTimeAsync(90000);});
    expect(vi.getTimerCount()).toBe(0);
  });
  it('allows the local Ollama model deadline to cover the configured cold-load window',async()=>{
    vi.useFakeTimers();
    const fetch=vi.fn((path:string,options?:RequestInit)=>{
      if(path==='/v1/chat')return new Promise<never>((_,reject)=>options?.signal?.addEventListener('abort',()=>reject(new DOMException('Aborted','AbortError')),{once:true}));
      return Promise.resolve({ok:true,json:async()=>path==='/v1/control-plane/model-status'?{...status,model:'qwen2.5:7b'}:status});
    });vi.stubGlobal('fetch',fetch);
    render(<UserChat/>);
    await act(async()=>{await Promise.resolve();});
    expect(screen.queryByText('Ollama · qwen2.5:7b')).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Pertanyaan Anda'),{target:{value:'Jelaskan pertanyaan lokal.'}});
    fireEvent.click(screen.getByRole('button',{name:'Kirim pertanyaan'}));
    await act(async()=>{await vi.advanceTimersByTimeAsync(90000);});
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    await act(async()=>{await vi.advanceTimersByTimeAsync(179999);});
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    await act(async()=>{await vi.advanceTimersByTimeAsync(1);});
    expect(screen.getByRole('alert')).toHaveTextContent('Batas waktu 270 detik');
    expect(fetch.mock.calls.filter(([path])=>path==='/v1/chat')).toHaveLength(1);
    expect(vi.getTimerCount()).toBe(0);
  });
  it.each(['success','http error','network error','invalid response'])('clears the chat deadline after %s',async(outcome)=>{
    vi.useFakeTimers();
    const fetch=vi.fn(async()=>{
      if(outcome==='network error')throw new Error('Koneksi gagal');
      return outcome==='http error'?{ok:false,status:503}:{ok:true,json:async()=>outcome==='invalid response'?{}:answer};
    });vi.stubGlobal('fetch',fetch);
    const request=sendUserChat('Pertanyaan','same-session');
    if(outcome==='success')await expect(request).resolves.toEqual(answer);
    else await expect(request).rejects.toThrow(outcome==='http error'?'503':outcome==='network error'?'Koneksi gagal':'kontrak layanan');
    expect(vi.getTimerCount()).toBe(0);
    const options=fetch.mock.calls[0] as unknown as [string,RequestInit];
    expect(options[1].signal?.aborted).toBe(false);
    await vi.advanceTimersByTimeAsync(90000);
    expect(options[1].signal?.aborted).toBe(false);expect(fetch).toHaveBeenCalledTimes(1);
  });
  it.each([false,true])('creates a new retry ID only for a server-confirmed pre-provider timeout: %s',async(retrySafe)=>{
    localStorage.clear();sessionStorage.clear();let attempts=0;
    const fetch=vi.fn(async(path:string)=>{
      if(path!=='/v1/chat')return {ok:true,json:async()=>status};
      if(++attempts===1)return {ok:false,status:504,
        headers:new Headers(retrySafe?{'X-Chat-Retry-Safe':'pre-provider'}:{}),json:async()=>({detail:'timeout'})};
      return {ok:true,json:async()=>answer};
    });vi.stubGlobal('fetch',fetch);
    render(<UserChat/>);
    fireEvent.change(screen.getByLabelText('Pertanyaan Anda'),{target:{value:'Pertanyaan dengan timeout'}});
    fireEvent.click(screen.getByRole('button',{name:'Kirim pertanyaan'}));
    expect(await screen.findByRole('alert')).toHaveTextContent('Batas waktu pemrosesan');
    expect(attempts).toBe(1);
    fireEvent.click(screen.getByRole('button',{name:'Kirim pertanyaan'}));
    expect(await screen.findByText(answer.response)).toBeInTheDocument();
    const bodies=fetch.mock.calls.filter(([path])=>path==='/v1/chat').map(call=>
      JSON.parse((call as unknown as [string,RequestInit])[1].body as string));
    if(retrySafe){expect(bodies[1].request_id).not.toBe(bodies[0].request_id);expect(bodies[1].retry_of).toBe(bodies[0].request_id);}
    else{expect(bodies[1]).toEqual(bodies[0]);}
  });
  it('keeps model-control fetches outside the chat deadline',async()=>{
    vi.useFakeTimers();
    const resolvers:(()=>void)[]=[];
    const fetch=vi.fn((path:string)=>new Promise(resolve=>resolvers.push(()=>resolve({ok:true,json:async()=>path.endsWith('/models')?{models:['fixture-a'],observed_revision:0}:status}))));
    vi.stubGlobal('fetch',fetch);
    const requests=[fetchModelStatus(),fetchAvailableModels('test-token'),selectOperatorModel('fixture-a',0,'test-token')];
    expect(vi.getTimerCount()).toBe(0);
    await vi.advanceTimersByTimeAsync(60000);
    expect(fetch).toHaveBeenCalledTimes(3);
    expect(fetch.mock.calls.every((call)=>(call as unknown as [string,RequestInit])[1].signal===undefined)).toBe(true);
    resolvers.forEach(resolve=>resolve());await Promise.all(requests);
    expect(vi.getTimerCount()).toBe(0);
  });
  it('starts a new client conversation without deleting server memory',async()=>{
    const fetch=vi.fn(async(path:string)=>({ok:true,json:async()=>path==='/v1/chat'?answer:status}));vi.stubGlobal('fetch',fetch);
    render(<UserChat/>);
    fireEvent.change(screen.getByLabelText('Pertanyaan Anda'),{target:{value:'Percakapan lama'}});fireEvent.click(screen.getByRole('button',{name:'Kirim pertanyaan'}));
    await screen.findByText(answer.response);fireEvent.click(screen.getByRole('button',{name:/Chat baru/}));
    expect(screen.queryByText('Percakapan lama')).not.toBeInTheDocument();expect(screen.getByText('Mau dibantu apa hari ini?')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Pertanyaan Anda'),{target:{value:'Percakapan baru'}});fireEvent.click(screen.getByRole('button',{name:'Kirim pertanyaan'}));await screen.findByText(answer.response);
    const calls=fetch.mock.calls.filter(([path])=>path==='/v1/chat') as unknown as [string,RequestInit][];
    expect(JSON.parse(calls[0][1].body as string).session_id).not.toBe(JSON.parse(calls[1][1].body as string).session_id);
    expect(fetch.mock.calls.every(([path])=>path==='/v1/chat'||path==='/v1/chat/history'||path==='/v1/control-plane/model-status')).toBe(true);
  });
  it('reports missing runtime endpoints honestly without enabling unsupported controls',async()=>{
    vi.stubGlobal('fetch',vi.fn(async()=>({ok:false,status:404})));
    render(<AdminAuthProvider><OperatorConsole/></AdminAuthProvider>);
    expect(await screen.findByRole('alert')).toHaveTextContent('Runtime yang terhubung belum menyediakan API ini');
    expect(screen.getByRole('button',{name:'Muat model tersedia'})).toBeDisabled();
    expect(screen.queryByLabelText('Pilih model tersedia')).not.toBeInTheDocument();
    expect(screen.getAllByText(/NOT_VERIFIED/).length).toBeGreaterThan(0);
  });
  it.each([403,500,503])('retains truthful runtime status when inventory fails with %s',async(code)=>{
    vi.stubGlobal('fetch',vi.fn(async(path:string)=>path.endsWith('/models')?{ok:false,status:code,json:async()=>({detail:code===503?'MODEL_INVENTORY_UNAVAILABLE':'denied'})}:{ok:true,json:async()=>status}));
    render(<AdminAuthProvider><OperatorConsole/></AdminAuthProvider>);fireEvent.change(screen.getByLabelText('Token operator'),{target:{value:'test-token'}});
    await waitFor(()=>expect(screen.getByRole('button',{name:'Muat model tersedia'})).toBeEnabled());
    fireEvent.click(screen.getByRole('button',{name:'Muat model tersedia'}));
    expect(await screen.findByRole('alert')).toBeInTheDocument();
    expect(screen.queryByLabelText('Pilih model tersedia')).not.toBeInTheDocument();
    expect(screen.getByText(/Model aktif: fixture-a/)).toBeInTheDocument();
  });
  it('preserves multiline response content and session across a follow-up',async()=>{
    const longResponse=('Baris jawaban lengkap.\n').repeat(400)+'AKHIR JAWABAN';
    const fetch=vi.fn(async(path:string)=>({ok:true,json:async()=>path==='/v1/chat'?{...answer,response:longResponse}:status}));vi.stubGlobal('fetch',fetch);
    render(<UserChat/>);
    for(const text of ['Hallo','Pertanyaan lanjutan']){
      fireEvent.change(screen.getByLabelText('Pertanyaan Anda'),{target:{value:text}});fireEvent.click(screen.getByRole('button',{name:'Kirim pertanyaan'}));
      await waitFor(()=>expect(screen.getByLabelText('Pertanyaan Anda')).toHaveValue(''));
    }
    expect(document.querySelectorAll('.answer p')[0].textContent).toBe(longResponse);
    const calls=fetch.mock.calls.filter(([path])=>path==='/v1/chat') as unknown as [string,RequestInit][];
    expect(calls).toHaveLength(2);
    expect(JSON.parse(calls[0][1].body as string).session_id).toBe(JSON.parse(calls[1][1].body as string).session_id);
    expect(screen.getByText('Pertanyaan lanjutan')).toBeInTheDocument();
  });
  it('sends chat to V1 without a user model override and displays the projected response',async()=>{
    const fetch=vi.fn(async(path:string)=>({ok:true,json:async()=>path==='/v1/chat'?answer:status}));vi.stubGlobal('fetch',fetch);
    render(<UserChat/>);fireEvent.change(screen.getByLabelText('Pertanyaan Anda'),{target:{value:'Pertanyaan saya'}});fireEvent.click(screen.getByRole('button',{name:'Kirim pertanyaan'}));
    expect(await screen.findByText('Jawaban aman dari Hermes.')).toBeInTheDocument();
    const call=fetch.mock.calls.find(([path])=>path==='/v1/chat') as unknown as [string,RequestInit];
    const body=JSON.parse(call[1].body as string);expect(body.user_input).toBe('Pertanyaan saya');expect(body.session_id).toMatch(/^web-/);expect(body.model).toBeUndefined();expect(screen.queryByLabelText('Pilih model tersedia')).not.toBeInTheDocument();
  });
  it('keeps model details out of the Chat header',async()=>{
    vi.stubGlobal('fetch',vi.fn(async(path:string)=>({ok:true,json:async()=>path==='/v1/control-plane/model-status'?{...status,model:'qwen2.5:7b',provider:'ollama'}:status})));
    render(<UserChat/>);
    await act(async()=>{await Promise.resolve();});
    expect(screen.queryByText('Ollama · qwen2.5:7b')).not.toBeInTheDocument();
  });
  it('retains the question and shows an error when backend is unavailable',async()=>{
    vi.stubGlobal('fetch',vi.fn(async(path:string)=>path==='/v1/chat'?{ok:false,status:503}:{ok:true,json:async()=>status}));
    render(<UserChat/>);fireEvent.change(screen.getByLabelText('Pertanyaan Anda'),{target:{value:'Tetap simpan ini'}});fireEvent.click(screen.getByRole('button',{name:'Kirim pertanyaan'}));
    expect(await screen.findByRole('alert')).toHaveTextContent('503');expect(screen.getByLabelText('Pertanyaan Anda')).toHaveValue('Tetap simpan ini');expect(screen.getByRole('button',{name:'Kirim pertanyaan'})).toBeEnabled();
  });
  it('rejects a response containing private internal fields',async()=>{
    vi.stubGlobal('fetch',vi.fn(async(path:string)=>({ok:true,json:async()=>path==='/v1/chat'?{...answer,gate_pipeline:{secret:'PRIVATE'}}:status})));
    render(<UserChat/>);fireEvent.change(screen.getByLabelText('Pertanyaan Anda'),{target:{value:'hello'}});fireEvent.click(screen.getByRole('button',{name:'Kirim pertanyaan'}));
    expect(await screen.findByRole('alert')).toBeInTheDocument();expect(screen.queryByText('Jawaban aman dari Hermes.')).not.toBeInTheDocument();expect(screen.queryByText('PRIVATE')).not.toBeInTheDocument();
  });
  it('loads actual inventory with authorization and applies only an acknowledged change',async()=>{
    const fetch=vi.fn(async(path:string)=>({ok:true,json:async()=>path.includes('/models')?{models:['fixture-a','fixture-b'],provider:'ollama',observed_revision:0}:path.endsWith('/model-selection')?{...status,model:'fixture-b',revision:1,selection_source:'OPERATOR'}:status}));vi.stubGlobal('fetch',fetch);
    render(<AdminAuthProvider><OperatorConsole/></AdminAuthProvider>);expect(screen.queryByRole('combobox')).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Token operator'),{target:{value:'test-token'}});await waitFor(()=>expect(screen.getByRole('button',{name:'Muat model tersedia'})).toBeEnabled());fireEvent.click(screen.getByRole('button',{name:'Muat model tersedia'}));
    fireEvent.change(await screen.findByLabelText('Pilih model tersedia'),{target:{value:'fixture-b'}});fireEvent.click(screen.getByRole('button',{name:'Terapkan model global'}));expect(await screen.findByText(/Model diterapkan untuk request berikutnya/)).toBeInTheDocument();
    const call=fetch.mock.calls.find(([path])=>path.endsWith('/model-selection')) as unknown as [string,RequestInit];expect(JSON.parse(call[1].body as string)).toEqual({model:'fixture-b',provider:'ollama',expected_revision:0});expect(call[1].headers).toEqual(expect.objectContaining({'X-Admin-Token':'test-token'}));
  });
  it('loads Ollama tags and applies Qwen from an OpenRouter bootstrap without a provider dispatch',async()=>{
    const bootstrap={...status,provider:'openrouter',model:'openai/gpt-4o-mini'};
    const fetch=vi.fn(async(path:string)=>({ok:true,json:async()=>path.includes('/models')?{models:['qwen2.5:7b','llama3.2:1b'],provider:'ollama',observed_revision:0}:path.endsWith('/model-selection')?{...bootstrap,provider:'ollama',model:'qwen2.5:7b',revision:1}:bootstrap}));vi.stubGlobal('fetch',fetch);
    render(<AdminAuthProvider><OperatorConsole/></AdminAuthProvider>);
    fireEvent.change(await screen.findByLabelText('Provider runtime'),{target:{value:'ollama'}});
    fireEvent.change(screen.getByLabelText('Token operator'),{target:{value:'test-token'}});
    fireEvent.click(screen.getByRole('button',{name:'Muat model tersedia'}));
    expect(await screen.findByRole('option',{name:'qwen2.5:7b'})).toBeInTheDocument();
    expect(fetch.mock.calls.some(([path])=>path==='/v1/control-plane/models?provider=ollama')).toBe(true);
    fireEvent.change(screen.getByLabelText('Pilih model tersedia'),{target:{value:'qwen2.5:7b'}});
    fireEvent.click(screen.getByRole('button',{name:'Terapkan model global'}));
    expect(await screen.findByText(/Model diterapkan untuk request berikutnya/)).toBeInTheDocument();
    const selection=fetch.mock.calls.find(([path])=>path.endsWith('/model-selection')) as unknown as [string,RequestInit];
    expect(JSON.parse(selection[1].body as string)).toEqual({model:'qwen2.5:7b',provider:'ollama',expected_revision:0});
  });
});


