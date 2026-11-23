import {useMemo, useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {useAdminAuth} from './auth';

type Connection = {
  status: 'NOT_CHECKED'|'CONNECTED'|'UNAVAILABLE'|'BUSY';
  reason: string; checked_at?: string|null;
  agent_name?: string; agent_version?: string; protocol_version?: number;
  openrouter_auth_advertised?: boolean;
  task_execution_enabled: false;
};
const endpoint='/v1/control-plane/hermes/connection';
export function hermesHttpError(status:number,detail?:unknown){
  const code=typeof detail==='string'?detail:'';
  if(status===403&&code==='BROWSER_BOUNDARY_REJECTED')return 'Permintaan diblokir batas browser lokal. Buka Control Plane dari alamat lokal yang diizinkan, lalu coba lagi.';
  if(status===401||status===403)return 'Akses operator ditolak. Periksa token operator di Pengaturan Sistem.';
  if(status===404)return 'Endpoint koneksi Hermes belum dimuat. Periksa backend dan proxy.';
  if(status===503&&code==='HERMES_NORMAL_PROFILE_REQUIRED')return 'Pemeriksaan ACP hanya tersedia pada backend V1 NORMAL yang dapat ditulis.';
  return `Pemeriksaan koneksi gagal (${status}).`;
}
export function hermesReason(reason:string){
  if(reason==='HERMES_INSTALL_STATE_NOT_WRITABLE')return 'Proses backend tidak dapat menulis status instalasi Hermes. Periksa pemilik dan izin instalasi Hermes.';
  if(reason==='HERMES_DEPENDENCY_UNAVAILABLE')return 'Executable ditemukan, tetapi dependensi Hermes ACP belum tersedia untuk proses backend.';
  return reason;
}
async function readConnection(token:string, method:'GET'|'POST', signal?:AbortSignal):Promise<Connection>{
  const response=await fetch(endpoint,{method,signal,credentials:'omit',cache:'no-store',redirect:'error',
    headers:{'X-Admin-Token':token,...(method==='POST'?{'Content-Type':'application/json'}:{})},
    ...(method==='POST'?{body:'{}'}:{})});
  if(!response.ok){
    let detail:unknown;
    try{detail=(await response.json() as {detail?:unknown}).detail;}catch{}
    throw new Error(hermesHttpError(response.status,detail));
  }
  const result=await response.json() as Connection;
  if(!['NOT_CHECKED','CONNECTED','UNAVAILABLE','BUSY'].includes(result.status)||
      typeof result.reason!=='string'||result.task_execution_enabled!==false)
    throw new Error('Respons koneksi Hermes tidak sesuai kontrak.');
  return result;
}
export function HermesConnectionPanel(){
  const {token}=useAdminAuth();
  const authKey=useMemo(()=>crypto.randomUUID(),[token]);
  const [checking,setChecking]=useState(false);
  const [message,setMessage]=useState('');
  const q=useQuery({queryKey:['hermes-acp-connection',authKey],enabled:!!token.trim(),retry:false,gcTime:0,
    queryFn:({signal})=>readConnection(token,'GET',signal)});
  async function check(){
    if(checking)return;
    setChecking(true);setMessage('');
    const controller=new AbortController();
    const timer=setTimeout(()=>controller.abort(),45000);
    try{
      await readConnection(token,'POST',controller.signal);
      await q.refetch();
    }catch(error){setMessage(error instanceof Error?error.message:'Pemeriksaan gagal.');}
    finally{clearTimeout(timer);setChecking(false);}
  }
  const labels={NOT_CHECKED:'Belum diperiksa',CONNECTED:'ACP terhubung',UNAVAILABLE:'Belum terhubung',BUSY:'Sedang diperiksa'};
  return <section className="panel"><h2>Koneksi Hermes</h2>
    <p>Pemeriksaan handshake dari backend Nusantara. Tidak menjalankan tugas atau mengirim prompt model.</p>
    {!token.trim()?<p>Masukkan token operator di Pengaturan Sistem untuk memeriksa koneksi.</p>:
      q.isPending?<p role="status">Membaca status koneksi…</p>:
      q.isError?<p role="alert">{q.error.message}</p>:<>
        <p role="status"><strong>{labels[q.data.status]}</strong> · {hermesReason(q.data.reason)}</p>
        {q.data.agent_name&&<p>Agent: {q.data.agent_name} · versi {q.data.agent_version} · ACP {q.data.protocol_version}</p>}
        {q.data.checked_at&&<p>Diperiksa: {new Date(q.data.checked_at).toLocaleString('id-ID')}</p>}
        {q.data.openrouter_auth_advertised&&<p>Server menawarkan autentikasi OpenRouter. Ini belum membuktikan request model atau integrasi biaya.</p>}
      </>}
    <button disabled={!token.trim()||checking} onClick={()=>void check()}>{checking?'Memeriksa ACP…':'Periksa koneksi Hermes'}</button>
    {message&&<p role="alert">{message}</p>}
    <p>Pengiriman tugas belum diaktifkan. Izin tools, batas biaya, dan pencatatan tugas ke History belum diintegrasikan.</p>
  </section>;
}
