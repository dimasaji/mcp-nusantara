import {afterEach,expect,it,vi} from 'vitest';
import {uploadKnowledgeDocument} from '../src/api';
afterEach(()=>vi.unstubAllGlobals());
function file(){const file=new File(['upload contents'],'chosen.pdf');Object.defineProperty(file,'arrayBuffer',{value:async()=>new ArrayBuffer(15)});return file;}
it.each([
  [403,'ADMIN_TOKEN_INVALID',/Token operator ditolak/],
  [413,'FILE_TOO_LARGE_MAX_20MB',/File melebihi batas 20 MB/],
  [503,'KNOWLEDGE_PIPELINE_FAILED:RuntimeError',/Layanan pemrosesan dokumen belum tersedia/],
])('explains upload rejection %s without exposing internal codes',async(status,detail,message)=>{
  vi.stubGlobal('fetch',vi.fn(async()=>({ok:false,status,json:async()=>({detail})})));
  await expect(uploadKnowledgeDocument(file(),'fixture-token')).rejects.toThrow(message);
});
it('explains a network failure while allowing the selected file to be retried',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>{throw new TypeError('Failed to fetch');}));
  await expect(uploadKnowledgeDocument(file(),'fixture-token')).rejects.toThrow(/Koneksi upload terputus/);
});
