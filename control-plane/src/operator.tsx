import {DetailDrawer} from './operator-panels';
export {DetailDrawer} from './operator-panels';
import {useMemo,useState} from 'react';
import {useQuery,useQueryClient} from '@tanstack/react-query';
import {Link} from '@tanstack/react-router';
import {fetchOperationsSummary,fetchCostSummary,fetchEvidencePackage,fetchExecutionHistory,fetchExecutionContext,fetchModelStatus,fetchSnapshot,fetchRuntimeHealth} from './api';
import {useAdminAuth} from './auth';
import {isAttestation} from './schemas';
import {plainReason} from './readiness';
import {EngineeringConsole} from './engineering-console';

export const operatorMenus=[
  ['/dashboard','Beranda'],['/workspace','AI Workspace'],
  ['/approvals','Human Control'],['/settings','Pengaturan & Teknis'],
] as const;
function RuntimeOverview(){
  const health=useQuery({queryKey:['runtime-health'],queryFn:fetchRuntimeHealth,retry:false,refetchInterval:30000});
  const snapshot=useQuery({queryKey:['control-plane','snapshot'],queryFn:({signal})=>fetchSnapshot(signal),retry:false});
  const state=snapshot.data&&!isAttestation(snapshot.data.state)?snapshot.data.state:undefined;
  const checked=Math.max(health.dataUpdatedAt,health.errorUpdatedAt);
  return <div className="runtime-overview"><section className="panel"><p className="eyebrow">KONDISI SISTEM</p><h2>Health &amp; koneksi</h2>
    {health.isPending?<p role="status">Membaca health…</p>:health.isError?<p role="alert">Belum tersedia — {health.error.message}</p>:<p className="health-reading">{health.data.status} <small>HTTP {health.data.httpStatus} · {health.data.service??'Backend'}</small></p>}
    <p>Pembacaan terakhir: {checked?new Date(checked).toLocaleString('id-ID'):'Belum tersedia'}. Pembacaan berkala setiap 30 detik; hasil gagal tidak membuktikan health terkini.</p>
    <DetailDrawer label="Detail health"><Source path="/health"/><p>Hasil: {health.isError?'Belum tersedia':health.data?.status??'Menunggu pembacaan'}</p><p>Versi: {health.data?.version??'Belum tersedia'}</p><p>Pembacaan: {checked?new Date(checked).toLocaleString('id-ID'):'Belum tersedia'}</p><p>Health backend tidak membuktikan inferensi atau kesiapan VPS. Periksa layanan lokal bila pembacaan gagal.</p><Link to="/settings">Buka pengaturan dan recovery</Link></DetailDrawer>
  </section><section className="panel"><p className="eyebrow">PEMERIKSAAN SISTEM</p><h2>Hasil pemeriksaan</h2>
    {snapshot.isPending?<p role="status">Membaca hasil pemeriksaan…</p>:snapshot.isError?<p role="alert">Belum tersedia — {snapshot.error.message}</p>:state?<><p>{state.gates.filter(g=>g.status==='PASS').length} dari {state.gates.length} pemeriksaan tercatat lulus.</p><p>Dicatat {state.timestamp}. Hasil tersimpan ini belum membuktikan layanan dan model berjalan saat ini.</p></>:<p>Hasil pemeriksaan lengkap belum tersedia pada mode ini.</p>}
    <DetailDrawer label="Detail teknis pemeriksaan"><Source path="/v1/control-plane/snapshot"/>{state?state.gates.map(g=><article key={g.id}><h3>{g.id} · {g.status}</h3><p>Evidence: {g.evidence.join(', ')||'Belum tersedia'}</p></article>):<p>Belum tersedia. Periksa evidence teknis dan kontrak proyeksi backend.</p>}<Link to="/approvals">Tinjau prasyarat keputusan</Link></DetailDrawer>
  </section></div>;
}
export function OperatorConnection(){
  const q=useQuery({queryKey:['operator','model'],queryFn:fetchModelStatus,retry:false});
  return <span role="status">{q.isPending?'Memeriksa koneksi…':q.isError?'Backend belum terhubung':`API terhubung · identitas ${q.data.status} · diperiksa ${new Date(q.dataUpdatedAt).toLocaleTimeString('id-ID')}`}<details><summary>Sumber pemeriksaan</summary><p>/v1/control-plane/model-status · proses {q.data?.process_id??'belum diketahui'}. Ketersediaan API tidak membuktikan identitas build aktif.</p></details></span>;
}
function useOperations(){
  const {token}=useAdminAuth();
  // Separate authorization contexts without putting credentials in query keys.
  const authKey=useMemo(()=>crypto.randomUUID(),[token]);
  const history=useQuery({queryKey:['operator','history',authKey],queryFn:()=>fetchExecutionHistory(token),enabled:!!token.trim(),retry:false,gcTime:0});
  const plan=useQuery({queryKey:['operator','plan',authKey],queryFn:()=>fetchExecutionContext(token),enabled:!!token.trim(),retry:false,gcTime:0});
  return {history,plan,authorized:!!token.trim()};
}
function Source({path}:{path:string}){return <p className="operator-source">Sumber: <code>{path}</code></p>}
function OperationCounts({kind}:{kind:'work'|'review'}){
  const {token}=useAdminAuth();const authKey=useMemo(()=>crypto.randomUUID(),[token]);
  const q=useQuery({queryKey:['operations-summary',authKey],queryFn:()=>fetchOperationsSummary(token),enabled:!!token.trim(),retry:false,gcTime:0});
  if(!token.trim())return <p>Masukkan token operator untuk membaca ringkasan.</p>;
  if(q.isPending)return <p role="status">Memuat ringkasan…</p>;
  if(q.isError)return <ErrorState error={q.error} retry={()=>void q.refetch()}/>;
  const count=kind==='work'?q.data.pending_work:q.data.pending_review;
  return <><p>{count===null?q.data.reason:count===0?kind==='work'?'Tidak ada pekerjaan tertunda':'Tidak ada rencana menunggu review':`${count} rencana ${kind==='work'?'belum selesai':'menunggu review'}`}</p><p>Cakupan: eksekusi terkontrol. Keputusan yang tercatat tetap diperiksa ulang backend sebelum eksekusi.</p></>;
}
function HomeCosts(){
  const {token}=useAdminAuth();const authKey=useMemo(()=>crypto.randomUUID(),[token]);
  const q=useQuery({queryKey:['home-costs',authKey],queryFn:()=>fetchCostSummary(token),enabled:!!token.trim(),retry:false,gcTime:0});
  return !token.trim()?<p>Token operator diperlukan untuk membaca biaya.</p>:q.isPending?<p role="status">Memuat biaya…</p>:q.isError?<ErrorState error={q.error} retry={()=>void q.refetch()}/>:q.data.status==='UNAVAILABLE'?<p>{q.data.reason}</p>:<p>Aktual USD {q.data.actual_usd??'belum tersedia'} · reservasi USD {q.data.reserved_usd??'belum tersedia'} · sisa anggaran USD {q.data.remaining_budget_usd??'belum tersedia'}.</p>;
}
function Missing({children}:{children:React.ReactNode}){return <p className="operator-missing">Belum tersedia — {children}</p>}
function ErrorState({error,retry}:{error:Error;retry:()=>void}){return <div role="alert" className="error"><p>{error.message}</p><button onClick={retry}>Coba lagi</button></div>}
function Activity(){
  const {history,authorized}=useOperations();
  return <section className="panel"><h2>Aktivitas terbaru</h2><Source path="/v1/control-plane/history"/>
    {!authorized?<Missing>masukkan token operator di Pengaturan &amp; Teknis untuk membaca history.</Missing>:history.isPending?<p role="status">Memuat aktivitas…</p>:history.isError?<ErrorState error={history.error} retry={()=>void history.refetch()}/>:history.data.executions.length===0?<p>Belum ada eksekusi pada history yang dibaca.</p>:<ul>{history.data.executions.slice(-5).reverse().map((e,i)=><li key={i}>{e.timestamp} · {e.change_id} · {e.result} <Link to="/tasks">Detail tugas</Link></li>)}</ul>}
  </section>;
}
function CurrentWork(){
  const {plan,history,authorized}=useOperations();
  if(!authorized)return <p>Rencana dan pekerjaan terakhir memerlukan token operator di Pengaturan &amp; Teknis.</p>;
  return <>{plan.isPending?<p role="status">Membaca rencana terbaru…</p>:plan.isError?<ErrorState error={plan.error} retry={()=>void plan.refetch()}/>:<><p>{plan.data.completed?'Tidak ada pekerjaan tertunda':'Ada rencana yang belum selesai'} dalam cakupan eksekusi terkontrol.</p><p>Rencana: {plan.data.objective} · {plan.data.change_id}. Tahap: {plan.data.completed?'selesai menurut backend':'rencana tersedia; aktivitas berjalan belum dibuktikan'}.</p></>}
    {history.data?.executions.at(-1)&&<p>Pekerjaan terakhir: {history.data.executions.at(-1)!.change_id} · {history.data.executions.at(-1)!.result} · {history.data.executions.at(-1)!.timestamp}</p>}
    <Source path="/v1/control-plane/execution-context dan /history"/></>;
}
export function OperatorHome(){
  const client=useQueryClient();
  const pkg=useQuery({queryKey:['operator','package'],queryFn:fetchEvidencePackage,retry:false});
  return <><header><div><p className="eyebrow">NUSANTARA · V1</p><h1>Beranda</h1><p>Pekerjaan, hambatan, keputusan, dan penggunaan.</p></div><button onClick={()=>void client.invalidateQueries({predicate:q=>['operator','operations-summary','home-costs'].includes(String(q.queryKey[0]))})}>Perbarui Beranda</button></header>
    <section className="service-focus"><div><p className="eyebrow">FOKUS LAYANAN · PIAK-03</p><h2>Periksa bukti. Tentukan langkah berikutnya.</h2><p>Telusuri tugas, hambatan, dan keputusan dari sumber V1. Kesiapan layanan mengikuti evidence backend.</p></div><Link to="/workspace" className="button-link">Buka workspace ↗</Link></section>
    <div className="operator-cards">
      <section className="panel"><h2>Apa yang sedang dikerjakan?</h2><OperationCounts kind="work"/><Missing>jumlah tugas aktif dan progres global belum disediakan backend.</Missing><CurrentWork/><Link to="/tasks">Buka Aktivitas Tugas →</Link></section>
      <section className="panel"><h2>Apa masalahnya?</h2>{pkg.isPending?<p role="status">Membaca blocker…</p>:pkg.isError?<ErrorState error={pkg.error} retry={()=>void pkg.refetch()}/>:<><p>{pkg.data.blockers.length} blocker dalam paket evidence ini; jumlah masalah aktif global belum tersedia.</p><p>{pkg.data.blockers[0]?plainReason(pkg.data.blockers[0].reason):'Tidak ada masalah pada paket yang dibaca.'}</p><p>Dampak: penerimaan hasil mengikuti kelengkapan evidence. Prioritas belum tersedia.</p></>}<Link to="/blockers">Buka Masalah &amp; Blocker →</Link></section>
      <section className="panel"><h2>Apa yang perlu saya setujui?</h2><OperationCounts kind="review"/><Missing>jumlah antrean keputusan global belum disediakan.</Missing><p>Tinjau penerimaan paket evidence dan izin eksekusi secara terpisah pada modul persetujuan.</p>{pkg.data&&<p>Paket saat ini: {pkg.data.criteria.length} kriteria, {pkg.data.evidence.length} referensi evidence. Runtime: {pkg.data.runtime_status}. Sumber: /v1/control-plane/evidence-package.</p>}<Link to="/approvals">Buka Persetujuan →</Link></section>
      <section className="panel"><h2>Berapa biayanya?</h2><HomeCosts/><Link to="/costs">Buka Biaya &amp; Model →</Link></section>
    </div><RuntimeOverview/><section className="panel"><h2>Dokumen dan Chat</h2><p>Tambahkan dokumen, periksa hasil pemrosesan, lalu gunakan sumbernya di Chat V1.</p><Link to="/knowledge">Kelola dokumen</Link> · <Link to="/">Buka Chat</Link></section><Activity/>
  </>;
}
export function TasksPage(){
  const {history,plan,authorized}=useOperations();
  return <><header><h1>Aktivitas Tugas</h1></header><section className="panel"><h2>Rencana eksekusi yang tersedia</h2><Source path="/v1/control-plane/execution-context"/>
    {!authorized?<Missing>token operator diperlukan. Buka Pengaturan &amp; Teknis.</Missing>:plan.isPending?<p role="status">Membaca rencana…</p>:plan.isError?<ErrorState error={plan.error} retry={()=>void plan.refetch()}/>:<><h3>{plan.data.change_id} · {plan.data.objective}</h3><p>Tahap: {plan.data.completed?'selesai menurut rencana backend':'rencana tersedia; belum membuktikan sedang berjalan'}</p><p>Diperiksa: {plan.data.checked_at} · Selesai: {plan.data.completed_at??'Belum tersedia'}</p><p>Hasil yang diharapkan: {plan.data.expected_change}</p><p>Risiko: {plan.data.risk}</p><p>ID rencana: {plan.data.plan_binding.plan_id} · versi {plan.data.plan_binding.version}</p><Missing>waktu dibuat, pelaksana, dan progres persentase tidak disediakan.</Missing><Link to="/approvals">Evidence dan keputusan terkait</Link></>}
    <p>Ini adalah rencana controlled execution eksisting, bukan daftar seluruh tugas agent.</p></section>
    <section className="panel"><h2>Riwayat eksekusi</h2><Source path="/v1/control-plane/history"/>{!authorized?<Missing>history memerlukan otorisasi.</Missing>:history.isPending?<p role="status">Memuat history…</p>:history.isError?<ErrorState error={history.error} retry={()=>void history.refetch()}/>:history.data.executions.length===0?<p>Belum ada eksekusi tercatat.</p>:<div className="table-scroll"><table><thead><tr><th>Tugas / waktu</th><th>Hasil backend</th><th>Evidence dan keputusan</th></tr></thead><tbody>{history.data.executions.map((e,i)=><tr key={i}><td>{e.change_id}<br/>{e.timestamp}</td><td>{e.result}<p>{e.reason??'Alasan tambahan belum tersedia'}</p><p>{e.files_changed.join(', ')}</p></td><td><code>{e.package_id??'Paket belum tersedia'}<br/>{e.decision_id??'Keputusan belum tersedia'}</code><p><Link to="/approvals">Telusuri keputusan</Link> · <Link to="/blockers">Blocker paket saat ini</Link></p></td></tr>)}</tbody></table></div>}</section></>;
}
function SnapshotBlockers(){
  const snapshot=useQuery({queryKey:['control-plane','snapshot'],queryFn:({signal})=>fetchSnapshot(signal),retry:false});
  const health=snapshot.data&&!isAttestation(snapshot.data.state)?snapshot.data.state:undefined;
  return <section className="panel"><h2>Temuan snapshot sistem</h2><Source path="/v1/control-plane/snapshot"/>{snapshot.isPending?<p role="status">Membaca snapshot…</p>:snapshot.isError?<ErrorState error={snapshot.error} retry={()=>void snapshot.refetch()}/>:health?<><p>Cakupan snapshot: {health.timestamp}; status runtime {health.runtime.current_status}. Temuan ini bukan inventaris error aktif global.</p><p>{health.blockers.length} pemeriksaan sistem memerlukan peninjauan.</p>{health.blockers.length>0&&<p>Ada prasyarat yang belum terpenuhi. Tinjau alasan pemeriksaan sebelum memberi persetujuan.</p>}<details><summary>Detail teknis kondisi sistem</summary><h3>Alasan pemeriksaan</h3>{health.blockers.length?<ul>{health.blockers.map((b,i)=><li key={i}>{b}</li>)}</ul>:<p>Tidak ada blocker pada snapshot ini.</p>}<h3>Peringatan dari sumber</h3>{health.warnings.map((w,i)=><p key={i}>{w}</p>)}</details><p>Penyebab belum diketahui kecuali dibuktikan pada evidence sumber.</p><Link to="/technical">Telusuri evidence teknis</Link></>:<Missing>proyeksi ATTESTATION tidak menyediakan daftar blocker NORMAL.</Missing>}</section>;
}
export function BlockersPage(){
  const q=useQuery({queryKey:['operator','package'],queryFn:fetchEvidencePackage,retry:false});
  return <><header><h1>Masalah &amp; Blocker</h1><button disabled={q.isFetching} onClick={()=>void q.refetch()}>Muat ulang</button></header><SnapshotBlockers/><section className="panel"><Source path="/v1/control-plane/evidence-package"/><p>Cakupan: blocker paket penerimaan. Kelengkapan inventaris error runtime global belum tersedia.</p>{q.isPending?<p role="status">Membaca blocker…</p>:q.isError?<ErrorState error={q.error} retry={()=>void q.refetch()}/>:<><p>Paket: <code>{q.data.package_id}</code> · {q.data.generated_at}</p>{q.data.blockers.length===0?<p>Tidak ada blocker dalam paket ini.</p>:q.data.blockers.map((b,i)=><article className="operator-blocker" id={`blocker-${i}`} key={`${b.id}-${i}`}><h2>Pemeriksaan yang perlu ditinjau</h2><p>{plainReason(b.reason)}</p><p>Status: tercatat dalam paket saat dibaca. Dampak: periksa gate penerimaan dan kriteria terkait.</p><p>Penyebab belum diketahui; alasan backend di atas bukan diagnosis akar masalah.</p><Missing>prioritas, hubungan tugas, riwayat penyelesaian, dan tindakan perbaikan terverifikasi belum disediakan.</Missing><DetailDrawer label={`Detail teknis masalah ${i+1}`}><p>Kode pemeriksaan: {b.id}</p><p>Dampak: penerimaan paket menunggu prasyarat yang belum terpenuhi.</p><p>Asal: /v1/control-plane/evidence-package ? {q.data.generated_at}</p><p>Lingkup: {q.data.read_scope} ? paket {q.data.package_id}</p><p>Task/request ID: belum tersedia pada kontrak blocker.</p><h3>Kriteria paket untuk ditinjau</h3><p>Hubungan spesifik dengan blocker belum tersedia; berikut kriteria paket yang perlu diperiksa.</p>{q.data.criteria.filter(c=>c.id===b.id||c.status!=='PASS').map(c=><p key={c.id}>{c.id} · {c.summary} · {c.status}<br/>{c.evidence.join(', ')||'Referensi belum tersedia'}</p>)}<h3>Evidence terkait kriteria</h3>{q.data.evidence.filter(e=>q.data.criteria.filter(c=>c.id===b.id||c.status!=='PASS').some(c=>c.evidence.includes(e.id))).map(e=><article key={e.id}><strong>{e.id} ? {e.validation_status}</strong><p>{e.path}</p><p>Asal: {e.classification} ? hasil: {e.reason??e.validation_status}</p><p>SHA-256: {e.sha256??'Belum tersedia'}</p></article>)}<p>Langkah: tinjau kriteria, buka referensi evidence, lalu periksa prasyarat di Human Control. Hubungan spesifik yang belum disediakan tidak disimpulkan.</p><Link to="/approvals">Periksa paket evidence lengkap</Link></DetailDrawer></article>)}</>}</section></>;
}
export {WorkspacePage} from './workspace';
export function WorkspaceTasks(){
  const [search,setSearch]=useState('');
  const {token}=useAdminAuth();const authKey=useMemo(()=>crypto.randomUUID(),[token]);
  const q=useQuery({queryKey:['operations-summary',authKey],queryFn:()=>fetchOperationsSummary(token),enabled:!!token.trim(),retry:false,gcTime:0,refetchInterval:30000});
  return <section className="panel"><h2>Status tugas V1</h2><Source path="/v1/control-plane/operations-summary"/>
    <p>Cakupan: rencana eksekusi terkontrol dan audit tersimpan; percakapan Chat tidak dianggap sebagai eksekusi tugas.</p>
    {!token.trim()?<p>Masukkan token operator di Pengaturan &amp; Teknis untuk membaca status tugas.</p>:q.isPending?<p role="status">Membaca tugas...</p>:q.isError?<ErrorState error={q.error} retry={()=>void q.refetch()}/>:<>
      <p>Diperiksa: {q.data.checked_at}</p>{q.data.reason&&<p>{q.data.reason}</p>}
      <label className="task-search">Cari tugas yang dimuat<input type="search" value={search} onChange={e=>setSearch(e.target.value)} placeholder="ID, tujuan, atau status tugas"/></label>{q.data.tasks.filter(task=>`${task.id} ${task.objective} ${task.status}`.toLocaleLowerCase().includes(search.toLocaleLowerCase())).length?<ul>{q.data.tasks.filter(task=>`${task.id} ${task.objective} ${task.status}`.toLocaleLowerCase().includes(search.toLocaleLowerCase())).map((task,i)=><li key={`${task.id}-${i}`}><strong>{task.id}</strong>: {task.objective} — <span>{task.status}</span><p>{task.updated_at} · {task.source}</p></li>)}</ul>:<p>Tidak ada tugas yang cocok dalam cakupan yang dibaca.</p>}
      <button disabled={q.isFetching} onClick={()=>void q.refetch()}>Perbarui status tugas</button></>}
    <Link to="/approvals">Tinjau izin dan hasil eksekusi</Link></section>;
}
export function CostsPage(){
  const q=useQuery({queryKey:['operator','model'],queryFn:fetchModelStatus,retry:false});
  const {token}=useAdminAuth();
  const authKey=useMemo(()=>crypto.randomUUID(),[token]);
  const ledger=useQuery({queryKey:['operator','costs',authKey],queryFn:()=>fetchCostSummary(token),enabled:!!token.trim(),retry:false,gcTime:0});
  return <><header><h1>Biaya &amp; Model</h1><button disabled={q.isFetching||ledger.isFetching} onClick={()=>{void q.refetch();if(token.trim())void ledger.refetch();}}>Muat ulang</button></header>
    <section className="panel"><h2>Provider dan model runtime</h2><Source path="/v1/control-plane/model-status"/>{q.isPending?<p role="status">Membaca status model…</p>:q.isError?<ErrorState error={q.error} retry={()=>void q.refetch()}/>:<><p>Provider: {q.data.provider} · Model: {q.data.model}</p><p>Ketersediaan: {q.data.availability} · Status: {q.data.status}</p><p>Cakupan: {q.data.consistency_scope} · proses {q.data.process_id}</p></>}</section>
    <section className="panel"><h2>Cost Ledger</h2><Source path="/v1/control-plane/cost-summary"/><p>Sisa anggaran ledger bukan saldo OpenRouter. Membaca ringkasan tidak memanggil provider berbayar.</p>
      {!token.trim()?<p>Masukkan token operator di Pengaturan &amp; Teknis untuk membaca ledger.</p>:ledger.isPending?<p role="status">Membaca biaya…</p>:ledger.isError?<ErrorState error={ledger.error} retry={()=>void ledger.refetch()}/>:ledger.data.status==='UNAVAILABLE'?<p>{ledger.data.reason}</p>:<>
      <p>Periode: seluruh umur ledger · {ledger.data.period?.start??'belum ada transaksi'} — {ledger.data.period?.end??'belum ada transaksi'}</p>
      <dl>{[['Biaya aktual',ledger.data.actual_usd],['Reservasi termasuk hasil belum diketahui',ledger.data.reserved_usd],['Batas per permintaan',ledger.data.per_request_cap_usd],['Anggaran',ledger.data.budget_usd],['Sisa anggaran',ledger.data.remaining_budget_usd]].map(([label,value])=><div key={label}><dt>{label}</dt><dd>{value===undefined?'Belum tersedia':`USD ${value}`}</dd></div>)}</dl>
      <p>{ledger.data.reason}</p><p>Diperiksa: {ledger.data.checked_at}</p><h3>Riwayat ledger (100 terbaru)</h3>{ledger.data.history?.length?<ul>{ledger.data.history.map(row=><li key={row.request_id}>{row.created_at} · {row.request_id} · {row.status} · reservasi {row.reserved_cents} sen · aktual {row.actual_cents===null?'belum diketahui':`${row.actual_cents} sen`}</li>)}</ul>:<p>Belum ada transaksi.</p>}</>}
      <dl>{['Token input / output','Estimasi biaya','Model/provider per transaksi','Saldo provider','Penolakan kebijakan biaya'].map(label=><div key={label}><dt>{label}</dt><dd>Belum tersedia melalui API</dd></div>)}</dl>
    </section></>;
}
export function TechnicalPage(){return <><header><h1>Detail Teknis R1–R21</h1></header><section className="panel"><p>Identitas tahapan dan status di bawah mengikuti modul bukti eksisting. Bukti historis tidak membuktikan runtime aktif.</p><nav aria-label="Halaman teknis lama">{[['/system','System'],['/evidence','Evidence'],['/test','Test'],['/verification','Verification'],['/roadmap','Roadmap'],['/architecture','Architecture'],['/engineering','Engineering'],['/runtime','Runtime'],['/engineering-overview','Engineering overview'],['/console','Console lama'],['/ui','Chat V1 lama']].map(([to,label])=><Link key={to} to={to as '/system'}>{label}</Link>)}</nav></section><EngineeringConsole/></>}



