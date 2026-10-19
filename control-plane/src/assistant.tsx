import {useEffect,useState,useRef} from 'react';
import {Link} from '@tanstack/react-router';
import {ChatSendError,fetchChatHistory,fetchModelStatus,fetchAvailableModels,selectOperatorModel,sendUserChat,type ModelStatus,type PublicChat} from './api';
import {useAdminAuth} from './auth';

export function UserChat({embedded=false}:{embedded?:boolean}={}){
  const Title=embedded?'h2':'h1';
  const [sessions,setSessions]=useState<string[]>(()=>{try{const value=JSON.parse(localStorage.getItem('nusantara-chat-sessions')??'[]');return Array.isArray(value)?value.filter((id:unknown)=>typeof id==='string'&&/^web-[a-f0-9-]{36}$/.test(id)).slice(-20):[];}catch{return [];}});
  const [session,setSession]=useState(()=>{const saved=sessionStorage.getItem('nusantara-chat-session');return saved&&/^web-[a-f0-9-]{36}$/.test(saved)?saved:sessions.at(-1)??`web-${crypto.randomUUID()}`;});
  const currentSession=useRef(session);currentSession.current=session;
  const [model,setModel]=useState<ModelStatus|null>(null);
  const [question,setQuestion]=useState('');
  const [messages,setMessages]=useState<{question:string;answer:PublicChat}[]>([]);
  const [pending,setPending]=useState(false);
  const [error,setError]=useState('');
  const [historyError,setHistoryError]=useState('');
  const [historyFailures,setHistoryFailures]=useState<{question:string;error:string|null;timestamp:string}[]>([]);
  const logicalRequest=useRef<{question:string;session:string;id:string;retryOf?:string}|null>(null);
  async function refreshHistory(active=()=>true){
    const requestedSession=session;
    try{const history=await fetchChatHistory(session);if(active()&&currentSession.current===requestedSession){
      const restored=history.turns.filter(t=>t.answer!==null).map(t=>({question:t.question,answer:t.answer!}));
      setMessages(current=>[...restored,...current.filter(t=>!restored.some(r=>r.answer.timestamp===t.answer.timestamp&&r.question===t.question))]);
      setHistoryFailures(history.turns.filter(t=>t.status==='FAILED'));setHistoryError('');
    }}catch{if(active()&&currentSession.current===requestedSession)setHistoryError('History server belum dapat dibaca. Percakapan yang tampil belum membuktikan riwayat tersimpan.');}
  }
  useEffect(()=>{sessionStorage.setItem('nusantara-chat-session',session);setSessions(old=>{const next=[...old.filter(id=>id!==session),session].slice(-20);localStorage.setItem('nusantara-chat-sessions',JSON.stringify(next));return next;});let active=true;
    void refreshHistory(()=>active);
    return ()=>{active=false;};},[session]);
  useEffect(()=>{void fetchModelStatus().then(setModel).catch(()=>setModel(null));},[]);
  async function send(){
    if(pending||!question.trim())return;
    const submitted=question.trim();setPending(true);setError('');
    if(logicalRequest.current?.question!==submitted||logicalRequest.current.session!==session){
      logicalRequest.current={question:submitted,session,id:crypto.randomUUID().replaceAll('-','')};
    }
    const request=logicalRequest.current;
    try{const answer=await sendUserChat(submitted,session,request.id,request.retryOf);setMessages(old=>[...old,{question:submitted,answer}]);setQuestion('');logicalRequest.current=null;
      void fetchModelStatus().then(setModel).catch(()=>setModel(null));
    }catch(e){
      if(e instanceof ChatSendError&&e.retrySafe){logicalRequest.current={...request,id:crypto.randomUUID().replaceAll('-',''),retryOf:request.id};}
      setError(e instanceof Error?e.message:'Pertanyaan belum berhasil dikirim.');
    }
    finally{setPending(false);void refreshHistory();}
  }
  function newChat(){if(pending)return;logicalRequest.current=null;setSession(`web-${crypto.randomUUID()}`);setMessages([]);setHistoryFailures([]);setQuestion('');setError('');}
  return <div className="assistant"><header><div><p className="eyebrow">NUSANTARA</p><Title>Asisten Anda</Title><p>Tanyakan hal yang ingin Anda pahami.</p><button type="button" disabled={pending} onClick={newChat}>+ New Chat</button></div>{!embedded&&<Link to="/settings">Pengaturan &amp; Teknis</Link>}</header>
    <p className="assistant-model">Model aktif: <strong>{model?.model??'Belum terverifikasi'}</strong><span> Dipilih operator · cara kerja standar</span></p>
    <div className="conversation" aria-live="polite">{messages.length===0?<section className="welcome"><h2>Apa yang bisa saya bantu?</h2><p>Mulai dengan pertanyaan. Sumber jawaban akan ditampilkan jika tersedia.</p></section>:messages.map((turn,index)=><article key={index} className="turn"><p className="question">{turn.question}</p><div className="answer"><p>{turn.answer.response}</p>{(turn.answer.trust.requires_human||!turn.answer.grounding.grounded)&&<small>Jawaban ini membutuhkan verifikasi.</small>}
      {turn.answer.evidence.filter((e,i,all)=>all.findIndex(x=>x.document_id===e.document_id&&x.chunk===e.chunk)===i).map((e,i)=><details className="citation" key={`${e.document_id}-${i}`}><summary>Sumber: {e.title}</summary><blockquote>{e.chunk}</blockquote></details>)}<small>{turn.answer.provider_status==='evidence_fast_path'?'Jawaban disusun dari informasi dalam sumber.':`Model yang menjawab: ${turn.answer.model}`}</small></div></article>)}
      {pending&&<p role="status">Nusantara sedang memproses pertanyaan…</p>}</div>
    {error&&<p role="alert" className="error">{error} Pertanyaan Anda tetap tersedia untuk dicoba lagi.</p>}
    <form onSubmit={e=>{e.preventDefault();void send();}}><label htmlFor="question">Pertanyaan Anda</label><textarea id="question" value={question} onChange={e=>setQuestion(e.target.value)} maxLength={20000} disabled={pending} required/><button disabled={pending||!question.trim()} type="submit">{pending?'Memproses…':'Kirim pertanyaan'}</button></form>
    <details><summary>History sesi ini</summary><label>Sesi pada perangkat ini <select value={session} disabled={pending} onChange={e=>{setMessages([]);setHistoryFailures([]);setSession(e.target.value);}}>{sessions.map((id,i)=><option key={id} value={id}>Percakapan {i+1} · {id.slice(-8)}</option>)}</select></label><button disabled={pending} onClick={()=>void refreshHistory()}>Muat ulang History</button>{historyError&&<p role="status">{historyError}</p>}<p>{messages.length} jawaban ditampilkan. Maksimal 20 hasil terakhir disimpan di server. Identitas sesi tersimpan pada perangkat ini.</p>{historyFailures.map((turn,i)=><p key={i}>{turn.timestamp} · Gagal: {turn.question} · {turn.error}</p>)}<p>+ New Chat memulai sesi baru; riwayat lama tetap tersimpan di server dan tidak dihapus.</p></details>
    <footer>Chat V1. Integrasi Hermes Nous belum tersedia. <Link to="/dashboard">Buka Control Panel</Link></footer></div>;
}

export function OperatorConsole({title='Developer Console'}:{title?:string}){
  const {token,setToken}=useAdminAuth();
  const [status,setStatus]=useState<ModelStatus|null>(null);
  const [models,setModels]=useState<string[]>([]);
  const [choice,setChoice]=useState('');const [pending,setPending]=useState(false);
  const [error,setError]=useState('');const [notice,setNotice]=useState('');
  async function refresh(){setError('');try{const value=await fetchModelStatus();setStatus(value);return value;}catch(e){setStatus(null);setError(e instanceof Error?e.message:'Status belum terverifikasi.');return null;}}
  useEffect(()=>{void refresh();},[]);
  async function loadModels(){setPending(true);setError('');setNotice('');try{
    const available=await fetchAvailableModels(token);const current=await refresh();
    if(!current||current.revision!==available.observed_revision)throw new Error('Konfigurasi berubah. Muat ulang daftar model.');
    setModels(available.models);setChoice(available.models.includes(current.model)?current.model:(available.models[0]??''));
  }catch(e){setModels([]);setChoice('');setError(e instanceof Error?e.message:'Daftar model belum tersedia.');}finally{setPending(false);}}
  async function apply(){if(!status||!choice)return;setPending(true);setError('');setNotice('');try{
    const applied=await selectOperatorModel(choice,status.revision,token);setStatus(applied);setModels([]);setChoice('');
    setNotice('Model diterapkan untuk request berikutnya pada proses ini. Request yang berjalan mempertahankan model awal.');
  }catch(e){await refresh();setError(e instanceof Error?e.message:'Perubahan belum diterapkan.');}finally{setPending(false);}}
  return <><header><div><p className="eyebrow">KENDALI OPERATOR</p><h1>{title}</h1></div><Link to="/ui">Buka Chat V1 lama</Link></header>
    <section className="panel"><h2>Model runtime V1</h2><p>Status: <strong>{status?.status??'NOT_VERIFIED'}</strong></p><p>Model aktif: {status?.model??'NOT_VERIFIED'} · Provider: {status?.provider??'NOT_VERIFIED'}</p>
      <p>Pilihan berlaku pada proses ini saja. Konsistensi antarworker belum dibuktikan. Pilihan kembali ke bootstrap setelah proses berhenti.</p>
      <label htmlFor="operator-token">Token operator</label><input id="operator-token" type="password" autoComplete="off" value={token} onChange={e=>{setToken(e.target.value);setModels([]);setChoice('');}}/>
      <button disabled={pending||!token.trim()||!status?.selection_enabled} onClick={()=>void loadModels()}>Muat model tersedia</button>
      {status?.provider==='openrouter'&&<p>Katalog OpenRouter memakai pricing lokal yang sudah terverifikasi. Membaca daftar tidak menguji inferensi atau memanggil model berbayar.</p>}
      {models.length>0&&<><label htmlFor="operator-model">Pilih model tersedia</label><select id="operator-model" disabled={pending} value={choice} onChange={e=>setChoice(e.target.value)}>{models.map(m=><option key={m}>{m}</option>)}</select><button disabled={pending||!choice} onClick={()=>void apply()}>Terapkan model global</button></>}
      <button disabled={pending} onClick={()=>void refresh()}>Perbarui status</button>{pending&&<p role="status">Memeriksa runtime…</p>}{notice&&<p role="status">{notice}</p>}{error&&<p role="alert">{error}</p>}
    </section><section className="panel"><h2>Diagnostik dan batas verifikasi</h2><p>Status Knowledge dan health mengikuti pembacaan API aktual. Jumlah dokumen tidak membuktikan ketepatan semua jawaban atau keberlakuan SOP.</p><p>Policy dan approval eksekusi ditegakkan Backend; tinjau keputusan pada Human Control.</p><p>Riwayat Chat mengikuti sesi V1 existing.</p>
      <details><summary>Request terakhir dan identitas source</summary><pre>{JSON.stringify({process:status?.process_id,source:status?.source_build_id,revision:status?.revision,last_request:status?.last_request},null,2)}</pre><p>Fingerprint source saat import belum membuktikan seluruh loaded build atau model weights.</p></details>
      <p><Link to="/overview">Evidence dan acceptance</Link> · <Link to="/verification">Regression evidence</Link> · <Link to="/knowledge">Knowledge diagnostics</Link></p></section></>;
}
