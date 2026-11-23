import {useEffect,useRef,useState,type ReactNode} from 'react';
import type {EvidencePackage,ExecutionContext} from './api';
import {plainReason,type Check} from './readiness';

export function StatusPill({status}:{status:string}){
 const tone=['PASS','VALID','READY','AVAILABLE'].includes(status)?'positive':['FAIL','INVALID','ERROR'].includes(status)?'negative':'caution';
 return <span className={`op-status ${tone}`}>{status.replaceAll('_',' ')}</span>;
}
export function OperatorDrawer({title,open,onClose,children}:{title:string;open:boolean;onClose:()=>void;children:ReactNode}){
 const dialog=useRef<HTMLDialogElement>(null);
 useEffect(()=>{if(open&&!dialog.current?.open)dialog.current?.showModal();else if(!open&&dialog.current?.open)dialog.current.close();},[open]);
 return <dialog ref={dialog} className="operator-drawer" aria-label={title} onClose={onClose} onClick={e=>{if(e.target===e.currentTarget)dialog.current?.close();}}>
  <div className="drawer-heading"><div><p className="eyebrow">NUSANTARA V1 · DETAIL OPERATOR</p><h2>{title}</h2></div><button aria-label="Tutup detail" onClick={()=>dialog.current?.close()}>Tutup ×</button></div><div className="drawer-content">{children}</div>
 </dialog>;
}
export function DetailDrawer({label,children}:{label:string;children:ReactNode}){
 const [open,setOpen]=useState(false);
 return <><button className="detail-trigger" onClick={()=>setOpen(true)}>{label} ↗</button><OperatorDrawer title={label} open={open} onClose={()=>setOpen(false)}>{children}</OperatorDrawer></>;
}
export function PlanDetails({plan}:{plan:ExecutionContext}){return <>
 <p className="eyebrow">{plan.change_id}</p><h3>{plan.objective}</h3><p>Dampak: {plan.expected_change}</p>
 <dl className="op-specs"><div><dt>Risiko</dt><dd>{plan.risk}</dd></div><div><dt>Operasi</dt><dd>{plan.operation}</dd></div><div><dt>Sumber</dt><dd>{plan.source}</dd></div><div><dt>Diperiksa</dt><dd>{plan.checked_at}</dd></div></dl>
 <h3>Berkas target</h3>{plan.target_files.length?<ul>{plan.target_files.map(f=><li key={f}>{f}</li>)}</ul>:<p>Belum tersedia.</p>}
 <h3>Pengujian yang diwajibkan</h3><ul>{plan.tests_required.map(t=><li key={t}>{t}</li>)}</ul><h3>Pemulihan</h3><p>{plan.rollback}</p><h3>Identitas rencana</h3><pre>{JSON.stringify(plan.plan_binding,null,2)}</pre>
 </>;}
export function ReadinessTrack({checks}:{checks:Check[]}){return <section className="panel op-readiness" aria-label="Alur kesiapan"><div className="op-section-head"><div><h2>Alur kesiapan</h2><p>Setiap keputusan punya prasyarat yang bisa ditelusuri.</p></div><span>{checks.filter(c=>c.status==='READY').length} / {checks.length} pemeriksaan siap</span></div>
 <div className="op-gate-track">{checks.map((c,i)=><div key={c.id} className="op-gate"><span className="op-gate-number">{c.status==='READY'?'✓':`0${i+1}`}</span><DetailDrawer label={c.label}><StatusPill status={c.status}/><h3>{c.label}</h3><p>{c.detail}</p><h3>Prasyarat dan langkah berikutnya</h3><p>{c.why}</p><p>Sumber: evidence-package, execution-context dan history backend. Aturan memakai readiness V1 existing; tidak memakai dependensi gate demo.</p></DetailDrawer><StatusPill status={c.status}/></div>)}</div>
 <p className="op-hint">Evidence, rencana, autentikasi, keputusan dan izin eksekusi dinilai terpisah. Backend memeriksa ulang setiap mutasi.</p></section>;}
export function EvidenceRegistry({pkg}:{pkg:EvidencePackage}){
 const [filter,setFilter]=useState('ALL');
 const statuses=[...new Set(pkg.evidence.map(e=>e.validation_status))];
 const rows=pkg.evidence.filter(e=>filter==='ALL'||e.validation_status===filter);
 function exportPackage(){
  const url=URL.createObjectURL(new Blob([JSON.stringify({source:'/v1/control-plane/evidence-package',exported_at:new Date().toISOString(),package:pkg},null,2)],{type:'application/json'}));
  const link=document.createElement('a');link.href=url;link.download=`nusantara-evidence-${pkg.package_id}.json`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 }
 return <section className="panel op-evidence" aria-label="Paket evidence"><div className="op-section-head"><div><h2>Paket evidence</h2><p>Asal, lingkup dan hasil mengikuti registry backend.</p></div><div className="op-button-row"><StatusPill status={pkg.runtime_status}/><button onClick={exportPackage}>Ekspor JSON</button></div></div>
 <div className="op-filter"><div className="op-chips" role="group" aria-label="Filter evidence">{['ALL',...statuses].map(s=><button key={s} aria-pressed={filter===s} onClick={()=>setFilter(s)}>{s==='ALL'?'Semua':s}</button>)}</div><span>{rows.length} evidence</span></div>
 <div className="table-scroll"><table><thead><tr><th>Evidence</th><th>Jenis / sumber</th><th>Status</th><th>Pembacaan paket</th><th>Detail</th></tr></thead><tbody>{rows.map(e=><tr key={`${e.id}-${e.path}`}><td><strong>{e.id}</strong><small>{e.path}</small></td><td>{e.classification}<small>Registry backend · bukan inferensi baru</small></td><td><StatusPill status={e.validation_status}/></td><td>{pkg.generated_at}</td><td><DetailDrawer label={`Evidence ${e.id}`}><StatusPill status={e.validation_status}/><p>{e.reason?plainReason(e.reason):'Tidak ada alasan tambahan dari backend.'}</p><h3>Asal dan lingkup</h3><p>{e.classification} · {pkg.read_scope}</p><p>Path: <code>{e.path}</code></p><p>Paket: <code>{pkg.package_id}</code></p><p>Pembacaan paket: {pkg.generated_at}. Waktu pengujian per artefak dan task/request ID belum disediakan kontrak ini.</p><h3>Hasil dan integritas</h3><p>SHA-256: <code>{e.sha256??'Belum tersedia'}</code></p><p>Ukuran: {e.bytes??'Belum tersedia'}</p>{e.results_path&&<p>Hasil: <code>{e.results_path}</code></p>}{e.result_artifacts?.map(a=><p key={a.path}>{a.path}<code>{a.sha256}</code></p>)}<p>Klasifikasi registry tidak dengan sendirinya membuktikan inferensi model, retrieval RAG, atau laporan operator. Periksa artefak sumber sebelum menarik kesimpulan.</p></DetailDrawer></td></tr>)}</tbody></table></div>
 {!rows.length&&<div className="op-empty"><h3>Tidak ada evidence pada filter ini</h3><p>Pilih Semua untuk melihat inventaris yang dikembalikan backend.</p></div>}
 <p className="operator-source">Sumber: /v1/control-plane/evidence-package · lingkup {pkg.read_scope}</p></section>;
}
export function BlockerRegistry({pkg,onEvidence}:{pkg:EvidencePackage;onEvidence:()=>void}){
 const [filter,setFilter]=useState('open'),[search,setSearch]=useState('');
 const rows=filter==='closed'?[]:pkg.blockers.filter(b=>`${b.id} ${b.reason}`.toLowerCase().includes(search.toLowerCase()));
 return <section className="panel" aria-label="Masalah dan blocker"><div className="op-section-head"><div><h2>Masalah &amp; blocker</h2><p>Klik masalah untuk memahami dampak, prasyarat dan evidence terkait.</p></div><span>{pkg.blockers.length} tercatat</span></div>
 <div className="op-filter"><div className="op-chips" role="group" aria-label="Filter blocker">{[['open','Terbuka'],['closed','Selesai'],['all','Semua']].map(([id,label])=><button key={id} aria-pressed={filter===id} onClick={()=>setFilter(id)}>{label}</button>)}</div><label>Cari blocker<input type="search" value={search} onChange={e=>setSearch(e.target.value)}/></label></div>
 {filter==='closed'&&<p className="op-hint">Riwayat penyelesaian blocker belum tersedia pada endpoint ini. Status selesai tidak disimpulkan dari hilangnya blocker.</p>}
 {rows.map(b=><article className="op-blocker-row" key={b.id}><span className="op-row-icon" aria-hidden="true">!</span><div><h3>{b.id}</h3><p>{plainReason(b.reason)}</p><small>Paket penerimaan · {pkg.generated_at}</small></div><DetailDrawer label={`Detail blocker ${b.id}`}><StatusPill status="BLOCKED"/><p className="op-lead">{plainReason(b.reason)}</p><h3>Dampak pada alur</h3><p>Penerimaan paket mengikuti kriteria yang belum terpenuhi. Hubungan spesifik blocker dengan tugas, prioritas dan gate runtime belum disediakan backend.</p><h3>Penyebab / hipotesis</h3><p>Belum diketahui. Alasan backend di atas bukan diagnosis akar masalah.</p><h3>Langkah penelusuran</h3><ol><li>Periksa alasan dan waktu pembacaan paket.</li><li>Tinjau kriteria yang terkait; jika pemetaan spesifik tidak tersedia, periksa seluruh kriteria belum valid.</li><li>Baca artefak evidence sebelum meninjau keputusan di Human Control.</li></ol><h3>Prasyarat dari paket</h3>{pkg.criteria.filter(c=>c.id===b.id||c.status!=='VALID').map(c=><div className="op-requirement" key={c.id}><strong>{c.id} · {c.summary}</strong><StatusPill status={c.status}/><p>{c.evidence.join(', ')||'Referensi belum tersedia'}</p></div>)}<h3>Evidence terkait</h3><p>Pemetaan langsung blocker ke artefak belum tersedia. Inventaris dapat ditelusuri pada tab Evidence.</p><button onClick={onEvidence}>Buka tab Evidence</button><p className="operator-source">/v1/control-plane/evidence-package · {pkg.read_scope} · {pkg.generated_at}</p><code>{pkg.package_id}</code><p>Task/request ID belum tersedia pada kontrak blocker. Tidak ada kontrol simulasi penyelesaian di mode aktual.</p></DetailDrawer></article>)}
 {!rows.length&&<div className="op-empty"><h3>Tidak ada blocker pada tampilan ini</h3><p>Filter hanya membaca paket backend yang tersedia.</p></div>}</section>;
}
