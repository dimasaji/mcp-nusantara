import {useEffect,useMemo,useState} from 'react';
import {Link} from '@tanstack/react-router';
import {type PublicChat} from './api';
import {SOPMetadataForm,type OfficialMetadata} from './sop-metadata';

type ReviewEvent={event_id:string;kind:string;note?:string;created_at:string;principal:string;problem_id?:string;category?:string};
type Trial={trial_id:string;case_id:string;question:string;answer:PublicChat;principal?:string;created_at?:string;rating?:{ok:boolean;note:string;principal?:string;created_at?:string}|null};
type ApprovalRequirement={key:string;satisfied:boolean};
type VersionComparison={previous_version_id:string;version_id:string;changed_blocks:number;omitted_blocks:number;changes:{block_id:string;kind:string;pages:number[];before:string;after:string;excerpt_truncated:boolean}[]};
export type Review={material_binding?:string;operator_status?:string;next_action?:string;metadata_origin?:'system'|'operator';system_summary?:{passed:boolean;primary_issue:string|null;checks:{name:string;status:string;action:string}[];scenarios:{name:string;result:string;pages:number[]}[]}|null;official_metadata?:OfficialMetadata|null;metadata_event_id?:string|null;metadata_confirmed?:boolean;suggested_title?:string;comparison?:VersionComparison|null;publication_decision?:ReviewEvent|null;document_id:string;title:string;version_id:string;status:string;source_available:boolean;source_type:string|null;text:string;pages:{page:number;start:number;end:number}[];content_ok:boolean;can_approve:boolean;problems:ReviewEvent[];events:ReviewEvent[];trials:Trial[];required_cases:string[];approval_requirements:ApprovalRequirement[];extraction?:{status:string;error?:string;warnings?:string[]};extracted_blocks?:{block_id:string;type:string;content:string;page_numbers:number[];related_pages?:number[];table_data?:{headers?:string[];rows?:string[][]};flowchart_nodes?:{row_number:string;column_header:string;bbox:number[]}[]}[]};
const cases:Record<string,{label:string;question:string}>={
  requirements:{label:'Persyaratan',question:'Apa persyaratan menurut SOP ini?'},
  procedure:{label:'Prosedur',question:'Bagaimana prosedur menurut SOP ini?'},
  time_cost:{label:'Waktu dan biaya',question:'Berapa waktu penyelesaian dan biaya menurut SOP ini? Jika tidak tercantum, jelaskan keterbatasannya.'},
  followup:{label:'Ringkasan lanjutan',question:'Ringkas penjelasan sebelumnya dengan bahasa sederhana, tetap berdasarkan SOP ini.'},
  missing:{label:'Informasi yang tidak ada',question:'Apakah SOP ini menyebutkan nomor WhatsApp petugas? Jika tidak ada, katakan belum ditemukan dalam SOP.'},
};
const publicationActions={reject:'Tolak dokumen',defer:'Tunda keputusan',revoke:'Cabut dari Chat'};
type PublicationAction=keyof typeof publicationActions;
const correctionCategories:Record<string,string>={unknown:'Belum diketahui',extraction:'Pembacaan dokumen',retrieval:'Pencarian sumber',context:'Konteks percakapan',answer:'Penyusunan jawaban',claim_check:'Pemeriksaan klaim',citation_viewer:'Tampilan sitasi'};
const eventLabels:Record<string,string>={official_metadata:'Metadata resmi diperiksa',content_ok:'Isi dinyatakan sesuai',problem:'Masalah dilaporkan',resolve:'Masalah diselesaikan',rating:'Jawaban dinilai',approve:'Disetujui untuk digunakan',reject:'Dokumen ditolak',defer:'Keputusan ditunda',revoke:'Penggunaan di Chat dicabut'};
function ExtractedBlock({block}:{block:NonNullable<Review['extracted_blocks']>[number]}){
  const table=block.table_data;
  return <div><details><summary>Detail sumber blok</summary><small>{block.type} · {block.block_id} · halaman {block.page_numbers.join(', ')}</small></details>
    {table?.headers&&table.rows?<><p>Geser tabel ke kanan untuk melihat seluruh pelaksana dan hasil kegiatan.</p><div className="sop-table-scroll" tabIndex={0} role="region" aria-label="Tabel lengkap, dapat digeser"><table className="sop-source-table" aria-label={`Tabel SOP halaman ${block.page_numbers.join(', ')}`}><thead><tr>{table.headers.map((h,i)=><th key={i} scope="col">{h}</th>)}</tr></thead><tbody>{table.rows.map((r,i)=><tr key={i}>{r.map((cell,j)=><td key={j}>{cell}</td>)}</tr>)}</tbody></table></div></>:<pre style={{whiteSpace:'pre-wrap',maxHeight:450,overflow:'auto'}}>{block.content}</pre>}
    {!!block.related_pages?.length&&<p>Tabel berlanjut/terkait pada halaman {block.related_pages.join(', ')}.</p>}
    {!!block.flowchart_nodes?.length&&<details><summary>Marker bagan dari geometri PDF ({block.flowchart_nodes.length})</summary>{block.flowchart_nodes.map((n,i)=><p key={i}>Baris {n.row_number}: {n.column_header} · posisi PDF {n.bbox.map(v=>v.toFixed(1)).join(', ')}</p>)}<p>Alur panah dan cabang diperiksa pada PDF asli.</p></details>}
  </div>;
}

async function requestReview(path:string,token:string,body?:unknown,source=false){
  const controller=new AbortController();
  const timer=setTimeout(()=>controller.abort(),60000);
  try{
    const response=await fetch(`/v1/knowledge/pipeline/reviews/${path}`,{method:body?'POST':'GET',signal:controller.signal,cache:'no-store',credentials:'omit',redirect:'error',headers:{'X-Admin-Token':token,...(body?{'Content-Type':'application/json'}:{})},...(body?{body:JSON.stringify(body)}:{})});
    if(!response.ok){const error=await response.json().catch(()=>null);throw new Error(typeof error?.detail==='string'?error.detail:`Pemeriksaan gagal (${response.status}). Coba muat ulang.`);}
    if(source){const blob=await response.blob();if(!blob.size)throw new Error('File sumber kosong. Hubungi pengelola untuk memeriksa sumber asli.');return blob;}
    const data=await response.json();
    if(path.endsWith('/process')&&typeof data?.job_id==='string'&&typeof data?.status==='string')return data;
    if(!data||typeof data.document_id!=='string'||typeof data.version_id!=='string'||!Array.isArray(data.trials)||!Array.isArray(data.events))throw new Error('Respons pemeriksaan tidak lengkap. Muat ulang atau hubungi pengelola.');
    return data;
  }catch(error){if(controller.signal.aborted)throw new Error('Batas waktu pemeriksaan tercapai. Muat ulang status sebelum mencoba kembali.');throw error;}
  finally{clearTimeout(timer);}
}

export function SOPReviewPanel({documentId,token}:{documentId:string;token:string}){
  const [review,setReview]=useState<Review|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const [pdf,setPdf]=useState(''),[inspect,setInspect]=useState(true);
  const [sourcePage,setSourcePage]=useState(1);
  const [preview,setPreview]=useState(''),[previewError,setPreviewError]=useState('');
  const [publicationAction,setPublicationAction]=useState<PublicationAction|null>(null);
  const [category,setCategory]=useState('unknown');
  const [sourceError,setSourceError]=useState(''),[sourceRevision,setSourceRevision]=useState(0);
  const [note,setNote]=useState(''),[report,setReport]=useState<string|null>(null);
  const session=useMemo(()=>`web-${crypto.randomUUID()}`,[documentId,token,review?.version_id]);
  const id=encodeURIComponent(documentId);
  async function readReview(){
    const current=await requestReview(id,token) as Review;
    if(current.source_available&&(current.source_type!=='.pdf'||current.extraction?.status==='COMPLETE'))
    {
      await requestReview(`${id}/prepare`,token,{version_id:current.version_id});
      const prepared=await requestReview(id,token) as Review;
      if(prepared.version_id!==current.version_id)throw new Error('Versi sumber berubah. Muat ulang ringkasan.');
      return prepared;
    }
    return current;
  }
  async function load(){setReview(await readReview());}
  function openReport(value:string){setPublicationAction(null);setNote('');setCategory('unknown');setReport(value);}
  useEffect(()=>{
    let live=true;setReview(null);setError('');setPdf('');setInspect(true);setSourcePage(1);setPublicationAction(null);setNote('');setReport(null);
    void readReview().then(data=>{if(live)setReview(data as Review);}).catch(e=>{if(live)setError(e.message);});
    return()=>{live=false;};
  },[id,token]);
  useEffect(()=>{if(!['QUEUED','PROCESSING'].includes(review?.extraction?.status??''))return;const timer=setInterval(()=>void load().catch(e=>setError(e.message)),3000);return()=>clearInterval(timer);},[review?.extraction?.status,id,token]);
  useEffect(()=>{
    if(!inspect||!review?.source_available)return;
    let live=true,url='';setPdf('');setSourceError('');
    void requestReview(`${id}/source?version_id=${review.version_id}`,token,undefined,true).then(blob=>{url=URL.createObjectURL(blob as Blob);if(live)setPdf(url);else URL.revokeObjectURL(url);}).catch(e=>{if(live)setSourceError(e.message);});
    return()=>{live=false;if(url)URL.revokeObjectURL(url);};
  },[inspect,id,token,review?.version_id,sourceRevision]);
  useEffect(()=>{
    if(!inspect||!review?.source_available||review.source_type!=='.pdf')return;
    let live=true,url='';setPreview('');setPreviewError('');
    void requestReview(`${id}/source?version_id=${review.version_id}&page_number=${sourcePage}`,token,undefined,true).then(blob=>{
      url=URL.createObjectURL(blob as Blob);if(live)setPreview(url);else URL.revokeObjectURL(url);
    }).catch(e=>{if(live)setPreviewError(e.message);});
    return()=>{live=false;if(url)URL.revokeObjectURL(url);};
  },[inspect,id,token,review?.version_id,review?.source_type,sourceRevision,sourcePage]);
  async function act(action:()=>Promise<unknown>){
    if(busy)return;setBusy(true);setError('');
    try{await action();await load();setReport(null);setPublicationAction(null);setNote('');}
    catch(e){setError(e instanceof Error?e.message:'Penyimpanan gagal. Muat ulang untuk memeriksa hasil.');}
    finally{setBusy(false);}
  }
  function decide(action:string,problem_id?:string){return requestReview(`${id}/decision`,token,{version_id:review!.version_id,action,note,problem_id,...(action==='approve'?{material_binding:review!.material_binding}:{}),...(action==='problem'?{category}:{})});}
  if(!review)return <section className="panel" aria-label="Pemeriksaan SOP">{error?<p role="alert">{error}</p>:<p role="status">Memuat pemeriksaan SOP...</p>}<button onClick={()=>void act(load)} disabled={busy}>Muat ulang pemeriksaan</button></section>;
  const pageNumbers=Array.from(new Set([...review.pages.map(p=>p.page),...(review.extracted_blocks??[]).flatMap(b=>b.page_numbers)])).sort((a,b)=>a-b);
  const pageBlocks=(review.extracted_blocks??[]).filter(b=>b.page_numbers.includes(sourcePage));
  return <section className="panel" aria-label="Pemeriksaan SOP">
    <h2>{review.title}</h2><p><strong>{review.operator_status??review.status}</strong></p><p>{review.next_action}</p>
    {review.metadata_origin==='system'&&<p>Metadata dibaca dan disimpan oleh sistem. Koreksi hanya jika berbeda dari sumber.</p>}
    <SOPMetadataForm key={`${session}:${review.metadata_event_id??"new"}:${review.extraction?.status??"na"}:${(review.extracted_blocks??[]).length}`} documentId={documentId} origin={review.metadata_origin} metadata={review.official_metadata} eventId={review.metadata_event_id} pdf={review.source_type==='.pdf'} busy={busy||!review.source_available||(review.source_type==='.pdf'&&review.extraction?.status!=='COMPLETE')} extractedBlocks={review.extracted_blocks??[]} onSave={(metadata,expected_event_id)=>void act(()=>requestReview(`${id}/metadata`,token,{version_id:review.version_id,expected_event_id,metadata}))}/>
    {review.extraction&&<><p role="status">Pembacaan dokumen: <strong>{review.extraction.status==='COMPLETE'?'Selesai':review.extraction.status==='PROCESSING'||review.extraction.status==='QUEUED'?'Sedang diproses':'Perlu diperiksa'}</strong></p>{review.extraction.error&&<p role="alert">Masalah pembacaan SOP: {review.extraction.error}</p>}<details><summary>Perbaikan pembacaan dan detail teknis</summary><p>Ekstraksi Docling: {review.extraction.status}</p><p>Proses ulang diperlukan jika hasil pembacaan keliru. Mengajukan pertanyaan tidak memerlukan proses ulang.</p><button disabled={busy||['QUEUED','PROCESSING'].includes(review.extraction.status)} onClick={()=>void act(()=>requestReview(`${id}/process`,token,{version_id:review.version_id}))}>Proses ulang dengan Docling</button></details></>}
    <details><summary>Identitas dan versi</summary><p>ID: {documentId}</p><p>Versi isi: {review.version_id}</p><p>Reviewer menggunakan token admin bersama; nama pribadi tidak tersedia.</p></details>
    <button disabled={busy} onClick={()=>void act(load)}>Muat ulang pemeriksaan</button>
    {busy&&<p role="status">Memproses. Mohon tunggu sampai selesai.</p>}{error&&<p role="alert">{error}</p>}
    {!review.source_available?<p>File sumber belum ditemukan. Hubungi pengelola untuk menelusuri PDF asli melalui Evidence dan memulihkan file dengan hash yang sesuai.</p>:<>
      <div className="sop-review-stage"><h3>1. Bandingkan isi dengan PDF</h3><p>Periksa judul, persyaratan, pelaksana, urutan kegiatan, waktu, biaya, dan hasil layanan. Bagan tetap diperiksa pada PDF asli.</p>
      {!inspect&&<button disabled={busy} onClick={()=>setInspect(true)}>Periksa isi</button>}
      {inspect&&<>
        <nav className="sop-review-toolbar" aria-label="Halaman SOP">{pageNumbers.map(page=><button key={page} aria-pressed={page===sourcePage} onClick={()=>setSourcePage(page)}>Halaman {page}</button>)}</nav>
        {!pageNumbers.length&&<p>Pemetaan halaman belum tersedia; nomor halaman tidak direka.</p>}
        <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(min(100%,350px),1fr))',gap:16}}>
          <div>{pdf?<><a href={`${pdf}#page=${sourcePage}`} target="_blank" rel="noreferrer">Buka sumber asli halaman {sourcePage}</a>{review.source_type==='.pdf'&&(preview?<img title="PDF asli SOP" alt={`PDF asli SOP halaman ${sourcePage}`} data-source-page={sourcePage} src={preview} style={{width:'100%',height:'auto',border:'1px solid #888'}}/>:previewError?<><p role="alert">{previewError}</p><button onClick={()=>setSourceRevision(v=>v+1)}>Coba muat sumber lagi</button></>:<p role="status">Memuat pratinjau halaman {sourcePage}...</p>)}</>:sourceError?<><p role="alert">{sourceError}</p><button onClick={()=>setSourceRevision(v=>v+1)}>Coba muat sumber lagi</button></>:<p>Memuat file sumber...</p>}</div>
          <div className="sop-reading-pane" role="region" aria-label={`Hasil baca halaman ${sourcePage}`} tabIndex={0}><h3>Hasil baca halaman {sourcePage}</h3>{pageBlocks.length?pageBlocks.map(b=><ExtractedBlock key={b.block_id} block={b}/>):review.source_type!=='.pdf'?<pre style={{whiteSpace:'pre-wrap'}}>{review.text}</pre>:<p>Hasil baca halaman ini belum tersedia. Periksa PDF asli dan laporkan jika ada isi yang hilang.</p>}</div>
        </div>

        <button disabled={busy} onClick={()=>openReport('content')}>Laporkan kesalahan</button>
      </>}
      {review.comparison&&<details><summary>Perubahan dari hasil baca sebelumnya</summary><p>{review.comparison.changed_blocks} blok berubah. Periksa kembali PDF sebelum menyetujui; perubahan hasil baca tidak otomatis mengubah keputusan operator.</p><small>Versi sebelumnya: {review.comparison.previous_version_id}</small>{review.comparison.changes.map(change=><article key={change.block_id}><p>Halaman {change.pages.join(', ')} · {change.block_id}</p><p style={{whiteSpace:'pre-wrap'}}>Sebelumnya: {change.before||'(Tidak ada blok)'}</p><p style={{whiteSpace:'pre-wrap'}}>Sekarang: {change.after||'(Blok dihapus)'}</p>{change.excerpt_truncated&&<p>Cuplikan dipendekkan. Baca isi lengkap pada PDF.</p>}</article>)}{review.comparison.omitted_blocks>0&&<p>{review.comparison.omitted_blocks} blok lain tidak ditampilkan; periksa sumber lengkap.</p>}</details>}
      </div><div className="sop-review-stage"><h3>Penggunaan di Chat</h3>
      <p>Persetujuan Anda mengizinkan versi dokumen dan metadata yang ditampilkan sebagai sumber Chat. Persetujuan ini tidak menyatakan keabsahan hukum SOP.</p>
      {review.system_summary&&<p>Pemeriksaan sistem: {review.system_summary.passed?'Sumber siap digunakan.':review.system_summary.primary_issue}</p>}
      {review.status==='Aktif'&&<Link to="/" onClick={()=>{
        sessionStorage.setItem('nusantara-chat-document-pending',documentId);
        sessionStorage.setItem('nusantara-chat-approved-version-pending',review.version_id);
        sessionStorage.removeItem('nusantara-chat-sop-version-pending');
      }}>Coba chat SOP ini</Link>}
      {review.problems.filter(p=>p.kind==='problem').slice(0,1).map(p=><article key={p.event_id}><p>Masalah terbuka: {p.note}</p><p>Kategori: {correctionCategories[p.category??'unknown']??p.category}</p><button disabled={busy} onClick={()=>openReport(`resolve:${p.event_id}`)}>Catat penyelesaian masalah</button></article>)}
      {report&&<div role="region" aria-label="Catatan masalah"><label>Kategori masalah<select value={category} disabled={busy} onChange={e=>setCategory(e.target.value)}>{Object.entries(correctionCategories).map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label><label>Catatan wajib<textarea autoFocus value={note} maxLength={2000} onChange={e=>setNote(e.target.value)} disabled={busy}/></label><button disabled={busy||!note.trim()} onClick={()=>void act(()=>report==='content'?decide('problem'):decide('resolve',report.slice(8)))}>Simpan catatan</button>{!note.trim()&&<p>Isi catatan sebelum menyimpan.</p>}<button disabled={busy} onClick={()=>setReport(null)}>Batal</button></div>}
      <details><summary>Pemeriksaan sistem dan detail teknis</summary>
        <p>Hasil otomatis merupakan pemeriksaan sistem, bukan penilaian manusia. Model live belum dievaluasi oleh pemeriksaan sumber ini.</p>
        <p>ID: {documentId} / Versi: {review.version_id}</p>
        {review.system_summary?.checks.map(c=><p key={c.name}>{c.name}: {c.status}</p>)}
        {review.system_summary?.scenarios.map(c=><p key={c.name}>{cases[c.name]?.label??c.name}: {c.result} / halaman {c.pages.join(', ')}</p>)}
        <p>Riwayat percobaan: {review.trials.length}. Jumlah atau penilaian trial tidak mengubah persetujuan isi.</p>
        {review.trials.slice(-10).map(t=><article key={t.trial_id}><p>{t.question}</p><p>{t.answer.response}</p></article>)}
      </details>
      <button disabled={busy||!review.can_approve||!review.material_binding||review.status==='Aktif'} onClick={()=>void act(()=>decide('approve'))}>Setujui penggunaan di Chat</button>
      <div role="group" aria-label="Keputusan penggunaan dokumen">{(Object.keys(publicationActions) as PublicationAction[]).filter(action=>action!=='revoke'||review.publication_decision?.kind==='approve'||review.status==='Aktif').map(action=><button key={action} disabled={busy} onClick={()=>{setPublicationAction(action);setReport(null);setNote('');}}>{publicationActions[action]}</button>)}</div>
      {publicationAction&&<section aria-label="Alasan keputusan operator"><p>{publicationActions[publicationAction]}: dokumen tidak akan dipakai untuk jawaban baru di Chat utama. Pratinjau pemeriksaan tetap tersedia.</p><label>Alasan keputusan<textarea autoFocus value={note} maxLength={2000} disabled={busy} onChange={e=>setNote(e.target.value)}/></label><button disabled={busy||!note.trim()} onClick={()=>void act(()=>requestReview(`${id}/decision`,token,{version_id:review.version_id,action:publicationAction,note}))}>Simpan keputusan</button><button disabled={busy} onClick={()=>{setPublicationAction(null);setNote('');}}>Batal keputusan</button></section>}
      {review.publication_decision?.note&&<p>Alasan: {review.publication_decision.note}</p>}
      {!review.can_approve&&<p>{review.next_action??'Sistem sedang memeriksa kesiapan sumber.'}</p>}
      </div>
    </>}
    <details><summary>Riwayat pemeriksaan versi ini</summary>{review.events.length?review.events.map(e=><p key={e.event_id}>{e.created_at} · {eventLabels[e.kind]??e.kind} · {e.principal} · {e.note}</p>):<p>Belum ada keputusan operator.</p>}</details>
  </section>;
}

