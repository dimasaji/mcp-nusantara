import {useMemo,useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {Link} from '@tanstack/react-router';
import {OperatorConsole} from './assistant';
import {useAdminAuth} from './auth';
import {fetchKnowledgePipelineStatus,fetchRuntimeHealth} from './api';

const settingsSections=[
  {to:'/settings/models',label:'Model & koneksi',description:'Pilih model dan periksa koneksi layanan.'},
  {to:'/knowledge',label:'Dokumen',description:'Kelola dokumen dan pemrosesan Knowledge.'},
  {to:'/dashboard',label:'Control Plane',description:'Aktivitas, masalah, persetujuan, dan biaya.'},
  {to:'/technical',label:'Teknis',description:'Bukti, konfigurasi, dan detail sistem.'},
] as const;
const operationPages=[['/dashboard','Ringkasan'],['/tasks','Aktivitas'],['/blockers','Masalah'],['/approvals','Persetujuan'],['/costs','Biaya'],['/settings/workspace','Workspace lanjutan']] as const;

export function SettingsNavigation({pathname}:{pathname:string}){
  const [technicalOpen,setTechnicalOpen]=useState(false);
  const operations=operationPages.some(([to])=>to===pathname)||['/review','/decision','/review-execute'].includes(pathname);
  const section=pathname==='/settings'?'':operations?'Control Plane':pathname==='/settings/models'||pathname==='/console'?'Model & koneksi':pathname==='/knowledge'?'Dokumen':'Teknis';
  return <div className="settings-navigation">
    <p className="settings-breadcrumb"><Link to="/settings">Pengaturan</Link>{section&&<> / {section}</>}</p>
    {pathname!=='/settings'&&<nav aria-label="Bagian pengaturan">{settingsSections.filter(s=>s.to!=='/technical').map(({to,label})=><Link key={to} to={to} className={section===label?'active':undefined} aria-current={section===label?'page':undefined}>{label}</Link>)}</nav>}
    {operations&&<nav aria-label="Control Plane">{operationPages.map(([to,label])=><Link key={to} to={to} activeProps={{className:'active'}}>{label}</Link>)}</nav>}
    <button type="button" aria-expanded={technicalOpen} onClick={()=>setTechnicalOpen(value=>!value)}>Detail teknis</button>{technicalOpen&&<nav aria-label="Navigasi teknis"><Link to="/technical">Teknis</Link><Link to="/system">Pemeriksaan sistem</Link><Link to="/evidence">Bukti pengujian</Link></nav>}
  </div>;
}

export function SettingsPage(){
  return <><header><div><h1>Pengaturan</h1><p>Kelola model, dokumen, dan sistem di satu tempat.</p></div></header>
    <nav className="settings-grid" aria-label="Pengaturan NUSANTARA">{settingsSections.filter(s=>s.to!=='/technical').map(({to,label,description})=><Link key={to} to={to}><strong>{label}</strong><span>{description}</span><span aria-hidden="true">Buka →</span></Link>)}</nav>
    <details className="panel"><summary>Detail teknis</summary><p>Bukti pengujian dan rincian engineering tersedia untuk penelusuran.</p><Link to="/technical">Buka detail sistem</Link></details>
  </>;
}

export function RuntimeSettingsPage(){
  const {token}=useAdminAuth();const scope=useMemo(()=>crypto.randomUUID(),[token]);
  const health=useQuery({queryKey:['runtime-health'],queryFn:fetchRuntimeHealth,retry:false,refetchInterval:30000});
  const lastHealthCheckAt=Math.max(health.dataUpdatedAt,health.errorUpdatedAt);
  const lastHealthCheckDate=lastHealthCheckAt>0?new Date(lastHealthCheckAt):null;
  const lastHealthCheckLabel=lastHealthCheckDate?`${lastHealthCheckDate.toLocaleString('id-ID',{dateStyle:'medium',timeStyle:'medium'})}.${String(lastHealthCheckDate.getMilliseconds()).padStart(3,'0')}`:null;
  const knowledge=useQuery({queryKey:['settings-knowledge',scope],queryFn:()=>fetchKnowledgePipelineStatus(token),enabled:!!token.trim(),retry:false,gcTime:0,refetchInterval:30000});
  return <><OperatorConsole title="Model & koneksi"/>
    <section className="panel"><h2>Health Backend aktual</h2><p>Sumber: /health</p>
      {health.isFetching&&<p role="status" aria-live="polite">Memeriksa GET /health pada Backend…</p>}
      {health.isError?<p role="alert">{health.error.message}</p>:health.data&&<><p>GET /health - HTTP {health.data.httpStatus}</p><p>{health.data.service??'Backend'}: {health.data.status} - versi {health.data.version}</p></>}
      <p>Pemeriksaan terakhir: {lastHealthCheckLabel??'Belum diperiksa'}</p>
      <p>GET /health hanya memeriksa kesehatan Backend; hasilnya tidak membuktikan inferensi model berhasil.</p>
      <button disabled={health.isFetching} onClick={()=>void health.refetch()}>{health.isFetching?'Memeriksa…':'Periksa health'}</button></section>
    <section className="panel"><h2>Knowledge aktual</h2><p>Sumber: /v1/knowledge/pipeline/status</p>
      {!token.trim()?<p>Masukkan token operator untuk membaca Knowledge.</p>:knowledge.isPending?<p role="status">Membaca Knowledge...</p>:knowledge.isError?<p role="alert">{knowledge.error.message}</p>:<>
      <p>Dokumen terindeks: {knowledge.data.documents_indexed}</p><p>Dokumen pipeline siap: {knowledge.data.pipeline_ready_documents}</p>
      <p>Pemantauan folder: {knowledge.data.watch.enabled?'aktif':'nonaktif'}</p><p>Diperiksa: {knowledge.data.checked_at}</p>
      <button disabled={knowledge.isFetching} onClick={()=>void knowledge.refetch()}>Perbarui Knowledge</button></>}
      <p><Link to="/knowledge">Kelola dokumen dan History Knowledge</Link></p></section>
    <section className="panel"><h2>Biaya &amp; routing model</h2><p>Model aktif dan pemilihan provider memakai kendali runtime V1 di atas. Biaya hanya ditampilkan jika tersedia dari ledger backend.</p><Link to="/costs">Buka biaya aktual dan riwayat ledger</Link></section>
    <section className="panel"><h2>Maintenance &amp; Recovery</h2><p>Periksa health backend dan koneksi model sebelum melakukan pemulihan. Jika API gagal, periksa status layanan lokal melalui skrip existing <code>scripts/Status-NusantaraV1.ps1</code>.</p><p>Backup, update, dan restore belum tersedia melalui API Control Plane. Penjadwalan pemulihan dan kesiapan VPS belum diverifikasi.</p></section>
    <section className="panel"><h2>Evidence teknis dan governance</h2><Link to="/technical">Buka evidence teknis existing</Link><p><Link to="/approvals">Human Control</Link></p></section></>;
}

