import {useMemo,useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {Link} from '@tanstack/react-router';
import {fetchKnowledgePipelineStatus,type KnowledgePipelineStatus,type SOPWorkflowState} from './api';
import {useAdminAuth} from './auth';
import './sop-progress.css';

const states:Record<SOPWorkflowState,string>={ACTIVE:'Aktif',QUEUED:'Mengantre',PROCESSING:'Sedang diproses',REVIEW_REQUIRED:'Perlu diperiksa',APPROVAL_REQUIRED:'Siap disetujui',BLOCKED:'Perlu ditangani',UNKNOWN:'Belum terbaca'};
const steps:Record<string,string>={source:'File sumber',extraction:'Ekstraksi',cleaning:'Pembersihan teks',indexing:'Indeks pencarian',review:'Pemeriksaan isi dan metadata',approval:'Persetujuan',availability:'Tersedia untuk chat'};
const readings:Record<string,string>={SUCCEEDED:'Selesai',RUNNING:'Berjalan',WAITING:'Menunggu',FAILED:'Perlu ditangani',UNKNOWN:'Belum diverifikasi'};
export const reviewSelectionKey='nusantara-review-document-pending';

export function SOPProgressPanel({data,onSelect,onRetry,busy=false}:{data:KnowledgePipelineStatus;onSelect?:(id:string)=>void;onRetry?:(id:string)=>void;busy?:boolean}){
 const [search,setSearch]=useState('');
 const summary=data.sop_summary;
 if(!summary)return <p>Ringkasan SOP belum disediakan backend. Muat ulang setelah backend diperbarui.</p>;
 const counts=summary.counts;
 const documents=(data.documents??[]).filter(doc=>`${doc.title} ${doc.review_status??''}`.toLocaleLowerCase().includes(search.toLocaleLowerCase()));
 return <>
  <p>Jumlah dokumen menurut status versi saat ini. Aktif berarti disetujui untuk digunakan; ketepatan seluruh jawaban model perlu diuji terpisah.</p>
  <dl className="sop-progress-counts">{[['Dokumen tersimpan',summary.total],['Aktif',counts.ACTIVE],['Mengantre / diproses',counts.QUEUED+counts.PROCESSING],['Perlu diperiksa',counts.REVIEW_REQUIRED],['Siap disetujui',counts.APPROVAL_REQUIRED],['Perlu ditangani',counts.BLOCKED],['Belum terbaca',counts.UNKNOWN]].map(([label,count])=><div key={label}><dt>{label}</dt><dd>{count}</dd></div>)}</dl>
  <label className="sop-progress-search">Cari SOP tersimpan<input type="search" value={search} onChange={e=>setSearch(e.target.value)} placeholder="Judul atau status SOP"/></label>
  {!summary.total?<p>Belum ada dokumen tersimpan. Tambahkan dokumen melalui Kelola dokumen.</p>:!documents.length?<p>Tidak ada SOP yang cocok.</p>:<div className="table-scroll"><table className="sop-progress-table"><thead><tr><th>Dokumen</th><th>Progres saat ini</th><th>Langkah berikutnya</th></tr></thead><tbody>{documents.map(doc=>{
   const workflow=doc.workflow;
   return <tr key={doc.document_id}><td><strong>{doc.title}</strong></td><td><span className={`sop-progress-state ${workflow?.state??'UNKNOWN'}`}>{states[workflow?.state??'UNKNOWN']}</span><p>{doc.review_status??'Status belum tersedia'}</p>
    {workflow&&<details><summary>Detail tahapan</summary><dl>{Object.entries(steps).map(([key,label])=><div key={key}><dt>{label}</dt><dd>{readings[workflow.stages[key]]??'Belum diverifikasi'}</dd></div>)}</dl><p>Pembersihan: {workflow.cleaning_profile??'Profil belum tercatat; tidak diasumsikan sudah dijalankan.'}</p><p>{workflow.reason}</p></details>}
   </td><td>{workflow?.next_action==='chat'?<Link to="/" onClick={()=>{sessionStorage.setItem('nusantara-chat-document-pending',doc.document_id);sessionStorage.removeItem('nusantara-chat-sop-version-pending');}}>Buka chat</Link>:<>
    {workflow?.next_action==='wait'&&<p>Pemrosesan berjalan otomatis. Tidak perlu unggah ulang.</p>}
    {onSelect?<button disabled={busy} onClick={()=>onSelect(doc.document_id)}>{workflow?.next_action==='prepare'?'Buka pemrosesan':'Periksa dokumen'}</button>:<Link to="/knowledge" onClick={()=>sessionStorage.setItem(reviewSelectionKey,doc.document_id)}>Periksa dokumen</Link>}
   </>}</td></tr>;
  })}</tbody></table></div>}
  {summary.failed_sources.length>0&&<details className="sop-progress-failures"><summary>Percobaan impor yang masih gagal ({summary.failed_sources.length} sumber)</summary><p>Hanya percobaan terbaru per file sumber. Riwayat kegagalan lama bukan jumlah SOP yang rusak.</p><ul>{summary.failed_sources.map(run=><li key={run.run_id}><strong>{run.filename}</strong><p>{run.reason??'Penyebab belum tersedia'}</p>{onRetry&&run.retryable?<button disabled={busy} onClick={()=>onRetry(run.run_id)}>Coba proses lagi</button>:<Link to="/knowledge">Kelola dokumen</Link>}</li>)}</ul></details>}
  <p>Diperiksa: {new Date(data.checked_at).toLocaleString('id-ID')} · Sumber: knowledge Nusantara saat ini.</p>
 </>;
}

export function SOPProgressOverview(){
 const {token}=useAdminAuth();
 const scope=useMemo(()=>crypto.randomUUID(),[token]);
 const query=useQuery({queryKey:['sop-overview',scope],queryFn:()=>fetchKnowledgePipelineStatus(token),enabled:!!token.trim(),retry:false,gcTime:0,refetchInterval:30000});
 return <section className="panel" aria-label="Progres SOP"><h2>Progres seluruh SOP</h2>
  {!token.trim()?<p>Masukkan token operator di Pengaturan &amp; Teknis untuk melihat progres SOP.</p>:query.isPending?<p role="status">Membaca progres SOP…</p>:query.isError?<div role="alert"><p>Progres SOP belum dapat dibaca: {query.error.message}</p><button onClick={()=>void query.refetch()}>Coba lagi</button></div>:query.data?<SOPProgressPanel data={query.data}/>:<p>Ringkasan SOP belum tersedia.</p>}
  <Link to="/knowledge">Kelola dokumen</Link>
 </section>;
}
