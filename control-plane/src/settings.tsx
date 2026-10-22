import {useMemo} from 'react';
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
  const operations=operationPages.some(([to])=>to===pathname)||['/review','/decision','/review-execute'].includes(pathname);
  const section=pathname==='/settings'?'':operations?'Control Plane':pathname==='/settings/models'||pathname==='/console'?'Model & koneksi':pathname==='/knowledge'?'Dokumen':'Teknis';
  return <div className="settings-navigation">
    <p className="settings-breadcrumb"><Link to="/settings">Pengaturan</Link>{section&&<> / {section}</>}</p>
    {pathname!=='/settings'&&<nav aria-label="Bagian pengaturan">{settingsSections.map(({to,label})=><Link key={to} to={to} className={section===label?'active':undefined} aria-current={section===label?'page':undefined}>{label}</Link>)}</nav>}
    {operations&&<nav aria-label="Control Plane">{operationPages.map(([to,label])=><Link key={to} to={to} activeProps={{className:'active'}}>{label}</Link>)}</nav>}
  </div>;
}

export function SettingsPage(){
  return <><header><div><h1>Pengaturan</h1><p>Kelola model, dokumen, dan sistem di satu tempat.</p></div></header>
    <nav className="settings-grid" aria-label="Pengaturan NUSANTARA">{settingsSections.map(({to,label,description})=><Link key={to} to={to}><strong>{label}</strong><span>{description}</span><span aria-hidden="true">Buka →</span></Link>)}</nav>
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
    <section className="panel"><h2>Evidence teknis dan governance</h2><Link to="/technical">Buka evidence teknis existing</Link><p><Link to="/approvals">Human Control</Link></p></section></>;
}
