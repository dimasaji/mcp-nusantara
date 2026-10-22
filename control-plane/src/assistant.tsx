import {memo,useEffect,useState,useRef} from 'react';
import {Link} from '@tanstack/react-router';
import {ChatSendError,fetchChatHistory,fetchModelStatus,fetchAvailableModels,selectOperatorModel,sendUserChat,fetchKnowledgePipelineStatus,uploadKnowledgeDocument,type ModelStatus,type PublicChat} from './api';
import {useAdminAuth} from './auth';

function InlineMarkdown({text}:{text:string}){
  return <>{text.split(/(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)/g).map((part,i)=>part.startsWith('`')?<code key={i}>{part.slice(1,-1)}</code>:part.startsWith('**')?<strong key={i}>{part.slice(2,-2)}</strong>:part.startsWith('*')?<em key={i}>{part.slice(1,-1)}</em>:part)}</>;
}
const MarkdownAnswer=memo(function MarkdownAnswer({text}:{text:string}){
  const lines=text.replace(/\r/g,'').split('\n');const blocks:React.ReactNode[]=[];let paragraph:string[]=[],code:string[]=[];let inCode=false,language='';
  const flush=()=>{if(paragraph.length){blocks.push(<p key={`p-${blocks.length}`}><InlineMarkdown text={paragraph.join('\n')}/></p>);paragraph=[];}};
  for(const line of lines){const fence=line.match(/^```\s*([\w+-]*)/);if(fence){flush();if(inCode){blocks.push(<pre key={`c-${blocks.length}`}><code className={language?`language-${language}`:undefined}>{code.join('\n')}</code></pre>);code=[];inCode=false;language='';}else{inCode=true;language=fence[1];}continue;}if(inCode){code.push(line);continue;}if(!line.trim()){flush();continue;}const heading=line.match(/^(#{1,3})\s+(.+)$/);if(heading){flush();const Tag=`h${heading[1].length}` as 'h1'|'h2'|'h3';blocks.push(<Tag key={`h-${blocks.length}`}><InlineMarkdown text={heading[2]}/></Tag>);continue;}const item=line.match(/^\s*[-*+]\s+(.+)$/);if(item){flush();blocks.push(<ul key={`ul-${blocks.length}`}><li><InlineMarkdown text={item[1]}/></li></ul>);continue;}const quote=line.match(/^>\s?(.*)$/);if(quote){flush();blocks.push(<blockquote key={`q-${blocks.length}`}><InlineMarkdown text={quote[1]}/></blockquote>);continue;}paragraph.push(line.trim());}
  flush();if(code.length)blocks.push(<pre key={`c-${blocks.length}`}><code className={language?`language-${language}`:undefined}>{code.join('\n')}</code></pre>);return <div className="markdown-answer">{blocks}</div>;
});
function PaperclipIcon(){return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m8.5 12.5 7-7a4 4 0 0 1 5.7 5.7l-9.5 9.5a6 6 0 0 1-8.5-8.5l9.2-9.2"/></svg>}
function SendIcon(){return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 19V5m-7 7 7-7 7 7"/></svg>}

export function UserChat({embedded=false,token=''}:{embedded?:boolean;token?:string;setToken?:(value:string)=>void}={}){
  const [uploadPanelOpen,setUploadPanelOpen]=useState(false);
  const previousToken=useRef(token);const credentialGeneration=useRef(0);
  if(previousToken.current!==token){previousToken.current=token;credentialGeneration.current++;}
  return <ChatSession key={credentialGeneration.current} embedded={embedded} token={token} uploadPanelOpen={uploadPanelOpen} setUploadPanelOpen={setUploadPanelOpen}/>;
}
function ChatSession({embedded,token,uploadPanelOpen,setUploadPanelOpen}:{embedded:boolean;token:string;uploadPanelOpen:boolean;setUploadPanelOpen:(value:boolean)=>void}){
  const storagePrefix=token?'nusantara-chat-p0-operator':'nusantara-chat-p0-public';
  const sessionListStorage=token?sessionStorage:localStorage;
  const Title=embedded?'h2':'h1';
  const [sessions,setSessions]=useState<string[]>(()=>{try{const value=JSON.parse(sessionListStorage.getItem(storagePrefix+'-sessions')??'[]');return Array.isArray(value)?value.filter((id:unknown)=>typeof id==='string'&&/^web-[a-f0-9-]{36}$/.test(id)).slice(-20):[];}catch{return [];}});
  const [session,setSession]=useState(()=>{const saved=sessionStorage.getItem(storagePrefix+'-session');return saved&&/^web-[a-f0-9-]{36}$/.test(saved)?saved:sessions.at(-1)??`web-${crypto.randomUUID()}`;});
  const currentSession=useRef(session);currentSession.current=session;
  const [model,setModel]=useState<ModelStatus|null>(null);
  const [question,setQuestion]=useState('');
  const [messages,setMessages]=useState<{question:string;answer:PublicChat}[]>([]);
  const [pending,setPending]=useState(false);
  const [partial,setPartial]=useState('');
  const [documents,setDocuments]=useState<{document_id:string;title:string}[]>([]);
  const [selectedDocument,setSelectedDocument]=useState('');
  const activeRequest=useRef<AbortController|null>(null);
  const [error,setError]=useState('');
  const [historyError,setHistoryError]=useState('');
  const [historyFailures,setHistoryFailures]=useState<{question:string;error:string|null;timestamp:string}[]>([]);
  const [titles,setTitles]=useState<Record<string,string>>(()=>{try{return token?{}:JSON.parse(localStorage.getItem(storagePrefix+'-titles')??'{}')}catch{return {}}});
  const [uploadFile,setUploadFile]=useState<File|null>(null);const [uploadReady,setUploadReady]=useState(false);const [uploadStatus,setUploadStatus]=useState('');const [uploadError,setUploadError]=useState('');const [uploadBusy,setUploadBusy]=useState(false);
  const [sidebarOpen,setSidebarOpen]=useState(()=>typeof window==='undefined'||!window.matchMedia?.('(max-width: 760px)').matches);const conversationRef=useRef<HTMLDivElement|null>(null);
  const logicalRequest=useRef<{question:string;session:string;id:string;retryOf?:string}|null>(null);
  async function refreshHistory(active=()=>true){
    const requestedSession=session;
    try{const history=await fetchChatHistory(session,selectedDocument?token:'');if(active()&&currentSession.current===requestedSession){
      const restored=history.turns.filter(t=>t.answer!==null).map(t=>({question:t.question,answer:t.answer!}));
      if(restored[0]?.question&&!titles[session])setTitles(old=>{const next={...old,[session]:restored[0].question.trim().replace(/\s+/g,' ').slice(0,60)};if(!token)localStorage.setItem(storagePrefix+'-titles',JSON.stringify(next));return next;});
      setMessages(current=>[...restored,...current.filter(t=>!restored.some(r=>r.answer.timestamp===t.answer.timestamp&&r.question===t.question))]);
      setHistoryFailures(history.turns.filter(t=>t.status==='FAILED'&&!(t.request_id&&history.turns.some(retry=>retry.status==='SUCCEEDED'&&retry.retry_of===t.request_id))));setHistoryError('');
    }}catch{if(active()&&currentSession.current===requestedSession)setHistoryError('History server belum dapat dibaca. Percakapan yang tampil belum membuktikan riwayat tersimpan.');}
  }
  useEffect(()=>{sessionStorage.setItem(storagePrefix+'-session',session);setSessions(old=>{const next=[...old.filter(id=>id!==session),session].slice(-20);sessionListStorage.setItem(storagePrefix+'-sessions',JSON.stringify(next));return next;});let active=true;
    void refreshHistory(()=>active);
    return ()=>{active=false;};},[session,selectedDocument,token]);
  useEffect(()=>{void fetchModelStatus().then(setModel).catch(()=>setModel(null));},[]);
  useEffect(()=>{if(!token){setSelectedDocument('');return;}const pendingDocument=sessionStorage.getItem('nusantara-chat-document-pending');const selected=pendingDocument??sessionStorage.getItem(storagePrefix+'-document-'+session)??'';setSelectedDocument(selected);if(pendingDocument){sessionStorage.setItem(storagePrefix+'-document-'+session,pendingDocument);sessionStorage.removeItem('nusantara-chat-document-pending');}},[session]);
  useEffect(()=>{if(conversationRef.current)conversationRef.current.scrollTop=conversationRef.current.scrollHeight;},[messages,pending,partial]);
  useEffect(()=>()=>activeRequest.current?.abort(),[]);
  async function send(){
    if(activeRequest.current||!question.trim())return;
    if(selectedDocument&&!token.trim()){setError('Token operator diperlukan untuk chat dokumen. Verifikasi akses melalui Lampirkan dokumen.');return;}
    const controller=new AbortController();activeRequest.current=controller;
    const submitted=question.trim();setPartial('');setPending(true);setError('');
    if(!titles[session])setTitles(old=>{const next={...old,[session]:submitted.replace(/\s+/g,' ').slice(0,60)};if(!token)localStorage.setItem(storagePrefix+'-titles',JSON.stringify(next));return next;});
    if(logicalRequest.current?.question!==submitted||logicalRequest.current.session!==session){
      logicalRequest.current={question:submitted,session,id:crypto.randomUUID().replaceAll('-','')};
    }
    const request=logicalRequest.current;
    try{const answer=await sendUserChat(submitted,session,request.id,request.retryOf,model?.provider==='ollama'?270000:90000,{signal:controller.signal,onDelta:text=>setPartial(old=>old+text),documentIds:selectedDocument?[selectedDocument]:undefined,token:selectedDocument?token:undefined});setMessages(old=>[...old,{question:submitted,answer}]);setQuestion('');logicalRequest.current=null;
      void fetchModelStatus().then(setModel).catch(()=>setModel(null));
    }catch(e){
      if(e instanceof ChatSendError&&e.retrySafe){logicalRequest.current={...request,id:crypto.randomUUID().replaceAll('-',''),retryOf:request.id};}
      setError(e instanceof Error?e.message:'Pertanyaan belum berhasil dikirim.');
    }
    finally{activeRequest.current=null;setPartial('');setPending(false);void refreshHistory();}
  }
  function stop(){activeRequest.current?.abort();logicalRequest.current=null;}
  function newChat(){if(pending)return;logicalRequest.current=null;setSession(`web-${crypto.randomUUID()}`);setMessages([]);setHistoryFailures([]);setQuestion('');setError('');setSidebarOpen(false);}
  async function verifyUpload(){setUploadBusy(true);setUploadError('');setUploadStatus('');try{const pipeline=await fetchKnowledgePipelineStatus(token);setDocuments(pipeline.documents??[]);setUploadReady(true);setUploadStatus('Knowledge siap. Pilih dokumen untuk diunggah atau ditanyakan.');}catch(e){setUploadReady(false);setUploadError(e instanceof Error?e.message:'Knowledge belum dapat dibaca.');}finally{setUploadBusy(false);}}
  function chooseDocument(id:string){setSelectedDocument(id);sessionStorage.setItem(storagePrefix+'-document-'+session,id);logicalRequest.current=null;}
  async function submitUpload(){if(!uploadReady||!uploadFile||!token.trim())return;setUploadBusy(true);setUploadError('');setUploadStatus('Menyimpan, mengekstrak, dan mengindeks dokumen…');try{const result=await uploadKnowledgeDocument(uploadFile,token);if(!['READY','DUPLICATE'].includes(result.status)||!result.document_id)throw new Error(`Dokumen belum siap ditanyakan. ${result.reason??'Periksa History Knowledge.'}`);setDocuments(old=>[...old.filter(d=>d.document_id!==result.document_id),{document_id:result.document_id!,title:result.filename}]);chooseDocument(result.document_id);setUploadStatus(`Dokumen ${result.filename} siap ditanyakan dan dipilih sebagai sumber. Otoritas sumber belum disahkan.`);setUploadFile(null);}catch(e){setUploadStatus('');setUploadError(e instanceof Error?e.message:'Dokumen belum berhasil diproses.');}finally{setUploadBusy(false);}}
  const uniqueEvidence=(items:PublicChat['evidence'])=>items.filter((e,i,all)=>all.findIndex(x=>x.document_id===e.document_id)===i);
  const Composer= <form className="message-composer" onSubmit={e=>{e.preventDefault();void send();}}>    <label className="chat-document-scope">Sumber dokumen <select aria-label="Sumber dokumen" disabled={pending} value={selectedDocument} onChange={e=>chooseDocument(e.target.value)}><option value="">Semua knowledge</option>{selectedDocument&&!documents.some(d=>d.document_id===selectedDocument)&&<option value={selectedDocument}>Dokumen sesi ini — verifikasi akses untuk membaca judul</option>}{documents.map(d=><option key={d.document_id} value={d.document_id}>{d.title}</option>)}</select></label>
    {selectedDocument&&<small>Jawaban dibatasi ke dokumen pilihan dengan model lokal. Jika informasi tidak ditemukan, jawaban akan menyatakannya.</small>}
<div className="composer-box">
    <details className="chat-upload" open={uploadPanelOpen} onToggle={event=>{const open=event.currentTarget.open;setUploadPanelOpen(open);if(open&&token.trim()&&!uploadReady&&!uploadBusy)void verifyUpload();}}><summary aria-label="Lampirkan dokumen" title="Lampirkan dokumen"><PaperclipIcon/></summary><div className="composer-upload-panel"><strong>Unggah dokumen</strong>{!token.trim()?<><p>Upload memerlukan akses operator.</p><Link className="chat-upload-settings" to="/knowledge">Buka Knowledge untuk mengatur akses</Link></>:<>{uploadBusy?<p role="status">Memeriksa akses Knowledge…</p>:uploadError?<p role="alert">{uploadError}</p>:uploadStatus&&<p role="status">{uploadStatus}</p>}<input aria-label="Dokumen untuk knowledge" type="file" accept=".pdf,.docx,.txt,.md,.html,.htm" disabled={!uploadReady||uploadBusy} onChange={e=>setUploadFile(e.target.files?.[0]??null)}/><button type="button" disabled={!uploadReady||!uploadFile||uploadBusy} onClick={()=>void submitUpload()}>{uploadBusy?'Memproses…':'Upload dan proses'}</button><small>Dokumen diproses melalui Knowledge lokal dan mengikuti pemeriksaan akses yang berlaku.</small></>}</div></details>
    <textarea aria-label="Pertanyaan Anda" id={embedded?'embedded-question':'question'} value={question} onChange={e=>setQuestion(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.ctrlKey&&!e.metaKey){e.preventDefault();void send();}}} maxLength={20000} disabled={pending} required placeholder="Tanyakan sesuatu atau lampirkan dokumen…"/>
    {uploadFile&&<span className="upload-filename" title={uploadFile.name}>{uploadFile.name}</span>}<button className="composer-send" aria-label={pending?'Memproses…':'Kirim pertanyaan'} title="Kirim" disabled={pending||!question.trim()} type="submit"><SendIcon/></button>{pending&&<button type="button" onClick={stop}>Berhenti</button>}</div>
    {pending&&<div role="status" className="stream-preview"><p>{partial?'Jawaban sementara — pemeriksaan sumber belum selesai.':'Menunggu respons model…'}</p>{partial&&<p style={{whiteSpace:'pre-wrap'}}>{partial}</p>}</div>}{uploadStatus&&<p className="upload-feedback" role="status">{uploadStatus}</p>}{uploadError&&<p className="upload-feedback" role="alert">{uploadError}</p>}</form>;
  const Header= <header className="chat-header">{!embedded&&<button className="sidebar-toggle" type="button" aria-label={sidebarOpen?'Ciutkan sidebar':'Buka sidebar'} title={sidebarOpen?'Ciutkan sidebar':'Buka sidebar'} onClick={()=>setSidebarOpen(v=>!v)}><span aria-hidden="true">☰</span></button>}<Link className="chat-header-brand" to="/">NUSANTARA</Link></header>;
  const Sidebar=!embedded&&<aside className="chat-sidebar"><button className="drawer-close" type="button" aria-label="Tutup sidebar" onClick={()=>setSidebarOpen(false)}>×</button><Link className="chat-brand" to="/"><span className="mark">N</span><span className="sidebar-brand-label">NUSANTARA<small>AI WORKSPACE</small></span></Link><button className="chat-new" type="button" aria-label="Chat baru" disabled={pending} onClick={newChat}><span aria-hidden="true">＋</span><span className="sidebar-label">Chat baru</span></button><div className="chat-history"><div className="chat-history-head"><p className="nav-caption">RIWAYAT CHAT</p><button type="button" className="history-refresh" aria-label="Muat ulang History" title="Muat ulang History" disabled={pending} onClick={()=>void refreshHistory()}>↻</button></div><nav aria-label="Riwayat Chat">{[...sessions].reverse().map((id,i)=><button type="button" key={id} title={titles[id]??('Percakapan '+(sessions.length-i))} aria-current={id===session?'page':undefined} onClick={()=>{if(pending)return;logicalRequest.current=null;setSession(id);setMessages([]);setHistoryFailures([]);setError('');setSidebarOpen(false);}}><span>{titles[id]??('Percakapan '+(sessions.length-i))}</span></button>)}</nav></div><Link className="chat-control-link" aria-label="Control Plane" to="/dashboard"><span aria-hidden="true">⚙</span><span className="sidebar-label">Control Plane</span></Link></aside>;
  return <div className={(embedded?'chat-embedded':'chat-workspace')+(!sidebarOpen?' sidebar-collapsed':'')+(sidebarOpen?' sidebar-open':'')}>{Sidebar}{!embedded&&sidebarOpen&&<button className="chat-backdrop" aria-label="Tutup sidebar" onClick={()=>setSidebarOpen(false)}/>}<section className={'assistant chat-main '+(messages.length?'has-messages':'empty-chat')}>{Header}
    {messages.length===0?<div className="empty-chat-content"><div className="conversation"><section className="welcome"><h2>Mau dibantu apa hari ini?</h2></section></div>{(error||historyError)&&<p role={error?'alert':'status'} className="chat-notice">{error||historyError}</p>}{Composer}</div>:<div className="chat-thread"><div className="conversation" ref={conversationRef} aria-live="polite">{messages.map((turn,index)=><article key={index} className="turn"><p className="question">{turn.question}</p><div className="answer"><MarkdownAnswer text={turn.answer.response}/>{!['not_evaluated','deterministic_response','general_knowledge_fallback'].includes(turn.answer.grounding.reason)&&(turn.answer.trust.requires_human||!turn.answer.grounding.grounded)&&<small className="verification-note">Jawaban dokumen belum cukup didukung sumber atau memerlukan peninjauan.</small>}
      {uniqueEvidence(turn.answer.evidence).length>0&&<details className="chat-sources"><summary>Sumber ({uniqueEvidence(turn.answer.evidence).length})</summary>{uniqueEvidence(turn.answer.evidence).map((e,i)=><details className="citation" key={e.document_id+'-'+i}><summary>{e.title}</summary>{e.pages?.length?<p>Halaman: {e.pages.join(', ')}</p>:<p>Halaman sumber belum tersedia.</p>}<p>Referensi: {e.document_id}</p></details>)}</details>}
      <details className="answer-meta"><summary>Detail jawaban</summary><small>{turn.answer.provider_status==='evidence_fast_path'?'Jawaban disusun dari informasi dalam sumber.':'Model yang menjawab: '+turn.answer.model}</small><small>{turn.answer.evidence.length?'Dukungan isi sumber tidak berarti dokumen resmi telah disahkan.':'Jawaban percakapan; tidak dinilai sebagai validasi dokumen resmi.'}</small><small>Jalur: {turn.answer.provider_status}</small><small>Latensi: {turn.answer.latency_ms} ms</small><small>Waktu: {turn.answer.timestamp}</small></details></div></article>)}{pending&&<p role="status">Nusantara sedang memproses pertanyaan…</p>}{(error||historyError)&&<p role={error?'alert':'status'} className="chat-notice">{error||historyError}</p>}{historyFailures.length>0&&<details className="chat-failures"><summary>{historyFailures.length} pesan gagal</summary>{historyFailures.map((turn,i)=><p key={i}>{turn.question} · Permintaan belum berhasil. Detail tersimpan di log layanan.</p>)}</details>}</div>{Composer}</div>}</section></div>;
}

export function OperatorConsole({title='Developer Console'}:{title?:string}){
  const {token,setToken}=useAdminAuth();
  const [status,setStatus]=useState<ModelStatus|null>(null);
  const [providerChoice,setProviderChoice]=useState<'ollama'|'openrouter'|''>('');
  const [models,setModels]=useState<string[]>([]);
  const [choice,setChoice]=useState('');const [pending,setPending]=useState(false);
  const [error,setError]=useState('');const [notice,setNotice]=useState('');
  async function refresh(){setError('');try{const value=await fetchModelStatus();setStatus(value);return value;}catch(e){setStatus(null);setError(e instanceof Error?e.message:'Status belum terverifikasi.');return null;}}
  useEffect(()=>{void refresh();},[]);
  async function loadModels(){setPending(true);setError('');setNotice('');try{
    const targetProvider=providerChoice||status?.provider as 'ollama'|'openrouter'|undefined;
    if(!targetProvider)throw new Error('Provider runtime belum tersedia. Perbarui status terlebih dahulu.');
    const available=await fetchAvailableModels(token,targetProvider);const current=await refresh();
    if(!current||current.revision!==available.observed_revision)throw new Error('Konfigurasi berubah. Muat ulang daftar model.');
    setProviderChoice(targetProvider);setModels(available.models);setChoice(current.provider===targetProvider&&available.models.includes(current.model)?current.model:(available.models[0]??''));
  }catch(e){setModels([]);setChoice('');setError(e instanceof Error?e.message:'Daftar model belum tersedia.');}finally{setPending(false);}}
  async function apply(){if(!status||!choice)return;setPending(true);setError('');setNotice('');try{
    const targetProvider=providerChoice||status.provider as 'ollama'|'openrouter';
    const applied=await selectOperatorModel(choice,status.revision,token,targetProvider);setStatus(applied);setProviderChoice(applied.provider as 'ollama'|'openrouter');setModels([]);setChoice('');
    setNotice('Model diterapkan untuk request berikutnya pada proses ini. Request yang berjalan mempertahankan model awal.');
  }catch(e){await refresh();setError(e instanceof Error?e.message:'Perubahan belum diterapkan.');}finally{setPending(false);}}
  return <><header><div><p className="eyebrow">KENDALI OPERATOR</p><h1>{title}</h1></div><Link to="/">Kembali ke Chat</Link></header>
    <section className="panel"><h2>Model runtime V1</h2><p>Status: <strong>{status?.status??'NOT_VERIFIED'}</strong></p><p>Model aktif: {status?.model??'NOT_VERIFIED'} · Provider: {status?.provider??'NOT_VERIFIED'}</p>
      <p>Pilihan berlaku pada proses ini saja. Konsistensi antarworker belum dibuktikan. Pilihan kembali ke bootstrap setelah proses berhenti.</p>
      <label htmlFor="operator-token">Token operator</label><input id="operator-token" type="password" autoComplete="off" value={token} onChange={e=>{setToken(e.target.value);setModels([]);setChoice('');}}/>
      {status&&<><label htmlFor="operator-provider">Provider runtime</label><select id="operator-provider" disabled={pending||!status.selection_enabled} value={providerChoice||status.provider} onChange={e=>{setProviderChoice(e.target.value as 'ollama'|'openrouter');setModels([]);setChoice('');setError('');setNotice('');}}>{(status.selectable_providers??[status.provider as 'ollama'|'openrouter']).map(provider=><option key={provider} value={provider}>{provider==='ollama'?'Ollama':'OpenRouter'}</option>)}</select></>}
      <button disabled={pending||!token.trim()||!status?.selection_enabled} onClick={()=>void loadModels()}>Muat model tersedia</button>
      {status?.provider==='openrouter'&&<p>Katalog OpenRouter memakai pricing lokal yang sudah terverifikasi. Membaca daftar tidak menguji inferensi atau memanggil model berbayar.</p>}
      {(providerChoice||status?.provider)==='ollama'&&<p>Chat diarahkan ke Ollama lokal. Jika Ollama gagal, request gagal secara eksplisit dan tidak dialihkan ke OpenRouter.</p>}
      {models.length>0&&<><label htmlFor="operator-model">Pilih model tersedia</label><select id="operator-model" disabled={pending} value={choice} onChange={e=>setChoice(e.target.value)}>{models.map(m=><option key={m}>{m}</option>)}</select><button disabled={pending||!choice} onClick={()=>void apply()}>Terapkan model global</button></>}
      <button disabled={pending} onClick={()=>void refresh()}>Perbarui status</button>{pending&&<p role="status">Memeriksa runtime…</p>}{notice&&<p role="status">{notice}</p>}{error&&<p role="alert">{error}</p>}
      <p>Diperiksa: {status?.checked_at?new Date(status.checked_at).toLocaleString('id-ID'):'Belum diperiksa'} · Inferensi terakhir yang cocok: {status?.verified_at?new Date(status.verified_at).toLocaleString('id-ID'):'Belum terverifikasi'}</p><p>Service sehat tidak membuktikan inferensi. Verifikasi inferensi berlaku untuk model, revision, dan proses yang sama selama lima menit.</p>
    </section><section className="panel"><h2>Diagnostik dan batas verifikasi</h2><p>Status Knowledge dan health mengikuti pembacaan API aktual. Jumlah dokumen tidak membuktikan ketepatan semua jawaban atau keberlakuan SOP.</p><p>Policy dan approval eksekusi ditegakkan Backend; tinjau keputusan pada Human Control.</p><p>Riwayat Chat mengikuti sesi V1 existing.</p>
      <details><summary>Request terakhir dan identitas source</summary><pre>{JSON.stringify({process:status?.process_id,source:status?.source_build_id,revision:status?.revision,last_request:status?.last_request},null,2)}</pre><p>Fingerprint source saat import belum membuktikan seluruh loaded build atau model weights.</p></details>
      <p><Link to="/overview">Evidence dan acceptance</Link> · <Link to="/verification">Regression evidence</Link> · <Link to="/knowledge">Knowledge diagnostics</Link></p></section></>;
}
