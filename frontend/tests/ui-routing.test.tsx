import {render,screen,cleanup} from '@testing-library/react';
import {afterEach,beforeEach,describe,it,expect,vi} from 'vitest';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {createRouter,createMemoryHistory,RouterProvider} from '@tanstack/react-router';
import {router as existingRouter} from '../src/router';
import {UserChat} from '../src/assistant';
import {OperatorHome} from '../src/operator';
import {within} from '@testing-library/react';
import {fetchModelStatus,sendUserChat} from '../src/api';

vi.mock('../src/api',async importOriginal=>{
  const original=await importOriginal<typeof import('../src/api')>();
  return {...original,
    fetchModelStatus:vi.fn().mockResolvedValue({model:'fixture-local',provider:'ollama',
      revision:0,process_id:42,consistency_scope:'CURRENT_PROCESS_ONLY',
      availability:'NOT_VERIFIED',status:'NOT_VERIFIED',selection_enabled:false,
      selection_source:'BOOTSTRAP',last_request:null}),
    fetchChatHistory:vi.fn().mockResolvedValue({session_id:'fixture',turns:[]}),sendUserChat:vi.fn()};
});
beforeEach(()=>{
  vi.spyOn(window,'scrollTo').mockImplementation(()=>{});
  vi.stubGlobal('fetch',vi.fn(()=>{throw new Error('Unexpected network request');}));
});
afterEach(()=>{cleanup();vi.mocked(window.scrollTo).mockRestore();vi.clearAllMocks();vi.unstubAllGlobals();});

describe('V1 assistant route alias',()=>{
  it.each(['/','/ui','/assistant','/workspace'])('renders the existing assistant at %s without Console layout',async path=>{
    const router=createRouter({routeTree:existingRouter.routeTree,
      history:createMemoryHistory({initialEntries:[path]})});
    const client=new QueryClient({defaultOptions:{queries:{retry:false}}});
    render(<QueryClientProvider client={client}><RouterProvider router={router}/></QueryClientProvider>);
    expect(await screen.findByRole('heading',{name:'Mau dibantu apa hari ini?'})).not.toBeNull();
    expect(screen.getByLabelText('Pertanyaan Anda')).not.toBeNull();
    expect((screen.getByRole('button',{name:'Kirim pertanyaan'}) as HTMLButtonElement).disabled).toBe(true);
    expect(screen.queryByRole('navigation',{name:'Runtime control'})).toBeNull();
    expect(screen.queryByRole('navigation',{name:'Control Plane'})).toBeNull();
    expect(screen.queryByRole('link',{name:'Buka Control Panel'})).toBeNull();
    expect(screen.getByRole('link',{name:'Pengaturan'})).toHaveAttribute('href','/settings');
    expect(screen.getByRole('navigation',{name:'Riwayat Chat'})).toBeInTheDocument();
    expect(screen.queryByText('Not Found')).toBeNull();
    expect(router.state.location.pathname).toBe(path);
    expect(fetchModelStatus).toHaveBeenCalled();
    expect(sendUserChat).not.toHaveBeenCalled();
    expect(fetch).not.toHaveBeenCalled();
  });
  it('makes chat the landing page and preserves the operator dashboard within Settings',()=>{
    const routes=existingRouter.routeTree.children??[];
    const componentFor=(path:string)=>routes.find(route=>'path' in route.options&&route.options.path===path)?.options.component;
    expect(componentFor('/')).not.toBe(OperatorHome);
    expect(componentFor('/ui')).not.toBe(OperatorHome);
    expect(componentFor('/workspace')).not.toBe(OperatorHome);
    expect(componentFor('/dashboard')).toBe(OperatorHome);
  });
  it('offers Control Plane only from Settings and keeps global navigation focused on chat',async()=>{
    const router=createRouter({routeTree:existingRouter.routeTree,
      history:createMemoryHistory({initialEntries:['/settings']})});
    const client=new QueryClient({defaultOptions:{queries:{retry:false}}});
    render(<QueryClientProvider client={client}><RouterProvider router={router}/></QueryClientProvider>);
    expect(await screen.findByRole('heading',{name:'Pengaturan'})).toBeInTheDocument();
    const global=screen.getByRole('navigation',{name:'Navigasi utama'});
    expect(within(global).queryByRole('link',{name:/Control Plane|Human Control|Beranda/})).toBeNull();
    const settings=screen.getByRole('navigation',{name:'Pengaturan NUSANTARA'});
    expect(within(settings).getByRole('link',{name:/Control Plane/})).toHaveAttribute('href','/dashboard');
    expect(screen.getByRole('link',{name:'Kembali ke chat'})).toHaveAttribute('href','/');
  });
});

