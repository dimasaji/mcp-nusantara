import {useEffect,useRef,useState} from 'react';
import type {PublicChat} from './api';

/** Open only the revision bound to this saved answer; credentials stay in headers. */
export function ChatCitation({evidence,requestId,session,token}:{evidence:PublicChat['evidence'][number];requestId?:string;session:string;token:string}){
  const [source,setSource]=useState<{url:string;page:number}|null>(null);
  const [busy,setBusy]=useState(false),[error,setError]=useState('');
  const active=useRef<AbortController|null>(null),objectUrl=useRef('');
  useEffect(()=>{
    setSource(null);setError('');setBusy(false);
    return()=>{const controller=active.current;active.current=null;controller?.abort();if(objectUrl.current){URL.revokeObjectURL(objectUrl.current);objectUrl.current='';}};
  },[session,requestId,evidence.document_id,token]);
  async function open(page:number){
    if(!requestId||!token||active.current)return;
    setSource(null);if(objectUrl.current){URL.revokeObjectURL(objectUrl.current);objectUrl.current='';}
    const controller=new AbortController();active.current=controller;setBusy(true);setError('');
    const timer=setTimeout(()=>controller.abort(),30000);
    try{
      const query=new URLSearchParams({request_id:requestId,page_number:String(page)});
      const response=await fetch(`/v1/knowledge/pipeline/reviews/${encodeURIComponent(evidence.document_id)}/citation?${query}`,{
        headers:{'X-Admin-Token':token,'X-Chat-Session':session},credentials:'omit',redirect:'error',cache:'no-store',signal:controller.signal});
      if(!response.ok)throw new Error(response.status===409?'Versi atau persetujuan sumber berubah. Ajukan pertanyaan kembali untuk memperoleh sumber yang berlaku.':'Sumber belum dapat dibuka. Periksa akses dan riwayat jawaban.');
      if(!response.headers.get('content-type')?.startsWith('application/pdf'))throw new Error('Sumber halaman ini belum tersedia sebagai PDF.');
      const blob=await response.blob();
      if(!blob.size)throw new Error('File sumber kosong.');
      if(controller.signal.aborted)return;
      if(objectUrl.current)URL.revokeObjectURL(objectUrl.current);
      objectUrl.current=URL.createObjectURL(blob);setSource({url:objectUrl.current,page});
    }catch(e){if(!controller.signal.aborted)setError(e instanceof Error?e.message:'Sumber belum dapat dibuka.');else if(active.current===controller)setError('Pembacaan sumber terhenti. Coba kembali.');}
    finally{clearTimeout(timer);if(active.current===controller){active.current=null;setBusy(false);}}
  }
  return <details className="citation"><summary>{evidence.title}</summary>
    <small>Referensi: {evidence.document_id}</small>
    {evidence.pages?.length?<><p>Halaman: {evidence.pages.join(', ')}</p>{evidence.pages.map(page=><button key={page} type="button" disabled={busy||!requestId||!token} onClick={()=>void open(page)}>Buka halaman {page}</button>)}</>:<p>Halaman sumber belum tersedia.</p>}
    {(evidence.pages?.length??0)>0&&(!requestId||!token)&&<p>Akses operator dan riwayat jawaban yang tersimpan diperlukan untuk membuka sumber.</p>}
    {busy&&<p role="status">Memeriksa versi dan membuka sumber…</p>}{error&&<p role="alert">{error}</p>}
    {source&&<section aria-label={`Sumber ${evidence.title} halaman ${source.page}`}><a href={`${source.url}#page=${source.page}`} target="_blank" rel="noreferrer">Buka PDF pada halaman {source.page}</a><iframe title={`PDF ${evidence.title} halaman ${source.page}`} src={`${source.url}#page=${source.page}`} style={{width:'100%',height:480,border:0}}/></section>}
  </details>;
}
