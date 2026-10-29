import {useMemo} from 'react';
import {useQuery} from '@tanstack/react-query';
import {fetchRuntimeReadiness} from './api';

const labels:Record<string,string>={api:'Backend',provider:'Koneksi Ollama',model:'Model terpilih',storage:'Penyimpanan',inference:'Inferensi yang teramati',document:'Dokumen terpilih'};
const states:Record<string,string>={AVAILABLE:'Tersedia',CONNECTED:'Terhubung',MISSING:'Model tidak ditemukan',UNAVAILABLE:'Belum tersedia',NOT_CHECKED:'Belum diperiksa',NOT_VERIFIED:'Belum terbukti',READABLE:'Dapat dibaca',OBSERVED:'Terbukti pada request terakhir yang cocok',LOCAL_PROVIDER_REQUIRED:'Pilih Ollama untuk dokumen internal',APPROVED:'Disetujui',BLOCKED:'Perlu diperiksa'};

export function RuntimeReadinessPanel({token}:{token:string}){
  const scope=useMemo(()=>crypto.randomUUID(),[token]);
  const result=useQuery({queryKey:['runtime-readiness',scope],queryFn:()=>fetchRuntimeReadiness(token),enabled:!!token.trim(),retry:false,gcTime:0});
  return <section className="panel" aria-label="Kesiapan Chat"><h2>Kesiapan Chat</h2>
    {!token.trim()?<p>Masukkan token operator untuk memeriksa kesiapan.</p>:result.isPending?<p role="status">Memeriksa model dan penyimpanan…</p>:result.isError?<p role="alert">{result.error.message}</p>:<>
      <p>{result.data.status==='PREREQUISITES_READY'?'Prasyarat tersedia; uji Chat tetap diperlukan.':result.data.status==='CONFIGURATION_CHANGED'?'Konfigurasi berubah saat pemeriksaan. Perbarui status.':'Ada prasyarat yang belum tersedia.'}</p>
      <dl>{Object.entries(result.data.checks).map(([name,check])=><div key={name}><dt>{labels[name]??name}</dt><dd>{states[check.status]??check.status}</dd></div>)}</dl>
      <p>Model: {result.data.model} · Provider: {result.data.provider}</p>
      <p>Daftar model membuktikan ketersediaan, bukan keberhasilan inferensi. Jalankan pertanyaan di Chat untuk menguji model. Penyimpanan diperiksa untuk pembacaan.</p>
      <p>Pemeriksaan ini tidak menjalankan model atau mengesahkan kelulusan SOP.</p>
      <details><summary>Identitas runtime</summary><p>Build: {result.data.build_id}</p><p>Proses: {result.data.process_id} · Revisi konfigurasi: {result.data.configuration_revision}</p><p>Build adalah snapshot sumber saat proses dimulai.</p><p>Diperiksa: {result.data.checked_at}</p></details>
    </>}
    <button disabled={!token.trim()||result.isFetching} onClick={()=>void result.refetch()}>{result.isFetching?'Memeriksa kesiapan…':'Periksa kesiapan Chat'}</button>
  </section>;
}
