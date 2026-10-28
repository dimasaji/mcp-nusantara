import {render,screen,fireEvent,waitFor} from '@testing-library/react';
import {afterEach,describe,it,expect,vi} from 'vitest';
import {UserChat,OperatorConsole} from '../src/assistant';
vi.mock('@tanstack/react-router',()=>({Link:({to,children}:{to:string;children:React.ReactNode})=><a href={to}>{children}</a>}));
afterEach(()=>vi.unstubAllGlobals());
const status={model:'fixture-a',provider:'ollama',revision:0,process_id:42,consistency_scope:'CURRENT_PROCESS_ONLY',availability:'NOT_VERIFIED',status:'NOT_VERIFIED',selection_enabled:true,selection_source:'BOOTSTRAP',last_request:null};
const answer={session_id:'session',response:'Jawaban aman dari Hermes.',model:'fixture-a',provider_status:'ollama',latency_ms:2,timestamp:'2026-10-09',trust:{supports_claim:true,confidence:.9,risk_level:'low',requires_human:false,evidence_count:0,evidence_available:false},grounding:{enabled:true,grounded:true,reason:'grounded'},understanding:{intent:'general'},problem:{goal:null},evidence:[]};
describe('V1 user and operator surfaces',()=>{
  it('starts a new client conversation without deleting server memory',async()=>{
    const fetch=vi.fn(async(path:string)=>({ok:true,json:async()=>path==='/v1/chat'?answer:status}));vi.stubGlobal('fetch',fetch);
    render(<UserChat/>);
    fireEvent.change(screen.getByLabelText('Pertanyaan Anda'),{target:{value:'Percakapan lama'}});fireEvent.click(screen.getByRole('button',{name:'Kirim pertanyaan'}));
    await screen.findByText(answer.response);fireEvent.click(screen.getByRole('button',{name:'+ New Chat'}));
    expect(screen.queryByText('Percakapan lama')).not.toBeInTheDocument();expect(screen.getByText('Apa yang bisa saya bantu?')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Pertanyaan Anda'),{target:{value:'Percakapan baru'}});fireEvent.click(screen.getByRole('button',{name:'Kirim pertanyaan'}));await screen.findByText(answer.response);
    const calls=fetch.mock.calls.filter(([path])=>path==='/v1/chat') as unknown as [string,RequestInit][];
    expect(JSON.parse(calls[0][1].body as string).session_id).not.toBe(JSON.parse(calls[1][1].body as string).session_id);
    expect(fetch.mock.calls.every(([path])=>path==='/v1/chat'||path==='/v1/control-plane/model-status')).toBe(true);
  });
  it('reports missing runtime endpoints honestly without enabling unsupported controls',async()=>{
    vi.stubGlobal('fetch',vi.fn(async()=>({ok:false,status:404})));
    render(<OperatorConsole/>);
    expect(await screen.findByRole('alert')).toHaveTextContent('Runtime yang terhubung belum menyediakan API ini');
    expect(screen.getByRole('button',{name:'Muat model tersedia'})).toBeDisabled();
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument();
    expect(screen.getAllByText(/NOT_VERIFIED/).length).toBeGreaterThan(0);
  });
  it.each([403,500,503])('retains truthful runtime status when inventory fails with %s',async(code)=>{
    vi.stubGlobal('fetch',vi.fn(async(path:string)=>path.endsWith('/models')?{ok:false,status:code}:{ok:true,json:async()=>status}));
    render(<OperatorConsole/>);fireEvent.change(screen.getByLabelText('Token operator'),{target:{value:'test-token'}});
    await waitFor(()=>expect(screen.getByRole('button',{name:'Muat model tersedia'})).toBeEnabled());
    fireEvent.click(screen.getByRole('button',{name:'Muat model tersedia'}));
    expect(await screen.findByRole('alert')).toBeInTheDocument();
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument();
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
    const body=JSON.parse(call[1].body as string);expect(body.user_input).toBe('Pertanyaan saya');expect(body.session_id).toMatch(/^web-/);expect(body.model).toBeUndefined();expect(screen.queryByRole('combobox')).not.toBeInTheDocument();
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
    const fetch=vi.fn(async(path:string)=>({ok:true,json:async()=>path.endsWith('/models')?{models:['fixture-a','fixture-b'],observed_revision:0}:path.endsWith('/model-selection')?{...status,model:'fixture-b',revision:1,selection_source:'OPERATOR'}:status}));vi.stubGlobal('fetch',fetch);
    render(<OperatorConsole/>);expect(screen.queryByRole('combobox')).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Token operator'),{target:{value:'test-token'}});await waitFor(()=>expect(screen.getByRole('button',{name:'Muat model tersedia'})).toBeEnabled());fireEvent.click(screen.getByRole('button',{name:'Muat model tersedia'}));
    fireEvent.change(await screen.findByLabelText('Pilih model tersedia'),{target:{value:'fixture-b'}});fireEvent.click(screen.getByRole('button',{name:'Terapkan model global'}));expect(await screen.findByText(/Model diterapkan untuk request berikutnya/)).toBeInTheDocument();
    const call=fetch.mock.calls.find(([path])=>path.endsWith('/model-selection')) as unknown as [string,RequestInit];expect(JSON.parse(call[1].body as string)).toEqual({model:'fixture-b',expected_revision:0});expect(call[1].headers).toEqual(expect.objectContaining({'X-Admin-Token':'test-token'}));
  });
});
