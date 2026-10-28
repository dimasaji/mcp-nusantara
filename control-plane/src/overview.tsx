import {useQuery} from '@tanstack/react-query';
import {useState,useMemo,useRef} from 'react';
import {Link} from '@tanstack/react-router';
import {fetchSnapshot,fetchEvidencePackage,fetchExecutionContext,fetchExecutionHistory,fetchModelStatus,
  fetchKnowledgePipelineStatus,uploadKnowledgeDocument,setKnowledgeWatch,retryKnowledgeDocument} from './api';
import {useAdminAuth} from './auth';
import {SOPReviewPanel} from './sop-review';
import './sop-workspace.css';

function explainUploadFailure(reason:string|null|undefined){
  if(!reason)return 'Periksa file, koneksi backend, dan izin operator.';
  if(reason.includes('FILE_TOO_LARGE'))return 'File melebihi batas 20 MB.';
  if(reason.includes('FORMAT_NOT_SUPPORTED'))return 'Format file ini belum didukung.';
  if(reason.includes('OCR_NOT_AVAILABLE'))return 'PDF tampaknya hasil pemindaian dan teks tidak dapat dibaca. OCR lokal belum tersedia di server.';
  if(reason.includes('EXTRACTED_TEXT_TOO_SHORT'))return 'Teks pada PDF terlalu sedikit untuk diindeks; periksa kualitas file atau OCR.';
  if(reason.includes('EXTRACTED_TEXT_QUALITY'))return 'Teks hasil ekstraksi tidak cukup terbaca untuk diindeks.';
  if(reason.includes('INDEXING_FAILED'))return 'Teks berhasil dibaca, tetapi gagal disimpan ke index Chat.';
  if(reason.includes('ORIGINAL_FILE_SAVE_FAILED'))return 'File asli tidak berhasil disimpan di server.';
  return `Pemrosesan belum berhasil: ${reason}`;
}
import {HumanStatus} from './human';
import {readiness,plainReason} from './readiness';
import {isAttestation,type SystemHealth} from './schemas';

/**
 * Overview dashboard (route /overview).
 *
 * Shows the live system condition, what needs attention, and the next step.
 * It is a status/navigation hub: it composes existing evidence and never
 * replaces the System / Evidence / Test / Review acceptance stages.
 */
export function OverviewPage(){
  const {token}=useAdminAuth();
  const snapshot=useQuery({queryKey:['control-plane','snapshot'],queryFn:({signal})=>fetchSnapshot(signal)});
  const pkg=useQuery({queryKey:['overview','package'],queryFn:fetchEvidencePackage,retry:false,refetchInterval:30000});
  const plan=useQuery({queryKey:['overview','plan',!!token.trim()],queryFn:()=>fetchExecutionContext(token),enabled:!!token.trim(),retry:false});
  const history=useQuery({queryKey:['overview','history',!!token.trim()],queryFn:()=>fetchExecutionHistory(token),enabled:!!token.trim(),retry:false});
  const model=readiness({token,
    packageState:{state:pkg.isPending?'UNKNOWN':pkg.isError?'BLOCKED':'READY',pkg:pkg.data,reason:pkg.error instanceof Error?pkg.error.message:undefined},
    planState:{state:plan.isPending?'UNKNOWN':plan.isError?'BLOCKED':'READY',context:plan.data,reason:plan.error instanceof Error?plan.error.message:undefined},
    auditState:{state:history.isPending?'UNKNOWN':history.isError?'BLOCKED':'READY',history:history.data,reason:history.error instanceof Error?history.error.message:undefined}});
  const refresh=()=>{void snapshot.refetch();void pkg.refetch();if(token.trim()){void plan.refetch();void history.refetch();}};
  const state=snapshot.data?.state;
  const health=state&&!isAttestation(state)?state as SystemHealth:undefined;
  const gates=health?health.gates.filter(g=>g.status==='PASS').length:0;

  const attention:string[]=[
    ...(health?.blockers??[]),
    ...(health?.warnings??[]).slice(0,4),
    ...(pkg.data?.blockers.map(b=>`${b.id}: ${plainReason(b.reason)}`)??[]),
    ...(health&&health.runtime.current_status!=='NOT_VERIFIED'?[`Runtime saat ini: ${health.runtime.current_status}`]:['Runtime saat ini belum terverifikasi (NOT VERIFIED).']),
    ...(health?.protected_assets.filter(a=>a.status!=='UNCHANGED').map(a=>`Aset terlindungi ${a.path}: ${a.status}`)??[]),
    ...(model.staleDecision?[`Keputusan sebelumnya berlaku untuk paket lama (${model.staleDecision.package_id}).`]:[]),
  ];

  return <>
    <header>
      <div><div className="eyebrow">OVERVIEW / KONDISI · PERHATIAN · LANGKAH BERIKUTNYA</div><h1>Overview</h1></div>
      <button onClick={refresh} disabled={snapshot.isFetching||pkg.isFetching}>{snapshot.isFetching?'Membaca kondisi…':'Muat ulang kondisi'}</button>
    </header>

    <section className="panel" aria-label="Kondisi sistem">
      <h2>Kondisi sistem</h2>
      {snapshot.isPending?<p role="status">Membaca evidence sistem…</p>
        :snapshot.isError?<section className="panel error" role="alert"><h3>Kondisi sistem tidak dapat diverifikasi</h3><p>{snapshot.error.message}</p><p>Status kesehatan sistem tidak disimpulkan dari kegagalan ini.</p></section>
        :health?<>
          <div className="diagnostics"><HumanStatus status={health.status}/><span>Fase {health.current_phase}</span><span>Gate PASS {gates}/{health.gates.length}</span><span>Runtime {health.runtime.current_status}</span><span>RAG {health.rag.status}</span></div>
          <p>Evidence dibaca {new Date(snapshot.data.fetchedAt).toLocaleTimeString()} · {snapshot.data.latencyMs} ms · build {health.runtime.build_id??'NOT VERIFIED'}</p>
        </>:<p>Proyeksi ATTESTATION aktif; status kesehatan NORMAL tidak termasuk dalam cakupan.</p>}
      <p><Link to={'/system' as '/overview'}>Buka System →</Link></p>
    </section>

    <section className="panel" aria-label="Perlu perhatian">
      <h2>Yang perlu perhatian</h2>
      {attention.length?<ul className="attention">{attention.map((item,i)=><li key={i}>△ {item}</li>)}</ul>:<p>✓ Tidak ada temuan yang perlu perhatian dari evidence saat ini.</p>}
    </section>

    <section className="panel next-action" aria-label="Langkah berikutnya">
      <h2>Langkah berikutnya</h2>
      <p>{model.next.why}</p>
      <div className="action-row">
        <Link to={model.next.to as '/overview'} className="button-link primary">{model.next.label}</Link>
        <Link to={'/verification' as '/overview'} className="button-link">Lihat Test &amp; Verification</Link>
        <Link to={'/review-execute' as '/overview'} className="button-link">Review &amp; Execute</Link>
      </div>
      <ul className="checks compact">{model.checks.map(c=><li key={c.id} data-status={c.status}>
        <span className="check-id">{c.id}</span><strong>{c.label}</strong>
        <span className={`human-status ${c.status==='READY'?'positive':c.status==='BLOCKED'?'negative':'caution'}`}>{c.status}</span>
      </li>)}</ul>
    </section>

    <section className="panel" aria-label="Enam tanggung jawab">
      <h2>Enam tanggung jawab Developer Core</h2>
      <div className="responsibility-grid">
        <Link to={'/system' as '/overview'}><strong>01 · System</strong><span>Kondisi sistem dan batasannya</span></Link>
        <Link to={'/evidence' as '/overview'}><strong>02 · Evidence</strong><span>Artefak dan status verifikasinya</span></Link>
        <Link to={'/console' as '/overview'}><strong>03 · Blocker &amp; Diagnosis</strong><span>Runtime, diagnostik dan hambatan</span></Link>
        <Link to={'/review-execute' as '/overview'}><strong>04 · Plan &amp; Execute</strong><span>Rencana, keputusan, eksekusi</span></Link>
        <Link to={'/verification' as '/overview'}><strong>05 · Test &amp; Verification</strong><span>Apa yang diuji dan cakupannya</span></Link>
        <Link to={'/review' as '/overview'}><strong>06 · Review &amp; Human Decision Gate</strong><span>Tinjauan dan keputusan manusia</span></Link>
      </div>
      <p className="checklist-help">Knowledge adalah layanan logis tersendiri, Governance berlaku lintas proses, dan History mencatat setiap proses pada halaman Review &amp; Execute.</p>
    </section>
  </>;
}

/** General knowledge operations dashboard; sample documents are fixtures only. */
export function KnowledgeOperationsPage(){
  const {token,setToken}=useAdminAuth();
  const [tokenDraft,setTokenDraft]=useState(token);
  const [reviewDocument,setReviewDocument]=useState<string|null>(null);
  const [selected,setSelected]=useState<File|null>(null);
  const fileInput=useRef<HTMLInputElement>(null);
  const [busy,setBusy]=useState(false);
  const [message,setMessage]=useState('');
  const [uploadFailed,setUploadFailed]=useState(false);
  const [showAllRuns,setShowAllRuns]=useState(false);
  const uploadInFlight=useRef(false);
  const [existingFile,setExistingFile]=useState<{authKey:string;documentId:string}|null>(null);
  const authKey=useMemo(()=>crypto.randomUUID(),[token]);
  const query=useQuery({queryKey:['knowledge-pipeline',authKey],queryFn:()=>fetchKnowledgePipelineStatus(token),enabled:!!token.trim(),retry:false,refetchInterval:busy?2000:30000,gcTime:0});
  async function retryRun(id:string){
    setBusy(true);setMessage('');
    try{const run=await retryKnowledgeDocument(id,token);setMessage(run.status==='FAILED'?explainUploadFailure(run.reason):'Dokumen telah diproses ulang.');await query.refetch();}
    catch(e){setMessage(e instanceof Error?e.message:'Pemrosesan ulang gagal.');}
    finally{setBusy(false);}
  }
  async function submit(){
    if(!selected||busy||uploadInFlight.current||!token.trim())return;
    uploadInFlight.current=true;
    setBusy(true);setMessage('');setUploadFailed(false);setExistingFile(null);
    try{
      if(selected.size<=20*1024*1024&&crypto.subtle){
        const digest=await crypto.subtle.digest('SHA-256',await selected.arrayBuffer());
        const hash=Array.from(new Uint8Array(digest),byte=>byte.toString(16).padStart(2,'0')).join('');
        const existing=query.data?.documents?.find(doc=>doc.status==='READY'&&doc.source_sha256===hash);
        if(existing){
          setExistingFile({authKey,documentId:existing.document_id});
          setMessage('File identik sudah tersedia. Gunakan dokumen tersimpan; tidak perlu unggah ulang.');
          setSelected(null);if(fileInput.current)fileInput.current.value='';return;
        }
      }
      const run=await uploadKnowledgeDocument(selected,token);const status=run.status==='READY'?'Dokumen berhasil disimpan dan diproses.':run.status==='DUPLICATE'?'File tersimpan; isinya sudah ada di index Chat.':explainUploadFailure(run.reason);setMessage(`${status}${run.status==='READY'?' Sumber belum disahkan sebagai revisi resmi.':''}`);const failed=run.status==='FAILED';setUploadFailed(failed);if(!failed){setSelected(null);if(fileInput.current)fileInput.current.value='' ;}await query.refetch();}
    catch(e){setUploadFailed(true);const message=e instanceof Error?e.message:'Terjadi kesalahan saat mengirim dokumen.';const lower=message.toLowerCase();setMessage(lower.includes('di luar cakupan')||lower.includes('out_of_scope')?'Akun operator tidak memiliki izin untuk menambahkan dokumen. Hubungi administrator.':lower.includes('403')||lower.includes('401')?'Autentikasi operator gagal. Periksa token operator lalu coba lagi.':message);}
    finally{setBusy(false);uploadInFlight.current=false;}
  }
  async function watch(enabled:boolean){
    if(busy)return;setBusy(true);setMessage('');
    try{await setKnowledgeWatch(enabled,token);await query.refetch();}
    catch(e){setMessage(e instanceof Error?e.message:'Konfigurasi pemantauan gagal.');}
    finally{setBusy(false);}
  }
  const runs=query.data?.runs??[];
  const duplicateGroups=new Map<string,typeof runs>();
  const summarizedRuns=runs.filter(run=>{
    if(run.status!=='DUPLICATE')return true;
    const key=JSON.stringify([run.source_sha256,run.document_id,run.filename,run.reason]);
    const group=duplicateGroups.get(key);
    if(group){group.push(run);return false;}
    duplicateGroups.set(key,[run]);return true;
  });
  const duplicateCounts=new Map([...duplicateGroups.values()].map(group=>[group[0].run_id,group.length]));
  const visibleRuns=showAllRuns?runs:summarizedRuns;
  const ready=query.data?.pipeline_ready_documents??runs.filter(r=>r.status==='READY').length;
  const failed=runs.filter(r=>r.status==='FAILED').length;
  const canUpload=!!token.trim()&&query.isSuccess&&!busy;
  const documents=query.data?.documents??[];
  const currentDocument=documents.find(doc=>doc.document_id===reviewDocument)??documents.find(doc=>doc.review_status)??documents[0];
  return <div className="knowledge-workspace">
    <header><div><div className="eyebrow">DOKUMEN SOP</div><h1>Pemeriksaan SOP</h1><p>Periksa sumber, coba jawaban, lalu tentukan apakah SOP dapat digunakan.</p></div><button onClick={()=>void query.refetch()} disabled={!token.trim()||query.isFetching}>Muat ulang</button></header>
    <section className="panel" aria-label="Akses upload"><details open={!query.isSuccess}><summary>Akses operator</summary>
      <p>Masukkan token operator untuk membuka dokumen tersimpan. Setelah refresh, verifikasi kembali.</p>
      <form onSubmit={e=>{e.preventDefault();setMessage('');if(tokenDraft.trim()===token)void query.refetch();else setToken(tokenDraft.trim());}}>
        <label htmlFor="knowledge-operator-token">Token operator</label>
        <input id="knowledge-operator-token" type="password" autoComplete="off" value={tokenDraft} disabled={busy} onChange={e=>setTokenDraft(e.target.value)}/>
        <button type="submit" disabled={busy||query.isFetching||!tokenDraft.trim()}>Verifikasi akses</button>
        {token&&<button type="button" disabled={busy} onClick={()=>{setToken('');setTokenDraft('');}}>Keluar</button>}
      </form>
      </details><p role="status">{!token.trim()?'Belum masuk. File dapat dipilih; upload menunggu verifikasi token.':query.isFetching?'Memeriksa akses operator…':query.isSuccess?'Akses operator terverifikasi. Anda dapat mengunggah file.':'Akses belum terverifikasi. Periksa token dan coba Verifikasi akses lagi.'}</p>

    </section>
    <ol className="sop-steps" aria-label="Alur pemeriksaan"><li><strong>1. Pilih dokumen</strong><span>Gunakan file yang sudah tersimpan</span></li><li><strong>2. Periksa dan coba</strong><span>Cocokkan isi dan jawaban dengan PDF</span></li><li><strong>3. Putuskan</strong><span>Setujui atau catat masalahnya</span></li></ol>
    {!token.trim()?<section className="panel"><h2>Mulai dengan akses operator</h2><p>Dokumen yang sudah diunggah akan muncul setelah akses terverifikasi. Tidak perlu mengunggah ulang.</p></section>:query.isPending?<p role="status">Memuat dokumen tersimpan...</p>:query.isError?<p role="alert">Dokumen belum dapat dibuka: {query.error.message}</p>:currentDocument?<>
      <section className="panel sop-current-document" aria-label="Dokumen yang diperiksa">
        <div><p className="eyebrow">DOKUMEN TERPILIH</p><h2>{currentDocument.title}</h2><p>Dokumen sudah tersimpan. Anda tidak perlu mengunggah ulang.</p><p>Status pemeriksaan: <strong>{currentDocument.review_status??'Belum diperiksa'}</strong></p></div>
        <button className="primary" onClick={()=>setReviewDocument(currentDocument.document_id)}>Periksa isi</button>
      </section>
      {reviewDocument&&<SOPReviewPanel key={`${reviewDocument}-${authKey}`} documentId={reviewDocument} token={token}/>}
      <details className="panel"><summary>Pilih dokumen lain ({documents.length})</summary><p>Pilih berdasarkan judul dan file sumbernya. Versi atau salinan tetap disimpan terpisah.</p><div className="sop-document-list">{documents.map(doc=><article key={doc.document_id}><div><h3>{doc.title}</h3><small>{doc.review_status??'Belum diperiksa'} · {new Date(doc.updated_at).toLocaleDateString('id-ID')}</small><details><summary>Identitas dokumen</summary><p>{doc.document_id}</p></details></div><button onClick={()=>setReviewDocument(doc.document_id)} disabled={doc.document_id===reviewDocument}>Pilih dokumen</button></article>)}</div></details>
    </>:<section className="panel"><h2>Belum ada dokumen</h2><p>Buka Tambahkan dokumen baru di bawah untuk memasukkan SOP pertama.</p></section>}
    <details className="panel sop-optional"><summary>Tambahkan dokumen baru</summary><p>Gunakan hanya untuk dokumen yang belum tersedia atau revisi dengan isi berbeda.</p>
    <section className="panel" aria-label="Tambahkan dokumen"><h2>Tambahkan dokumen</h2><p>Didukung: PDF, DOCX, TXT, Markdown, HTML. Setelah dikirim, file asli disimpan utuh dan dokumen diproses dengan index Chat. File sumber tidak diubah.</p>
      <label>Pilih dokumen <input ref={fileInput} type="file" accept=".pdf,.docx,.txt,.md,.html,.htm" disabled={busy} onChange={e=>{setSelected(e.target.files?.[0]??null);setExistingFile(null);setMessage('');setUploadFailed(false);}}/></label>
      {selected&&<p>File dipilih: <strong>{selected.name}</strong> · {(selected.size/1024).toLocaleString('id-ID',{maximumFractionDigits:1})} KB</p>}
      <button className="primary" aria-describedby="knowledge-upload-help" disabled={!canUpload||!selected} onClick={()=>void submit()}>{busy?'Memproses...':'Proses dan validasi'}</button>
      <p id="knowledge-upload-help">{!token.trim()?'Verifikasi akses operator di halaman ini untuk mengaktifkan upload.':!query.isSuccess?'Upload menunggu akses backend terverifikasi.':!selected?'Pilih dokumen dari perangkat Anda.':'Siap diunggah melalui browser dan diproses otomatis.'}</p>
      {message&&<p role={uploadFailed?'alert':'status'}>{message}</p>}{existingFile?.authKey===authKey&&<Link to="/" onClick={()=>{sessionStorage.setItem('nusantara-chat-document-pending',existingFile.documentId);sessionStorage.removeItem('nusantara-chat-sop-version-pending');}}>Tanyakan dokumen tersimpan</Link>}
      {uploadFailed&&<button disabled={busy||!selected||!token.trim()} onClick={()=>void submit()}>Coba Lagi</button>}
        {ready>0&&query.isSuccess&&<Link to="/">Buka Chat</Link>}
    </section>
    </details>
    <details className="panel sop-optional"><summary>Riwayat proses sebelumnya</summary><p>Ini catatan proses lama, bukan daftar pekerjaan yang harus diulang.</p>
    <section className="panel" aria-label="History knowledge"><h2>History proses</h2>{runs.length>summarizedRuns.length&&<><p>Pengulangan file identik diringkas. Catatan asli tetap tersimpan; kegagalan tetap ditampilkan.</p><button onClick={()=>setShowAllRuns(value=>!value)}>{showAllRuns?'Ringkas pengulangan':`Tampilkan semua catatan (${runs.length})`}</button></>}{!token.trim()?<p>History memerlukan autentikasi operator, tanpa keputusan PASS.</p>:query.isPending?<p role="status">Memuat History...</p>:query.isError?<p role="alert">History gagal dimuat: {query.error.message}</p>:runs.length===0?<p>Belum ada dokumen yang diproses.</p>:<div className="table-scroll"><table><thead><tr><th>Waktu</th><th>Dokumen</th><th>Hasil</th><th>Alasan/status sumber</th><th>Detail</th></tr></thead><tbody>{visibleRuns.map(run=><tr key={run.run_id}><td>{new Date(run.created_at).toLocaleString('id-ID')}</td><td>{run.filename}</td><td>{run.status}{!showAllRuns&&(duplicateCounts.get(run.run_id)??0)>1&&<small> · {duplicateCounts.get(run.run_id)} percobaan identik</small>}</td><td>{run.status==='FAILED'?explainUploadFailure(run.reason):run.reason??'Berhasil dibaca dan disimpan ke Chat; otoritas/revisi belum disahkan.'}</td><td>{run.status==='FAILED'&&run.source_path&&<button disabled={busy} onClick={()=>void retryRun(run.run_id)}>Coba Lagi</button>}<details><summary>Detail</summary><p>ID run: <code>{run.run_id}</code></p><p>SHA-256: <code>{run.source_sha256}</code></p>{run.source_path&&<p>File tersimpan: <code>{run.source_path}</code></p>}{run.document_id&&<p>Dokumen index: <code>{run.document_id}</code></p>}</details></td></tr>)}</tbody></table></div>}</section>
    </details>
    <details className="panel sop-optional"><summary>Pengaturan dan informasi teknis</summary>
    <section className="panel" aria-label="Ringkasan pipeline"><h2>Ringkasan proses</h2>
      {!token.trim()?<p>Token operator diperlukan untuk operasi dan History knowledge. Chat dan status umum tetap dapat dibaca tanpa keputusan.</p>
      :query.isPending?<p role="status">Memuat status pipeline...</p>:query.isError?<p role="alert">Status tidak tersedia: {query.error.message}</p>:<>
        <div className="diagnostics"><span>{ready} dokumen lulus pipeline</span><span>{query.data.documents_indexed} dokumen ada di index Chat</span><span>{failed} dokumen gagal</span><span>Diperiksa {new Date(query.data.checked_at).toLocaleString('id-ID')}</span></div>
        <p>Sumber data: store knowledge Chat yang sama.</p>
        <p>Siap di index berarti ekstraksi, deduplikasi, dan indexing teknis berhasil. Ini tidak mengesahkan otoritas atau menetapkan dokumen sebagai revisi resmi yang berlaku.</p>
      </>}
    </section>
    <section className="panel" aria-label="Pemantauan folder"><h2>Pemantauan folder</h2>{query.data?<><p>Folder inbox: <code>{query.data.watch.folder}</code></p><p>Status: {query.data.watch.enabled?'AKTIF':'NONAKTIF'}. File baru diproses otomatis saat backend berjalan.</p><button disabled={!token.trim()||busy} onClick={()=>void watch(!query.data.watch.enabled)}>{query.data.watch.enabled?'Hentikan pemantauan':'Aktifkan pemantauan'}</button></>:<p>Folder tersedia setelah status pipeline berhasil dibaca.</p>}</section>
    </details>
  </div>;
}
