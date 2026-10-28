import {useEffect,useState} from 'react';
import {Link} from '@tanstack/react-router';
import {sendUserChat,type PublicChat} from './api';

type ReviewEvent={event_id:string;kind:string;note?:string;created_at:string;principal:string;problem_id?:string};
type Trial={trial_id:string;case_id:string;question:string;answer:PublicChat;principal?:string;created_at?:string;rating?:{ok:boolean;note:string;principal?:string;created_at?:string}|null};
type ApprovalRequirement={key:string;satisfied:boolean};
export type Review={document_id:string;title:string;version_id:string;status:string;source_available:boolean;source_type:string|null;text:string;pages:{page:number;start:number;end:number}[];content_ok:boolean;can_approve:boolean;problems:ReviewEvent[];events:ReviewEvent[];trials:Trial[];required_cases:string[];approval_requirements:ApprovalRequirement[];extraction?:{status:string;error?:string;warnings?:string[]};extracted_blocks?:{block_id:string;type:string;content:string;page_numbers:number[];related_pages?:number[];table_data?:{headers?:string[];rows?:string[][]};flowchart_nodes?:{row_number:string;column_header:string;bbox:number[]}[]}[]};
const cases:Record<string,{label:string;question:string}>={
  requirements:{label:'Persyaratan',question:'Apa persyaratan permohonan data pribadi dalam SOP ini?'},
  procedure:{label:'Prosedur',question:'Bagaimana prosedur permohonan data pribadi dalam SOP ini?'},
  time_cost:{label:'Waktu dan biaya',question:'Berapa waktu penyelesaian dan biaya menurut SOP ini? Jika tidak tercantum, jelaskan keterbatasannya.'},
  followup:{label:'Ringkasan lanjutan',question:'Ringkas penjelasan sebelumnya dengan bahasa sederhana, tetap berdasarkan SOP ini.'},
  missing:{label:'Informasi yang tidak ada',question:'Apakah SOP ini menyebutkan nomor WhatsApp petugas? Jika tidak ada, katakan belum ditemukan dalam SOP.'},
};
const approvalLabels:Record<string,string>={
  source_available:'File sumber tersedia',
  extraction_complete:'Ekstraksi Docling selesai',
  content_checked:'Pemeriksaan isi ditandai sesuai',
  all_trials_reviewed:'Semua percobaan dinilai sesuai atau masalahnya diselesaikan',
  no_open_problems:'Tidak ada masalah terbuka',
};
function approvalLabel(key:string){
  if(key.startsWith('case:'))return `Percobaan wajib: ${cases[key.slice(5)]?.label??key.slice(5)}`;
  return approvalLabels[key]??key;
}

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
  const [pdf,setPdf]=useState(''),[inspect,setInspect]=useState(true),[chat,setChat]=useState(false);
  const [sourcePage,setSourcePage]=useState(1);
  const [preview,setPreview]=useState(''),[previewError,setPreviewError]=useState('');
  const [showAllTrials,setShowAllTrials]=useState(false);
  const [sourceError,setSourceError]=useState(''),[sourceRevision,setSourceRevision]=useState(0);
  const [note,setNote]=useState(''),[report,setReport]=useState<string|null>(null),[caseId,setCaseId]=useState('requirements');
  const [question,setQuestion]=useState(cases.requirements.question),[session]=useState(()=>`sop-${crypto.randomUUID()}`);
  const id=encodeURIComponent(documentId);
  async function load(){setReview(await requestReview(id,token) as Review);}
  useEffect(()=>{
    let live=true;setReview(null);setError('');setPdf('');setInspect(true);setChat(false);setSourcePage(1);
    void requestReview(id,token).then(data=>{if(live)setReview(data as Review);}).catch(e=>{if(live)setError(e.message);});
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
    try{await action();await load();setReport(null);setNote('');}
    catch(e){setError(e instanceof Error?e.message:'Penyimpanan gagal. Muat ulang untuk memeriksa hasil.');}
    finally{setBusy(false);}
  }
  function decide(action:string,problem_id?:string){return requestReview(`${id}/decision`,token,{version_id:review!.version_id,action,note,problem_id});}
  async function ask(){
    await sendUserChat(question,`${session}-${review!.version_id.slice(0,12)}`,undefined,undefined,90000,
      {token,documentIds:[documentId],sopVersion:review!.version_id,sopCase:caseId});
  }
  if(!review)return <section className="panel" aria-label="Pemeriksaan SOP">{error?<p role="alert">{error}</p>:<p role="status">Memuat pemeriksaan SOP...</p>}<button onClick={()=>void act(load)} disabled={busy}>Muat ulang pemeriksaan</button></section>;
  const pageNumbers=Array.from(new Set([...review.pages.map(p=>p.page),...(review.extracted_blocks??[]).flatMap(b=>b.page_numbers)])).sort((a,b)=>a-b);
  const pageBlocks=(review.extracted_blocks??[]).filter(b=>b.page_numbers.includes(sourcePage));
  const unverifiedRatingCount=review.trials.filter(t=>t.rating?.principal==='shared-admin-token').length;
  return <section className="panel" aria-label="Pemeriksaan SOP">
    <h2>{review.title}</h2><p><strong>{review.status}</strong></p>
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
        <button disabled={busy} onClick={()=>void act(()=>decide('content_ok'))}>Isi sudah sesuai</button>
        <button disabled={busy} onClick={()=>setReport('content')}>Laporkan kesalahan</button>
      </>}
      </div><div className="sop-review-stage"><h3>2. Coba dan nilai jawaban</h3><p>Tanyakan isi SOP, buka halaman sumber, lalu tandai apakah jawabannya sesuai.</p>
      <button disabled={busy||(review.source_type==='.pdf'?review.extraction?.status!=='COMPLETE':!review.content_ok)} onClick={()=>setChat(true)}>Coba chat SOP ini</button>
      {review.extraction?.status==='COMPLETE'&&<Link to="/" onClick={()=>{sessionStorage.setItem('nusantara-chat-document-pending',documentId);sessionStorage.setItem('nusantara-chat-sop-version-pending',review.version_id);}}>Uji di chat utama</Link>}
      {!review.content_ok&&<p>Persetujuan isi belum diberikan. Percobaan teknis tersedia setelah ekstraksi lengkap; keputusan isi tetap oleh operator.</p>}
      {chat&&<><h3>Percobaan — belum aktif</h3><p>Percobaan terikat pada SOP dan versi di atas. Nilai seluruh jawaban, termasuk jawaban baru.</p>
        <label>Jenis percobaan<select disabled={busy} value={caseId} onChange={e=>{setCaseId(e.target.value);setQuestion(cases[e.target.value].question);}}>{review.required_cases.map(c=><option key={c} value={c}>{cases[c].label}</option>)}</select></label>
        <label>Pertanyaan SOP<textarea disabled={busy} value={question} maxLength={2000} onChange={e=>setQuestion(e.target.value)}/></label>
        <button disabled={busy||!question.trim()} onClick={()=>void act(ask)}>Kirim pertanyaan SOP</button>{!question.trim()&&<p>Isi pertanyaan terlebih dahulu.</p>}
      </>}
      <details open={chat}><summary>Hasil percobaan jawaban ({review.trials.length})</summary>
      {review.trials.length>10&&<button onClick={()=>setShowAllTrials(v=>!v)}>{showAllTrials?'Tampilkan 10 percobaan terbaru':`Tampilkan semua ${review.trials.length} percobaan`}</button>}
      {(showAllTrials?review.trials:review.trials.slice(-10)).map(t=><article key={t.trial_id}><h3>{cases[t.case_id]?.label}</h3><p>{t.question}</p><p style={{whiteSpace:'pre-wrap'}}>{t.answer.response}</p><p>Model: {t.answer.model}; sumber: {review.title}; versi: {review.version_id.slice(0,12)}</p>{t.answer.evidence.flatMap(e=>e.pages??[]).filter((p,i,a)=>a.indexOf(p)===i).map(page=><button key={page} disabled={busy} onClick={()=>{setSourcePage(page);setInspect(true);}}>Buka halaman {page}</button>)}<button disabled={busy} onClick={()=>setInspect(true)}>Buka sumber jawaban</button><p>{t.rating?t.rating.ok?'Jawaban sesuai':'Ada masalah':'Belum dinilai'}</p>
        <button disabled={busy} onClick={()=>void act(()=>requestReview(`${id}/trials/${t.trial_id}/rating`,token,{version_id:review.version_id,ok:true,note:''}))}>Jawaban sesuai</button>
        <button disabled={busy} onClick={()=>setReport(t.trial_id)}>Ada masalah</button></article>)}
      </details></div><div className="sop-review-stage"><h3>3. Keputusan operator</h3><p>{review.content_ok?'Isi sudah Anda nyatakan sesuai.':'Pemeriksaan isi belum dikonfirmasi.'} {review.problems.length} masalah masih terbuka.</p>
      {review.problems.map(p=><article key={p.event_id}><p>Masalah terbuka: {p.note}</p><button disabled={busy} onClick={()=>setReport(`resolve:${p.event_id}`)}>Catat penyelesaian masalah</button></article>)}
      {report&&<div role="region" aria-label="Catatan masalah"><label>Catatan wajib<textarea autoFocus value={note} maxLength={2000} onChange={e=>setNote(e.target.value)} disabled={busy}/></label><button disabled={busy||!note.trim()} onClick={()=>void act(()=>report==='content'?decide('problem'):report.startsWith('resolve:')?decide('resolve',report.slice(8)):requestReview(`${id}/trials/${report}/rating`,token,{version_id:review.version_id,ok:false,note}))}>Simpan catatan</button>{!note.trim()&&<p>Isi catatan sebelum menyimpan.</p>}<button disabled={busy} onClick={()=>setReport(null)}>Batal</button></div>}
      <section className="panel" aria-label="Syarat persetujuan"><h4>Syarat persetujuan</h4><ul>{review.approval_requirements.map(item=><li key={item.key}>{item.satisfied?'Terpenuhi:':'Belum terpenuhi:'} {approvalLabel(item.key)}</li>)}</ul>
        {unverifiedRatingCount>0&&<p role="note">{unverifiedRatingCount} rating tersimpan memakai token admin bersama; identitas penilainya tidak tercatat. Periksa kembali dan nilai ulang secara manual sebelum menyetujui.</p>}
      </section>
      <button disabled={busy||!review.can_approve||review.status==='Aktif'} onClick={()=>void act(()=>decide('approve'))}>Setujui untuk digunakan</button>
      {!review.can_approve&&<p>Persetujuan menunggu pemeriksaan isi, penilaian seluruh jawaban, lima jenis percobaan terbaru yang dinilai sesuai, dan penyelesaian masalah terbuka. Jawaban lama yang salah tetap tercatat; lakukan percobaan pengganti lalu catat penyelesaiannya.</p>}
      {review.status==='Aktif'&&<><p>Persetujuan versi ini tersimpan.</p><Link to="/" onClick={()=>{sessionStorage.setItem('nusantara-chat-document-pending',documentId);sessionStorage.removeItem('nusantara-chat-sop-version-pending');}}>Buka chat</Link></>}
      </div>
    </>}
    <details><summary>Riwayat pemeriksaan versi ini</summary>{review.events.length?review.events.map(e=><p key={e.event_id}>{e.created_at} · {e.kind} · {e.principal} · {e.note}</p>):<p>Belum ada keputusan operator.</p>}</details>
  </section>;
}
