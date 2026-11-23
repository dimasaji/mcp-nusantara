import {fireEvent,render,screen,waitFor} from '@testing-library/react';
import {describe,expect,it,vi,afterEach} from 'vitest';
import {hermesHttpError,hermesReason,HermesConnectionPanel} from '../src/hermes-connection';
import {AdminAuthProvider} from '../src/auth';
import {OperatorConsole} from '../src/assistant';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
vi.mock('@tanstack/react-router',()=>({Link:({to,children}:{to:string;children:React.ReactNode})=><a href={to}>{children}</a>}));
afterEach(()=>{vi.restoreAllMocks();vi.unstubAllGlobals();});

describe('Hermes connection errors',()=>{
  it('does not report a browser boundary rejection as a bad token',()=>{
    expect(hermesHttpError(403,'BROWSER_BOUNDARY_REJECTED')).toContain('batas browser lokal');
    expect(hermesHttpError(403,'BROWSER_BOUNDARY_REJECTED')).not.toContain('token operator');
  });

  it('keeps a real operator token rejection actionable',()=>{
    expect(hermesHttpError(403,'admin token diperlukan')).toContain('token operator');
  });

  it('translates only a safe allowlisted backend detail for profile errors',()=>{
    expect(hermesHttpError(503,'HERMES_NORMAL_PROFILE_REQUIRED')).toContain('backend V1 NORMAL');
    expect(hermesHttpError(503,'private traceback')).toBe('Pemeriksaan koneksi gagal (503).');
  });

  it('shows an actionable installation message without leaking local paths',()=>{
    const reason=hermesReason('HERMES_INSTALL_STATE_NOT_WRITABLE');
    expect(reason).toContain('izin instalasi Hermes');
    expect(reason).not.toContain('C:\\Users');
  });

  it('passes the System Settings token to Agent Workspace through the live auth provider',async()=>{
    const status={model:'fixture',provider:'local',revision:0,process_id:1,consistency_scope:'CURRENT_PROCESS_ONLY',availability:'NOT_VERIFIED',status:'NOT_VERIFIED',selection_enabled:false,selection_source:'BOOTSTRAP',last_request:null};
    const calls:{path:string;init?:RequestInit}[]=[];
    const fetch=vi.fn(async(path:string,init?:RequestInit)=>{calls.push({path,init});return {ok:true,json:async()=>path.endsWith('/hermes/connection')?
      {status:'NOT_CHECKED',reason:'Koneksi ACP belum diperiksa.',task_execution_enabled:false}:status};});
    vi.stubGlobal('fetch',fetch);
    const client=new QueryClient({defaultOptions:{queries:{retry:false}}});
    render(<QueryClientProvider client={client}><AdminAuthProvider><OperatorConsole title="Pengaturan Sistem"/><HermesConnectionPanel/></AdminAuthProvider></QueryClientProvider>);
    fireEvent.change(screen.getByLabelText('Token operator'),{target:{value:'session-only-test-token'}});
    await waitFor(()=>expect(calls.some(({path,init})=>path.endsWith('/hermes/connection')&&
      (init?.headers as Record<string,string>)['X-Admin-Token']==='session-only-test-token')).toBe(true));
    expect(screen.getByLabelText('Token operator')).toHaveAttribute('type','password');
    expect(await screen.findByText('Belum diperiksa')).toBeInTheDocument();
    client.clear();
  });
});
