import {useMemo} from 'react';
import {useQuery} from '@tanstack/react-query';
import {Link} from '@tanstack/react-router';
import {OperatorConsole} from './assistant';
import {useAdminAuth} from './auth';
import {fetchKnowledgePipelineStatus,fetchRuntimeHealth} from './api';

export function SettingsPage(){
  const {token}=useAdminAuth();const scope=useMemo(()=>crypto.randomUUID(),[token]);
  const health=useQuery({queryKey:['runtime-health'],queryFn:fetchRuntimeHealth,retry:false,refetchInterval:30000});
  const knowledge=useQuery({queryKey:['settings-knowledge',scope],queryFn:()=>fetchKnowledgePipelineStatus(token),enabled:!!token.trim(),retry:false,gcTime:0,refetchInterval:30000});
  return <><OperatorConsole title="Pengaturan & Teknis"/>
    <section className="panel"><h2>Health Backend aktual</h2><p>Sumber: /health</p>
      {health.isPending?<p role="status">Memeriksa health Backend...</p>:health.isError?<p role="alert">{health.error.message}</p>:<><p>GET /health - HTTP {health.data.httpStatus}</p><p>{health.data.service??'Backend'}: {health.data.status} - versi {health.data.version}</p></>}
      <p>GET /health hanya memeriksa kesehatan Backend; hasilnya tidak membuktikan inferensi model berhasil.</p>
      <button disabled={health.isFetching} onClick={()=>void health.refetch()}>{health.isFetching?'Memeriksa health...':'Periksa health'}</button></section>
    <section className="panel"><h2>Knowledge aktual</h2><p>Sumber: /v1/knowledge/pipeline/status</p>
      {!token.trim()?<p>Masukkan token operator untuk membaca Knowledge.</p>:knowledge.isPending?<p role="status">Membaca Knowledge...</p>:knowledge.isError?<p role="alert">{knowledge.error.message}</p>:<>
      <p>Dokumen terindeks: {knowledge.data.documents_indexed}</p><p>Dokumen pipeline siap: {knowledge.data.pipeline_ready_documents}</p>
      <p>Pemantauan folder: {knowledge.data.watch.enabled?'aktif':'nonaktif'}</p><p>Diperiksa: {knowledge.data.checked_at}</p>
      <button disabled={knowledge.isFetching} onClick={()=>void knowledge.refetch()}>Perbarui Knowledge</button></>}
      <p><Link to="/knowledge">Kelola dokumen dan History Knowledge</Link></p></section>
    <section className="panel"><h2>Evidence teknis dan governance</h2><Link to="/technical">Buka evidence teknis existing</Link><p><Link to="/approvals">Human Control</Link></p></section></>;
}
