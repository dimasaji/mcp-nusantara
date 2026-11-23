import {describe,it,expect,vi,afterEach} from 'vitest';
import {fetchSnapshot} from '../src/api';
afterEach(()=>vi.unstubAllGlobals());
describe('typed read-only API',()=>{
  it('rejects malformed evidence before rendering',async()=>{vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>({status:'PASS'})}));await expect(fetchSnapshot()).rejects.toThrow();});
  it('exposes failure instead of healthy dashboard',async()=>{vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false,status:503}));await expect(fetchSnapshot()).rejects.toThrow('503');});
  it('uses one allowlisted GET without credentials',async()=>{const fetch=vi.fn().mockResolvedValue({ok:false,status:500});vi.stubGlobal('fetch',fetch);await fetchSnapshot().catch(()=>{});expect(fetch).toHaveBeenCalledWith('/v1/control-plane/snapshot',expect.objectContaining({method:'GET',credentials:'omit'}));});
});
