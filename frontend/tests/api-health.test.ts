import {afterEach,expect,it,vi} from 'vitest';
import {fetchRuntimeHealth} from '../src/api';

afterEach(()=>vi.unstubAllGlobals());

it('GETs the existing relative /health route without operator credentials and returns HTTP status',async()=>{
 const fetchMock=vi.fn().mockResolvedValue(new Response(JSON.stringify({status:'ok',version:'0.1.0'}),{status:200}));
 vi.stubGlobal('fetch',fetchMock);
 const result=await fetchRuntimeHealth();
 expect(fetchMock).toHaveBeenCalledWith('/health',expect.objectContaining({credentials:'omit',cache:'no-store'}));
 expect(result).toEqual({status:'ok',version:'0.1.0',httpStatus:200});
});

it('reports the health route and HTTP error instead of returning a success payload',async()=>{
 const fetchMock=vi.fn().mockResolvedValue(new Response(JSON.stringify({status:'ok'}),{status:503}));
 vi.stubGlobal('fetch',fetchMock);
 await expect(fetchRuntimeHealth()).rejects.toThrow('GET /health gagal (HTTP 503)');
});

it('reports a clear connection error for a failed health request',async()=>{
 const fetchMock=vi.fn().mockRejectedValue(new TypeError('network unavailable'));
 vi.stubGlobal('fetch',fetchMock);
 await expect(fetchRuntimeHealth()).rejects.toThrow('GET /health gagal: koneksi ke Backend tidak berhasil');
});
