import {render,screen,fireEvent,within,waitFor} from '@testing-library/react';
import {describe,it,expect,vi,afterEach} from 'vitest';
import {useState} from 'react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {createRouter,createMemoryHistory,RouterProvider} from '@tanstack/react-router';
import {readSnapshotFile} from './snapshot-file';
import {AttestationSchema,SystemHealthSchema,parseSnapshot,isAttestation,type Attestation} from '../src/schemas';
import {fetchSnapshot,submitIntention} from '../src/api';
import {attestationKey,type Stage} from '../src/acceptance';
import {HumanContent,HumanProvider} from '../src/human';
import {Content} from '../src/ui';
import {router as existingRouter} from '../src/router';

const fixture=():Attestation=>AttestationSchema.parse({projection_contract:'ATTESTATION_FOUNDATION_V1',evidence_id:'r2-a9-auth-process',
  evidence_type:'SCOPED_IN_PROCESS',source:'SYNTHETIC ISOLATED TEST',scope:'R2-A8:ATTESTATION:ONE_GENERATION',
  created_at:'2026-10-08T00:00:00Z',status:'NOT_VERIFIED',evidence_version:'a'.repeat(64),live_actions:'LOCKED',operator_policy:'NOT_PROVISIONED',
  binding:{scope:'R2-A8:ATTESTATION:ONE_GENERATION',target:'127.0.0.1:8000',pid:123,process_start:134000000000000000,
    runtime_instance:'fixture-instance',source_snapshot:'fixture-source',scoped_loaded_code:'fixture-loaded',configuration_digest:'b'.repeat(64),
    endpoint:{origin:'http://127.0.0.1:11434',connection_origin:'http://127.0.0.1:11434'},profile:'ATTESTATION',
    active_process_build:'NOT_DIRECTLY_VERIFIED',runtime_identity:'NOT_VERIFIED'},reviews:[],provider_receipt:null});
const pending=(s:Attestation)=>({review_id:'fixture-review',scope:s.scope,evidence_version:s.evidence_version,state:'PENDING',expires_at:'2026-10-08T00:02:00Z'});
function Harness({state=fixture(),initial='System'}:{state?:Attestation;initial?:Stage}){
  const [stage,setStage]=useState<Stage>(initial);
  return <HumanProvider><button onClick={()=>setStage('Decision')}>Go Decision</button><HumanContent stage={stage} state={state} navigate={setStage} inspectRuntime={()=>{}}/></HumanProvider>;
}
function review(){
  fireEvent.click(screen.getByLabelText('I have read the ATTESTATION scope and limitations.'));
  fireEvent.click(screen.getByRole('button',{name:'Continue to Evidence'}));
  fireEvent.click(screen.getByLabelText('I inspected the exact evidence version and identity scope.'));
  fireEvent.click(screen.getByRole('button',{name:'Continue to Human Test'}));
  for(const id of ['runtime','separate','boundary'])fireEvent.click(within(screen.getByRole('group',{name:`Observation ${id}`})).getByRole('button',{name:'PASS'}));
  fireEvent.click(screen.getByRole('button',{name:'Continue to Review'}));
  fireEvent.click(screen.getByLabelText('I reviewed these observations and the NOT_VERIFIED limitations.'));
  fireEvent.click(screen.getByRole('button',{name:'Continue to Decision'}));
}
afterEach(()=>vi.unstubAllGlobals());
describe('separate scoped ATTESTATION integration',()=>{
  it('accepts actual guarded in-process backend projection and intention',()=>{
    const evidence=readSnapshotFile('R2_CPLANE_ISOLATED_EVIDENCE') as {live_http:boolean;dispatch_count:number;snapshot:unknown;intention:{state:string}};
    expect(evidence.live_http).toBe(false);expect(evidence.dispatch_count).toBe(0);
    expect(AttestationSchema.parse(evidence.snapshot).status).toBe('NOT_VERIFIED');
    expect(evidence.intention.state).toBe('PENDING');
  });
  it('accepts ATTESTATION and preserves NORMAL without masquerading',()=>{
    const s=fixture();expect(isAttestation(parseSnapshot(s))).toBe(true);expect(()=>SystemHealthSchema.parse(s)).toThrow();
    const normal=SystemHealthSchema.parse(readSnapshotFile());
    expect(isAttestation(parseSnapshot(normal))).toBe(false);expect(()=>AttestationSchema.parse(normal)).toThrow();
    expect(()=>parseSnapshot({...normal,projection_contract:'UNKNOWN'})).toThrow();
    expect(()=>parseSnapshot({...s,schema_version:1})).toThrow();
  });
  it.each(['PASS','READY','AUTHORIZED','ACTIVE','VERIFIED'])('rejects invented status %s',status=>expect(()=>parseSnapshot({...fixture(),status})).toThrow());
  it('uses the typed snapshot fetch and fixed intention body only',async()=>{
    const s=fixture(),fetch=vi.fn().mockResolvedValueOnce({ok:true,json:async()=>s}).mockResolvedValueOnce({ok:true,json:async()=>pending(s)});
    vi.stubGlobal('fetch',fetch);expect(isAttestation((await fetchSnapshot()).state)).toBe(true);
    expect((await submitIntention(s)).state).toBe('PENDING');
    const options=fetch.mock.calls[1][1];expect(JSON.parse(options.body)).toEqual({scope:s.scope,evidence_version:s.evidence_version});
    expect(options.method).toBe('POST');expect(options.credentials).toBe('omit');
  });
  it('rejects authorization responses, stale binding and failure without retry',async()=>{
    const s=fixture();const fetch=vi.fn().mockResolvedValue({ok:true,json:async()=>({...pending(s),state:'APPROVED'})});vi.stubGlobal('fetch',fetch);
    await expect(submitIntention(s)).rejects.toThrow();expect(fetch).toHaveBeenCalledTimes(1);
    fetch.mockResolvedValue({ok:true,json:async()=>({...pending(s),evidence_version:'c'.repeat(64)})});await expect(submitIntention(s)).rejects.toThrow('context mismatch');
    fetch.mockResolvedValue({ok:false,status:409});await expect(submitIntention(s)).rejects.toThrow('No authority granted');
  });
  it('invalidates material changes but not capture time',()=>{
    const s=fixture();expect(attestationKey({...s,created_at:'2026-10-08T00:01:00Z'})).toBe(attestationKey(s));
    expect(attestationKey({...s,evidence_version:'c'.repeat(64)})).not.toBe(attestationKey(s));
    expect(attestationKey({...s,reviews:[{review_id:'x',state:'PENDING',expires_at:'2026-10-08T00:02:00Z'}]})).not.toBe(attestationKey(s));
  });
  it('renders scoped evidence in every engineering view without historical gates',()=>{
    render(<Content name="Runtime" state={fixture()}/>);expect(screen.getAllByText('NOT_VERIFIED').length).toBeGreaterThan(0);
    expect(screen.getByText('NOT_DIRECTLY_VERIFIED')).toBeInTheDocument();expect(screen.getByText('SCOPED_IN_PROCESS')).toBeInTheDocument();
    expect(screen.queryByText('R3.1')).not.toBeInTheDocument();expect(screen.queryByText('PASS')).not.toBeInTheDocument();
  });
  it('blocks bypass, separates observations and only submits on an explicit click',async()=>{
    const s=fixture(),fetch=vi.fn().mockResolvedValue({ok:true,json:async()=>pending(s)});vi.stubGlobal('fetch',fetch);
    render(<Harness state={s}/>);expect(fetch).not.toHaveBeenCalled();review();expect(fetch).not.toHaveBeenCalled();
    expect(screen.queryByRole('button',{name:'APPROVE'})).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button',{name:'Create PENDING intention'}));
    await waitFor(()=>expect(screen.getByRole('status')).toHaveTextContent('PENDING — untrusted intention'));
    expect(screen.getByRole('button',{name:'Create PENDING intention'})).toBeDisabled();expect(fetch).toHaveBeenCalledTimes(1);
    expect(screen.getAllByText('NOT_VERIFIED').length).toBeGreaterThan(0);
  });
  it('uses the existing router, snapshot API and scoped navigation end to end in jsdom',async()=>{
    const s=fixture(),fetch=vi.fn().mockResolvedValue({ok:true,json:async()=>s});vi.stubGlobal('fetch',fetch);
    const router=createRouter({routeTree:existingRouter.routeTree,history:createMemoryHistory({initialEntries:['/overview']})});
    render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><RouterProvider router={router}/></QueryClientProvider>);
    fireEvent.click(await screen.findByRole('button',{name:'Buka detail teknis'}));
    await waitFor(()=>expect(screen.getByText('SCOPED_IN_PROCESS')).toBeInTheDocument());
    fireEvent.click(screen.getByLabelText('I have read the ATTESTATION scope and limitations.'));
    fireEvent.click(screen.getByRole('button',{name:'Continue to Evidence'}));
    await waitFor(()=>expect(router.state.location.pathname).toBe('/evidence'));
    fireEvent.click(await screen.findByRole('button',{name:'Buka detail teknis'}));
    await waitFor(()=>expect(screen.getByText('Evidence boundary')).toBeInTheDocument());
    expect(router.state.location.pathname).toBe('/evidence');
    // Technical pages remain reachable from the operator shell, but a direct
    // route must still enforce the scoped review prerequisites.
    await router.navigate({to:'/test'});
    fireEvent.click(await screen.findByRole('button',{name:'Buka detail teknis'}));
    await waitFor(()=>expect(screen.getByRole('region',{name:'Locked stage'})).toBeInTheDocument());
    expect(fetch.mock.calls.every(call=>!call[1].method||call[1].method==='GET')).toBe(true);
  });
  it('clears reviewed context on drift',()=>{
    const s=fixture();const {rerender}=render(<Harness state={s}/>);review();
    rerender(<Harness state={{...s,evidence_version:'c'.repeat(64)}}/>);
    expect(screen.getByRole('region',{name:'Locked stage'})).toBeInTheDocument();
  });
  it('rejects opening Decision without observations',()=>{render(<Harness initial="Decision"/>);expect(screen.getByRole('region',{name:'Locked stage'})).toBeInTheDocument();});
});
