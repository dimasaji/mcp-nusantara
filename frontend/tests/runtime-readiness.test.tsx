import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {afterEach,expect,it,vi} from 'vitest';
import {RuntimeReadinessPanel} from '../src/runtime-readiness';

afterEach(()=>{cleanup();vi.unstubAllGlobals();});
function panel(token:string){return render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><RuntimeReadinessPanel token={token}/></QueryClientProvider>);}
it('shows missing model independently of a reachable backend, with authenticated refresh',async()=>{
  const fetch=vi.fn(async()=>({ok:true,json:async()=>({status:'BLOCKED',provider:'ollama',model:'fixture',
    configuration_revision:1,process_id:123,build_id:'sha256:fixture',checked_at:'2026-10-30T00:00:00Z',
    operational_acceptance:'NOT_VERIFIED',checks:{api:{status:'AVAILABLE'},provider:{status:'CONNECTED'},model:{status:'MISSING'},storage:{status:'READABLE'},inference:{status:'NOT_VERIFIED'}}})}));
  vi.stubGlobal('fetch',fetch);panel('private-operator-token');
  expect(await screen.findByText('Model tidak ditemukan')).toBeVisible();
  expect(screen.getByText('Belum terbukti')).toBeVisible();
  expect(fetch.mock.calls[0]).toEqual(['/v1/runtime/readiness',expect.objectContaining({headers:{'X-Admin-Token':'private-operator-token'}})]);
  fireEvent.click(screen.getByRole('button',{name:'Periksa kesiapan Chat'}));
  await waitFor(()=>expect(fetch).toHaveBeenCalledTimes(2));
  expect(screen.queryByText('private-operator-token')).not.toBeInTheDocument();
});
it('does not probe without an operator token',()=>{
  const fetch=vi.fn();vi.stubGlobal('fetch',fetch);panel('');
  expect(screen.getByRole('button',{name:'Periksa kesiapan Chat'})).toBeDisabled();
  expect(fetch).not.toHaveBeenCalled();
});
