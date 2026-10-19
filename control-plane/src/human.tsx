import {createContext, useContext, useEffect, useRef, useState, type ReactNode, type Dispatch, type SetStateAction} from 'react';
import {useQuery} from '@tanstack/react-query';
import {Link, useNavigate, useRouterState} from '@tanstack/react-router';
import {fetchExecutionContext,fetchExecutionHistory,executeReviewedAction,fetchSnapshot,submitIntention,fetchInspectionPreview,fetchEvidencePackage,fetchDecisionRecords,saveEvidenceDecision,type InspectionPreviewResult,type EvidencePackage,type DecisionRecord} from './api';
import {useAdminAuth} from './auth';
import {readiness,plainReason} from './readiness';
import {isAttestation,type SystemHealth,type Snapshot,type Attestation,type PendingIntention} from './schemas';
import {canApprove, counts, emptySession, evidenceKey, gateEvidenceReady, humanCases, limitations, stagePath, stages, workflow,
  attestationKey,attestationWorkflow,type Decision, type HumanResult, type Session, type Stage} from './acceptance';

const SessionContext=createContext<{session:Session;setSession:Dispatch<SetStateAction<Session>>;attestation:boolean;setAttestation:Dispatch<SetStateAction<boolean>>}|null>(null);
export function HumanProvider({children}:{children:ReactNode}) {
  const [session,setSession]=useState(emptySession);
  const [attestation,setAttestation]=useState(false);
  return <SessionContext.Provider value={{session,setSession,attestation,setAttestation}}>{children}</SessionContext.Provider>;
}
function useSession(){const value=useContext(SessionContext);if(!value)throw new Error('HumanProvider required');return value;}
const symbol=(s:string)=>s==='PASS'||s==='CLOSED_PASS'||s==='UNCHANGED'||s==='APPROVE'||s==='AVAILABLE'?'✓':s==='FAIL'||s==='REJECT'?'✕':s==='BLOCKED'||s==='LOCKED'?'!':s==='UNKNOWN'?'?':s==='NOT_VERIFIED'||s==='NOT TESTED'?'○':s==='PENDING'||s==='HOLD'?'◷':'△';
export function HumanStatus({status}:{status:string}) {
  const label=status.replaceAll('_',' ');
  return <span className={`human-status ${status==='PASS'||status==='UNCHANGED'||status==='AVAILABLE'||status==='APPROVE'?'positive':status==='FAIL'||status==='REJECT'?'negative':'caution'}`}>{symbol(status)} {label}</span>;
}
function stepStatus(s:Stage,active:Stage|undefined,session:Session,attestation=false) {
  const flow=attestation?attestationWorkflow(session):workflow(session);
  return !flow.available[s]?'Locked':s===active?'Current':flow.complete[s]?'Completed':'Available';
}
export function HumanNavigation() {
  return <nav aria-label="Knowledge dan operasi">
    <Link to={'/dashboard' as '/overview'}>Ringkasan operasi</Link>
    <Link to={'/knowledge' as '/overview'}>Dokumen dan pemantauan</Link>
    <Link to={'/ui' as '/overview'}>Chat</Link>
    <Link to={'/review-execute' as '/overview'}>Keputusan dan History</Link>
    <p>Pekerjaan rutin mengikuti izin dan kebijakan yang berlaku. Keputusan tidak diperlukan untuk membaca status, memakai Chat, atau melihat History.</p>
  </nav>;
}
export function HumanProgress({stage,session}:{stage:Stage;session:Session}) {
  return <ol className="human-progress" aria-label="Human acceptance progress">{stages.map(s=>{const status=stepStatus(s,stage,session);return <li key={s} data-state={status} aria-current={status==='Current'?'step':undefined}><span aria-hidden="true">{status==='Locked'?'!':status==='Completed'?'✓':status==='Current'?'●':'○'}</span> {s}<small className="step-state">{status}</small></li>;})}</ol>;
}
function Explanation({status}:{status:string}) {
  return <details className="meaning"><summary>What does this mean?</summary><p>{status==='NOT_VERIFIED'?'We do not have evidence proving the current runtime or file state. A responding API is not proof. Inspect the source and request engineering verification.':status==='PASS'?'The recorded engineering gate passed within its documented scope. It does not determine your human test result.':status==='PENDING'?'A human has not yet recorded a session decision. Complete the review and choose explicitly.':'This status describes the available evidence. Read the source and known limitations before deciding.'}</p></details>;
}
export function KnownLimitations({state}:{state:SystemHealth}) {
  return <section className="panel human-limits"><h2>Known limitations</h2><p>Warnings remain part of the review. They do not silently change engineering gate results.</p><ul>{limitations(state).map(w=><li key={w}>△ {w}</li>)}</ul></section>;
}
const previewGoals=['Perbaiki RAG Nusantara.','Periksa kenapa jawaban AI kurang akurat.',
  'Buat Nusantara lebih cepat.','Periksa konfigurasi provider.','Cari masalah pada Developer Engine.'];
export function InspectionPreviewPanel(){
  const [goal,setGoal]=useState(previewGoals[0]);
  const [token,setToken]=useState('');
  const [result,setResult]=useState<InspectionPreviewResult|null>(null);
  const [error,setError]=useState('');
  const [pending,setPending]=useState(false);
  const request=useRef<AbortController|null>(null);
  useEffect(()=>()=>request.current?.abort(),[]);
  async function preview(){
    if(request.current)return;
    const controller=new AbortController();request.current=controller;
    setPending(true);setResult(null);setError('');
    const suppliedToken=token;setToken('');
    try{const value=await fetchInspectionPreview(goal,suppliedToken,controller.signal);
      if(!controller.signal.aborted)setResult(value);
    }catch(e){if(!controller.signal.aborted)setError(e instanceof Error?e.message:'Preview unavailable.');}
    finally{if(!controller.signal.aborted){request.current=null;setPending(false);}}
  }
  return <section className="panel" aria-label="Inspection plan preview"><h2>Inspection plan preview</h2>
    <p>Planning only. No files are inspected and no plan is executed. This does not record a human test or decision.</p>
    <label>Engineering goal<select value={goal} disabled={pending} onChange={e=>{setGoal(e.target.value);setResult(null);setError('');}}>{previewGoals.map(g=><option key={g}>{g}</option>)}</select></label>
    <label>Admin token<input type="password" autoComplete="off" value={token} disabled={pending} onChange={e=>setToken(e.target.value)}/></label>
    <p>The token stays in memory and clears when submitted or when this panel closes.</p>
    <button disabled={pending||!token.trim()} onClick={()=>void preview()}>{pending?'Preparing preview…':'Preview inspection plan'}</button>
    {error&&<p role="alert">{error}</p>}
    {result&&<div role="region" aria-label="Preview evidence"><p>PREVIEW READY · candidates have not been inspected.</p>
      <p>{result.inspection_preview.understanding}</p><p>Source: {result.source} · Captured: {result.captured_at}</p>
      <p>Runtime identity, active process build and provider/model correlation: NOT VERIFIED.</p>
      <p>Ultimate goal requirements and root cause remain unknown. Human review and decision are separate.</p>
      <h3>Proposed static inspection</h3><ol>{result.inspection_preview.plan.map((s,i)=><li key={i}>{s.step}</li>)}</ol>
      <h3>Candidate files</h3><ul>{result.inspection_preview.likely_files.map(f=><li key={f}><code>{f}</code></li>)}</ul>
      <p>{result.inspection_preview.next_step}</p><details><summary>Preview evidence details</summary><pre>{JSON.stringify(result,null,2)}</pre></details>
    </div>}
  </section>;
}
export function HumanPage({stage}:{stage:Stage}) {
  const q=useQuery({queryKey:['control-plane','snapshot'],queryFn:({signal})=>fetchSnapshot(signal)});
  const navigate=useNavigate();
  return <><header><div><div className="eyebrow">HUMAN ACCEPTANCE CONSOLE / STEP {stages.indexOf(stage)+1} OF 5</div><h1>{stage==='Test'?'Human Test':stage}</h1></div><button onClick={()=>void q.refetch()} disabled={q.isFetching}>{q.isFetching?'Reading evidence…':'Refresh evidence'}</button></header>
    {(q.isPending||q.isError)&&<HumanProgress stage={stage} session={emptySession()}/>}
    {q.isPending?<section className="panel" role="status"><h2>Reading evidence</h2><p>Please wait. No test or decision has been inferred.</p></section>:q.isError?<section className="panel error" role="alert"><h2>Evidence unavailable</h2><p>We cannot currently verify this information. System state is UNKNOWN. No healthy state has been inferred.</p><p>Check the evidence source, then retry. Human approval is unavailable while evidence cannot be read.</p><button onClick={()=>void q.refetch()}>Retry</button><details><summary>Technical Details</summary><code>{q.error.message}</code></details></section>:<><p className="snapshot-meta">Evidence read {new Date(q.data.fetchedAt).toLocaleTimeString()} · API response {q.data.latencyMs} ms</p><HumanContent stage={stage} state={q.data.state} busy={q.isFetching} inspectRuntime={()=>void navigate({to:'/runtime'})} navigate={s=>void navigate({to:stagePath[s] as '/overview'})}/></>}
    <footer>Human review session · engineering evidence remains read-only. <span>Session results clear when this page is reloaded.</span></footer></>;
}
export function HumanContent(props:{stage:Stage;state:Snapshot;navigate:(s:Stage)=>void;inspectRuntime:()=>void;busy?:boolean}) {
  const {setAttestation}=useSession();
  const attestation=isAttestation(props.state);
  useEffect(()=>setAttestation(attestation),[attestation,setAttestation]);
  return isAttestation(props.state)?<AttestationContent {...props} state={props.state}/>:<NormalHumanContent {...props} state={props.state}/>;
}
export function AttestationIdentity({state}:{state:Attestation}){
  return <section className="panel"><h2>ATTESTATION evidence</h2><dl>
    <dt>Evidence type</dt><dd>{state.evidence_type}</dd><dt>Evidence version</dt><dd>{state.evidence_version}</dd>
    <dt>Identity scope</dt><dd>SCOPED_LOADED_CODE — not FULL_APPLICATION_BUILD</dd>
    <dt>Verification state</dt><dd>{state.status}</dd><dt>Runtime identity</dt><dd>{state.binding.runtime_identity}</dd>
    <dt>Authorization state</dt><dd>Live actions: {state.live_actions}; operator: {state.operator_policy}</dd>
    <dt>Target</dt><dd>{state.binding.target}</dd><dt>Process PID / start</dt><dd>{state.binding.pid} / {String(state.binding.process_start)} (Windows FILETIME numeric projection; browser precision may be limited)</dd>
    <dt>Runtime instance</dt><dd>{state.binding.runtime_instance}</dd><dt>SOURCE_SNAPSHOT</dt><dd>{state.binding.source_snapshot}</dd>
    <dt>SCOPED_LOADED_CODE</dt><dd>{state.binding.scoped_loaded_code}</dd><dt>ACTIVE_PROCESS_BUILD</dt><dd>{state.binding.active_process_build}</dd>
    <dt>Source</dt><dd>{state.source}</dd><dt>Captured</dt><dd>{state.created_at}</dd>
  </dl><p>SOURCE_SNAPSHOT != ACTIVE_PROCESS_BUILD. No provider health or live success is inferred.</p></section>;
}
function AttestationContent({stage,state,navigate,busy=false}:{stage:Stage;state:Attestation;navigate:(s:Stage)=>void;busy?:boolean}){
  const {session,setSession}=useSession(),key=attestationKey(state);
  const activeKey=useRef(key);activeKey.current=key;
  const current=session.fingerprint===key?session:emptySession(key);
  const [pending,setPending]=useState<PendingIntention|null>(null),[sending,setSending]=useState(false),[error,setError]=useState('');
  const [submittedKey,setSubmittedKey]=useState<string|null>(null);
  useEffect(()=>{if(session.fingerprint!==key){setSession(emptySession(key));setPending(null);setError('');}},[key,session.fingerprint,setSession]);
  const flow=attestationWorkflow(current);
  const update=(change:Partial<Session>)=>setSession({...current,...change,reviewReviewed:'results' in change?false:change.reviewReviewed??current.reviewReviewed});
  const submit=async()=>{
    if(sending||busy||submittedKey===key||!flow.available.Decision)return;
    setSubmittedKey(key);setSending(true);setError('');
    try{const result=await submitIntention(state);if(activeKey.current===key)setPending(result);}catch(e){if(activeKey.current===key)setError(e instanceof Error?e.message:'Intention unavailable. No authority granted.');}finally{setSending(false);}
  };
  if(!flow.available[stage])return <section className="panel" aria-label="Locked stage"><h2>{stage} — Locked</h2><p>Review the current ATTESTATION evidence and preceding observations first.</p><button onClick={()=>navigate('System')}>Go to System</button></section>;
  return <><AttestationIdentity state={state}/><p>Automated Test Evidence ≠ Human Observation ≠ Authenticated Server Decision.</p>
    <p>R2-A8: BLOCKED / NOT_VERIFIED. Runtime Identity: NOT_VERIFIED. ARM and EXECUTE are NOT_AUTHORIZED.</p>
    {stage==='System'&&<section className="panel"><h2>System limitations</h2><p>This scoped projection does not prove full build identity. Native confirmation is unavailable in this integration.</p><label><input type="checkbox" checked={current.systemReviewed} onChange={e=>update({systemReviewed:e.target.checked,evidenceReviewed:false,reviewReviewed:false})}/> I have read the ATTESTATION scope and limitations.</label><button disabled={!current.systemReviewed||busy} onClick={()=>navigate('Evidence')}>Continue to Evidence</button></section>}
    {stage==='Evidence'&&<section className="panel"><h2>Evidence boundary</h2><p>Automated results are not attached to this process snapshot; prior isolated PASS_SCOPED is not live evidence.</p><p>Provider receipt: {state.provider_receipt?'Observed scoped receipt; no live verification inferred.':'Unavailable — NOT_VERIFIED'}</p><label><input type="checkbox" checked={current.evidenceReviewed} onChange={e=>update({evidenceReviewed:e.target.checked,reviewReviewed:false})}/> I inspected the exact evidence version and identity scope.</label><button disabled={!current.evidenceReviewed||busy} onClick={()=>navigate('Test')}>Continue to Human Test</button></section>}
    {stage==='Test'&&<section className="panel"><h2>Human observations only</h2>{humanCases.filter(c=>['runtime','separate','boundary'].includes(c.id)).map(c=><div key={c.id}><h3>{c.title}</h3><p>{c.expected}</p><p>{current.results[c.id]}</p><div role="group" aria-label={`Observation ${c.id}`}>{(['PASS','FAIL','BLOCKED'] as HumanResult[]).map(result=><button key={result} disabled={busy} onClick={()=>update({results:{...current.results,[c.id]:result}})}>{result}</button>)}</div></div>)}<button disabled={!flow.available.Review||busy} onClick={()=>navigate('Review')}>Continue to Review</button></section>}
    {stage==='Review'&&<section className="panel"><h2>Review scoped evidence</h2><p>Human observations do not change server decisions or identity status. Failed or blocked observations remain visible.</p>{['runtime','separate','boundary'].map(id=><p key={id}>{id}: {current.results[id]}</p>)}<label><input type="checkbox" checked={current.reviewReviewed} onChange={e=>update({reviewReviewed:e.target.checked})}/> I reviewed these observations and the NOT_VERIFIED limitations.</label><button disabled={!current.reviewReviewed||busy} onClick={()=>navigate('Decision')}>Continue to Decision</button></section>}
    {stage==='Decision'&&<section className="panel"><h2>Bounded browser intention</h2><p>This action creates PENDING only. It cannot APPROVE, authenticate an operator, ARM, EXECUTE or issue a permit.</p><button disabled={sending||busy||submittedKey===key} onClick={()=>void submit()}>Create PENDING intention</button>{error&&<p role="alert">{error}</p>}{pending&&<div role="status"><p>{pending.state} — untrusted intention; no authorization granted.</p><p>Review {pending.review_id}; evidence {pending.evidence_version}; scope {pending.scope}; server expiry {pending.expires_at}</p></div>}<h3>Server review states</h3>{state.reviews.map(r=><p key={r.review_id}>{r.review_id}: {r.state}; expires {r.expires_at}</p>)}<p>Native confirmation: not activated. No live IPC bridge is implemented.</p></section>}
  </>;
}
function NormalHumanContent({stage,state,navigate,inspectRuntime,busy=false}:{stage:Stage;state:SystemHealth;navigate:(s:Stage)=>void;inspectRuntime:()=>void;busy?:boolean}) {
  const {session,setSession}=useSession();const key=evidenceKey(state);
  const [changed,setChanged]=useState(false);
  useEffect(()=>{
    if(session.fingerprint!==key){if(session.fingerprint!==null)setChanged(true);setSession(emptySession(key));}
  },[key,session.fingerprint,setSession]);
  const current=session.fingerprint===key?session:emptySession(key);
  const update=(change:Partial<Session>)=>setSession({...current,...change,
    evidenceReviewed:change.systemReviewed===false?false:change.evidenceReviewed??current.evidenceReviewed,
    reviewReviewed:('results' in change||'systemReviewed' in change||'evidenceReviewed' in change)?false:change.reviewReviewed??current.reviewReviewed,
    receipt:'receipt' in change?change.receipt??null:null});
  const ready=canApprove(state,current)&&!busy;const totals=counts(current);const warnings=limitations(state);
  const flow=workflow(current);
  const gatePass=state.gates.filter(g=>/^R3\.(?:[1-9]|1[0-4])$/.test(g.id)&&g.status==='PASS').length;
  if(!flow.available[stage])return <><HumanProgress stage={stage} session={current}/>{changed&&<p role="status">Evidence changed. Review the new evidence from System.</p>}<section className="panel" aria-label="Locked stage"><h2>{stage==='Test'?'Human Test':stage} — Locked</h2><p>Complete these prerequisites to unlock this stage. No human result or decision has been inferred.</p><ul>{flow.blockers[stage].map(reason=><li key={reason}>{reason}</li>)}</ul><button onClick={()=>navigate(flow.next)}>Go to {flow.next==='Test'?'Human Test':flow.next} →</button></section>{stage==='Decision'&&<DecisionPanel state={state} session={current} ready={false} busy={busy} update={update} navigate={navigate} readOnly/>}</>;
  return <>
    <HumanProgress stage={stage} session={current}/>
    {stage==='System'&&<InspectionPreviewPanel/>}
    {changed&&<div className="review-notice" role="status">Evidence changed. Previous human results, acknowledgements and decisions were cleared. Review the new evidence before deciding.</div>}
    <div className="session-boundary"><strong>Review scope: Control Plane UI acceptance.</strong> Your selections stay in this session. They do not approve R2 authorization or modify R2/R3, production or engineering state.</div>
    {stage==='System'&&<><section className="human-intro"><div className="eyebrow">01 / UNDERSTAND THE SYSTEM</div><h2>Start with what we can prove.</h2><p>This console helps you inspect evidence, perform your own tests and make an explicit review decision.</p></section><div className="human-cards">
      <StatusCard title="Evidence API" status="AVAILABLE" text="This evidence request succeeded. It does not prove the model or production runtime is healthy."/>
      <StatusCard title="Engineering evidence" status={gateEvidenceReady(state)?'PASS':'NOT_VERIFIED'} text={`${gatePass} of 14 R3 gates are recorded PASS. Inspect each source before accepting the review.`}/>
      <StatusCard title="Runtime identity" status={state.runtime.current_status} text="This status comes from engineering evidence. A human click cannot mark an unverified runtime AVAILABLE."><button className="secondary" onClick={inspectRuntime}>Inspect runtime evidence →</button><button className="secondary" disabled={!flow.available.Test} onClick={()=>navigate('Test')}>Record my runtime display test →</button></StatusCard>
      <StatusCard title="Human decision" status={current.receipt?.decision??'PENDING'} text="You decide after reviewing evidence and completing human tests. Nothing is selected automatically."><button disabled={!flow.available.Decision} onClick={()=>navigate('Decision')}>Open Human Decision →</button></StatusCard>
    </div><p>Human Test unlocks after System and all Evidence are acknowledged. Human Decision unlocks after all eight tests and Review acknowledgement.</p><details className="panel"><summary>Engineering phase details</summary>{state.phases.map(p=><p key={p.id}><strong>{p.id}</strong> · {p.name} · <span>{p.status}</span></p>)}</details><KnownLimitations state={state}/><section className="panel next-action"><h2>What should I do next?</h2><p>Read the limitations, acknowledge this system summary, then inspect the evidence.</p><label className="check"><input type="checkbox" checked={current.systemReviewed} onChange={e=>update({systemReviewed:e.target.checked})}/> I have read the system summary and limitations.</label><p className="checklist-help">Click the checkbox or its text. You can also use Acknowledge System below. No acknowledgement is selected automatically.</p><button className="secondary" disabled={current.systemReviewed} onClick={()=>update({systemReviewed:true})}>Acknowledge System</button>{busy&&<p role="status">Reading evidence. You can acknowledge the displayed summary; Continue waits for this request to finish.</p>}<button disabled={!current.systemReviewed||busy} onClick={()=>navigate('Evidence')}>Continue to Evidence →</button></section></>}
    {stage==='Evidence'&&<><section className="human-intro"><div className="eyebrow">02 / INSPECT ENGINEERING EVIDENCE</div><h2>What supports the engineering result?</h2><p>Open each gate, read its source and limitations, then click I have inspected this source. Engineering PASS does not record your inspection.</p></section><OfflineEvidenceRegistry/><div className="gate-list">{Array.from({length:14},(_,i)=>`R3.${i+1}`).map(id=>{
      const gate=state.gates.find(g=>g.id===id);const refs=gate?.evidence.map(ref=>state.evidence.find(e=>e.id===ref)).filter(e=>!!e)??[];
      return <details className="panel gate-card" key={id}><summary><strong>{id}</strong><HumanStatus status={gate?.status??'UNKNOWN'}/><span>{current.inspected.includes(id)?'✓ Inspected':'Inspection pending'} · View Evidence</span></summary><dl><dt>What</dt><dd>The source records this engineering gate as {gate?.status??'UNKNOWN'}.</dd><dt>Why</dt><dd>This gate is part of the R3 effective configuration review. A recorded gate does not assign a human test result.</dd><dt>Source</dt><dd>{refs.length?refs.map(e=><div key={e.id}><code>{e.reference}</code><small>SHA-256 {e.sha256??'NOT VERIFIED'}</small><HumanStatus status={e.status==='VERIFIED_ARTIFACT'?'PASS':'NOT_VERIFIED'}/></div>):'Source unavailable — NOT VERIFIED'}</dd><dt>Integrity</dt><dd>{refs.length&&refs.every(e=>e.status==='VERIFIED_ARTIFACT'&&e.sha256)?'SHA-256 verified against the recorded reference.':'NOT VERIFIED — a source or hash is missing.'}</dd><dt>Limitation</dt><dd>Historical engineering evidence. RAG receipts are fixtures, not current production retrieval or runtime attestation.</dd></dl><button aria-label={`I have inspected ${id} source`} disabled={current.inspected.includes(id)||refs.length===0||refs.length!==gate?.evidence.length} onClick={()=>{if(refs.length>0&&refs.length===gate?.evidence.length)setSession(prev=>({...prev,inspected:[...new Set([...prev.inspected,id])],reviewReviewed:false,receipt:null}));}}>{current.inspected.includes(id)?'✓ Inspection recorded':'I have inspected this source'}</button>{(refs.length===0||refs.length!==gate?.evidence.length)&&<p>Source missing. Inspection cannot be recorded.</p>}</details>;
    })}</div><KnownLimitations state={state}/><section className="panel next-action"><h2>What should I do next?</h2><p>{current.inspected.length} of 14 gates inspected. Each source needs your explicit inspection acknowledgement.</p><p>{current.inspected.length<14?`Still to inspect: ${Array.from({length:14},(_,i)=>`R3.${i+1}`).filter(id=>!current.inspected.includes(id)).join(', ')}. Open each card above and click I have inspected this source.`:'All 14 source inspections are recorded. You can now acknowledge the evidence checklist.'}</p><label className="check"><input type="checkbox" disabled={current.inspected.length<14} checked={current.evidenceReviewed} onChange={e=>update({evidenceReviewed:e.target.checked})}/> I have inspected all gate sources and read their limitations.</label><button disabled={!current.evidenceReviewed||busy} onClick={()=>navigate('Test')}>Continue to Human Test →</button></section></>}
    {stage==='Test'&&<><section className="human-intro"><div className="eyebrow">03 / PERFORM YOUR OWN TESTS</div><h2>Record what you observed.</h2><p>Engineering PASS is not human PASS. Perform each check before selecting a result. Results stay NOT TESTED until you choose.</p></section><div className="human-test-list">{humanCases.map((c,i)=><section className="panel human-case" key={c.id}><div className="eyebrow">TEST CASE {String(i+1).padStart(2,'0')}</div><h2>{c.title}</h2><p><strong>Expected:</strong> {c.expected}</p><HumanStatus status={current.results[c.id]}/><div className="result-buttons" role="group" aria-label={`Result for ${c.id}`}>{(['PASS','FAIL','BLOCKED'] as HumanResult[]).map(result=><button key={result} disabled={busy} aria-pressed={current.results[c.id]===result} onClick={()=>update({results:{...current.results,[c.id]:result}})}>{symbol(result)} {result}</button>)}<button disabled={busy} onClick={()=>update({results:{...current.results,[c.id]:'NOT TESTED'}})}>Clear result</button></div></section>)}</div><section className="panel next-action"><h2>What should I do next?</h2><p>{totals.pass} PASS · {totals.fail} FAIL · {totals.blocked} BLOCKED · {totals.untested} NOT TESTED</p><button disabled={!flow.available.Review||busy} onClick={()=>navigate('Review')}>Review human results →</button></section></>}
    {stage==='Review'&&<><section className="human-intro"><div className="eyebrow">04 / REVIEW BEFORE DECIDING</div><h2>Compare evidence with your experience.</h2><p>These are different results. Both remain visible.</p></section><section className="panel review-summary"><h2>Human review</h2><div className="grid-two"><div><h3>Engineering evidence</h3><p>✓ {gatePass} recorded PASS / 14 gates</p><HumanStatus status={gateEvidenceReady(state)?'PASS':'NOT_VERIFIED'}/></div><div><h3>Human tests</h3><p>✓ {totals.pass} PASS · ✕ {totals.fail} FAIL · ! {totals.blocked} BLOCKED · ○ {totals.untested} NOT TESTED</p></div></div><p>Known limitations: {warnings.length}</p><p>Current runtime: <HumanStatus status={state.runtime.current_status}/></p><Explanation status={state.runtime.current_status}/><h3>{current.reviewReviewed?'REVIEW ACKNOWLEDGED':'REVIEW ACKNOWLEDGEMENT REQUIRED'}</h3><p>PASS, FAIL and BLOCKED are all explicit human test results. Only all-PASS tests with verified engineering sources permit approval; REJECT or HOLD remains available after this review is acknowledged.</p><ApprovalChecklist state={state} session={current} busy={busy} navigate={navigate}/><label className="check"><input type="checkbox" checked={current.reviewReviewed} disabled={busy} onChange={e=>update({reviewReviewed:e.target.checked})}/> I have reviewed the evidence, all human test results and unresolved limitations.</label><button disabled={!flow.available.Decision||busy} onClick={()=>navigate('Decision')}>Continue to Decision →</button><button className="secondary" onClick={()=>navigate('Test')}>Return to Human Test</button></section><KnownLimitations state={state}/></>}
    {stage==='Decision'&&<DecisionPanel state={state} session={current} ready={ready} busy={busy} update={update} navigate={navigate}/>}
  </>;
}
function StatusCard({title,status,text,children}:{title:string;status:string;text:string;children?:ReactNode}) {return <section className="panel"><h2>{title}</h2><HumanStatus status={status}/><p>{text}</p><Explanation status={status}/>{children}</section>;}
function ApprovalChecklist({state,session,busy,navigate}:{state:SystemHealth;session:Session;busy:boolean;navigate:(s:Stage)=>void}) {
  const totals=counts(session);
  const inspected=Array.from({length:14},(_,i)=>`R3.${i+1}`).filter(id=>session.inspected.includes(id)).length;
  return <section aria-label="Approval prerequisites"><h3>Approval prerequisites</h3><p>These are review requirements, not an application error. Use the buttons to complete a missing step. Runtime status remains evidence-based.</p><ul>
    <li>{session.systemReviewed?'✓':'◷'} System summary {session.systemReviewed?'acknowledged':'not acknowledged'}. {!session.systemReviewed&&<button className="secondary" onClick={()=>navigate('System')}>Review System</button>}</li>
    <li>{inspected===14&&session.evidenceReviewed?'✓':'◷'} {inspected} / 14 gate sources inspected; evidence {session.evidenceReviewed?'acknowledged':'not acknowledged'}. {(!session.evidenceReviewed||inspected<14)&&<button className="secondary" onClick={()=>navigate('Evidence')}>Inspect Evidence</button>}</li>
    <li>{totals.pass===humanCases.length?'✓':'◷'} Human tests: {totals.pass} / {humanCases.length} PASS, {totals.fail} FAIL, {totals.blocked} BLOCKED, {totals.untested} NOT TESTED. {totals.pass!==humanCases.length&&<button className="secondary" onClick={()=>navigate('Test')}>Complete Human Test</button>}</li>
    <li>{session.reviewReviewed?'✓':'◷'} Review {session.reviewReviewed?'acknowledged':'not acknowledged'}.</li><li>{gateEvidenceReady(state)?'✓':'○'} Engineering gate sources {gateEvidenceReady(state)?'verified':'NOT VERIFIED'}. {!gateEvidenceReady(state)&&<button className="secondary" onClick={()=>navigate('Evidence')}>Review missing evidence</button>}</li>
    {busy&&<li>◷ Reading evidence. Approval waits for the current request to finish.</li>}
  </ul></section>;
}
function OfflineEvidenceRegistry(){
  const q=useQuery({queryKey:['control-plane','evidence-package'],queryFn:fetchEvidencePackage,refetchInterval:30000});
  if(q.isPending)return <section className="panel" role="status">Loading offline evidence registry…</section>;
  if(q.isError)return <section className="panel error" role="alert"><h2>Evidence registry unavailable</h2><p>{q.error.message}</p></section>;
  const pkg=q.data;
  return <section className="panel" aria-label="Offline evidence registry"><h2>Offline evidence registry</h2><p>Package <code>{pkg.package_id}</code> · {pkg.read_scope} · runtime {pkg.runtime_status}</p>
    <ul>{pkg.criteria.map(c=><li key={c.id}><strong>{c.id} · {c.summary}</strong>: <HumanStatus status={c.status}/>{c.reason&&<> — {c.reason}</>}</li>)}</ul>
    <h3>Artifact inventory</h3>{pkg.evidence.map(e=><p key={e.path}><code>{e.path}</code> · {e.classification} / {e.validation_status} · SHA-256 {e.sha256??'not available'}{e.reason&&<> · {e.reason}</>}</p>)}
    <h3>Open blockers</h3>{pkg.blockers.length?pkg.blockers.map(b=><p key={b.id}>{b.id}: {b.reason}</p>):<p>No current evidence blockers.</p>}
  </section>;
}
function DecisionPanel({state,session,ready,busy,update,navigate,readOnly=false}:{state:SystemHealth;session:Session;ready:boolean;busy:boolean;update:(change:Partial<Session>)=>void;navigate:(s:Stage)=>void;readOnly?:boolean}) {
  const {token}=useAdminAuth();const [choice,setChoice]=useState<Decision|null>(null);const [notes,setNotes]=useState('');const [saving,setSaving]=useState(false);const [error,setError]=useState('');
  const [submittedRecord,setSubmittedRecord]=useState<DecisionRecord|null>(null);const savingRef=useRef(false);const [authVersion,setAuthVersion]=useState(0);
  const packageQuery=useQuery({queryKey:['control-plane','evidence-package'],queryFn:fetchEvidencePackage,refetchInterval:30000});
  const packageId=packageQuery.data?.package_id;
  // The credential stays out of query keys/caches; a token change gets a fresh audit read.
  useEffect(()=>setAuthVersion(version=>version+1),[token]);
  const auditQuery=useQuery({queryKey:['control-plane','decisions',authVersion],queryFn:()=>fetchDecisionRecords(token),enabled:!!token.trim()});
  const auditVerified=auditQuery.isSuccess&&!auditQuery.isError;
  const records=auditVerified?(auditQuery.data??[]):[];
  const activeRecord=packageId?records.filter(record=>record.package_id===packageId).at(-1):undefined;
  const submittedForActive=submittedRecord&&submittedRecord.package_id===packageId?submittedRecord:undefined;
  const displayActiveRecord=activeRecord??submittedForActive;
  const latestRecord=records.at(-1);
  const staleRecord=!activeRecord&&!submittedForActive&&latestRecord&&packageId&&latestRecord.package_id!==packageId?latestRecord:undefined;
  const finalizedPass=!!activeRecord&&auditVerified&&activeRecord.decision==='PASS'&&packageQuery.data?.pass_allowed===true;
  useEffect(()=>{setChoice(null);setNotes('');setError('');if(packageId){if(submittedRecord&&submittedRecord.package_id!==packageId)setSubmittedRecord(null);if(session.receipt&&session.receipt.packageId!==packageId)update({receipt:null});}},[packageId]);
  async function save(){
    if(savingRef.current)return;
    if(!choice||!packageId||!token.trim()||!auditVerified||displayActiveRecord||readOnly)return;
    savingRef.current=true;setSaving(true);setError('');
    try{const record=await saveEvidenceDecision({packageId,decision:choice,notes:notes.trim(),token});
      setSubmittedRecord(record);
      update({receipt:{decision:record.decision,reason:'Server recorded decision',notes:record.notes,timestamp:record.timestamp,fingerprint:record.package_id,decisionId:record.decision_id,packageId:record.package_id,reviewer:record.reviewer_principal}});
      setChoice(null);
      // Read-back verifies the persisted record and complete hash chain. If it fails,
      // retain the server receipt and show that verification is pending rather than retrying POST.
      void auditQuery.refetch();
    }catch(e){setError(e instanceof Error?e.message:'Decision could not be recorded.');void packageQuery.refetch();}
    finally{savingRef.current=false;setSaving(false);}
  }
  const pkg:EvidencePackage|undefined=packageQuery.data;
  return <><section className="human-intro"><div className="eyebrow">05 / HUMAN DECISION</div><h2>Decide against the current evidence package.</h2><p>PASS, FAIL, or HOLD. The server binds the decision to its package ID and records an audit entry.</p></section>
    {packageQuery.isPending?<section className="panel" role="status">Loading offline evidence package…</section>:packageQuery.isError?<section className="panel error" role="alert"><h2>Evidence package unavailable</h2><p>{packageQuery.error.message}</p></section>:pkg&&<>
      <section className="panel"><h2>Evidence summary</h2><p>Package <code>{pkg.package_id}</code> · generated {pkg.generated_at}</p><p>Read scope: {pkg.read_scope} · runtime: {pkg.runtime_status}</p><ul>{pkg.criteria.map(c=><li key={c.id}><strong>{c.id} · {c.summary}</strong>: <HumanStatus status={c.status}/>{c.reason&&<> — {c.reason}</>}</li>)}</ul>
        <h3>Evidence artifacts</h3>{pkg.evidence.map(e=><p key={e.path}><code>{e.path}</code> · {e.classification} / {e.validation_status} · SHA-256 {e.sha256??'not available'}{e.reason&&<> · {e.reason}</>}{e.results_path&&<> · Results <code>{e.results_path}</code> · SHA-256 {e.results_sha256}</>}{e.result_artifacts?.map(artifact=><small key={artifact.path}> · <code>{artifact.path}</code> · SHA-256 {artifact.sha256}</small>)}</p>)}
        <h3>Blockers</h3>{pkg.blockers.length?pkg.blockers.map(b=><p key={b.id}>{b.id}: {b.reason}</p>):<p>No package blockers recorded.</p>}
        <p>PASS {pkg.pass_allowed?'available':'disabled until every criterion is verified'}; FAIL and HOLD remain available. Runtime remains NOT VERIFIED independently.</p>
      </section>
      {!token.trim()&&<section className="panel" role="status">To read the protected decision audit after a reload, enter the operator token in <Link to="/console">Developer Console</Link>. The decision itself remains on the server.</section>}
      {token.trim()&&!auditVerified&&auditQuery.isPending&&<p role="status">Verifying saved decisions and the audit hash chain…</p>}
      {auditQuery.isError&&<p role="alert">{auditQuery.error.message}</p>}
      {staleRecord&&<section className="panel review-notice" role="status"><h2>Previous decision is for an older package</h2><p>{staleRecord.decision} · {staleRecord.decision_id} applies to package {staleRecord.package_id}, not the current package {pkg.package_id}. Review the current package before making a new decision.</p></section>}
      {displayActiveRecord&&<section className="panel receipt" aria-label="Server decision record">
        <h2>Server decision record</h2>
        <p role="status">{displayActiveRecord.decision} — {finalizedPass?'Saved / Finalized':activeRecord&&auditVerified?'Saved; audit chain verified':'Server accepted the decision; audit read-back is not verified yet'} · Decision ID {displayActiveRecord.decision_id}</p>
        <p>{displayActiveRecord.decision_id} · {displayActiveRecord.decision} · {displayActiveRecord.timestamp}</p><p>Reviewer: {displayActiveRecord.reviewer_principal} via {displayActiveRecord.authentication}</p><p>Package: {displayActiveRecord.package_id}</p><p>Audit hash: {displayActiveRecord.record_hash}</p>
        {displayActiveRecord.package_id===pkg.package_id&&displayActiveRecord.decision==='PASS'&&!pkg.pass_allowed&&<p role="alert">The current package does not permit PASS; review its blockers before treating this record as final.</p>}
        {!auditVerified&&submittedForActive&&<button className="secondary" disabled={auditQuery.isFetching} onClick={()=>void auditQuery.refetch()}>{auditQuery.isFetching?'Verifying…':'Retry audit verification'}</button>}
        {auditVerified&&activeRecord&&<><p>Test references: {activeRecord.test_evidence.join(', ')||'none'}</p><p>Hash chain and separate head checkpoint detect edits and single-file truncation. A filesystem administrator who changes both files together can still replace local records; no external anchor is configured.</p></>}
      </section>}
      {!readOnly&&!displayActiveRecord&&<section className="panel"><h2>Final human decision</h2><p>Reviewer authorization uses the existing admin token entered in Developer Console. It is a shared token principal, not a unique personal identity.</p>{!auditVerified&&token.trim()&&<p role="status">Decision controls stay disabled until the server audit is readable and its hash chain is verified.</p>}
        <label className="notes">Optional notes<textarea value={notes} onChange={e=>setNotes(e.target.value)} maxLength={2000}/></label>
        <div className="decision-buttons"><button disabled={!token.trim()||!auditVerified||!pkg.pass_allowed||saving||busy} onClick={()=>setChoice('PASS')}>PASS</button><button disabled={!token.trim()||!auditVerified||saving||busy} onClick={()=>setChoice('FAIL')}>FAIL</button><button disabled={!token.trim()||!auditVerified||saving||busy} onClick={()=>setChoice('HOLD')}>HOLD</button></div>
        {choice&&<div className="panel confirmation" role="region" aria-label={`Confirm ${choice}`}><p>Record {choice} for package {pkg.package_id}?</p><button className="secondary" onClick={()=>setChoice(null)}>Cancel</button><button disabled={saving} onClick={()=>void save()}>{saving?'Saving…':`Confirm ${choice}`}</button></div>}{error&&<p role="alert">{error}</p>}
      </section>}
    </>}{!readOnly&&auditVerified&&!displayActiveRecord&&!finalizedPass&&<button className="secondary" onClick={()=>navigate('Review')}>Return to Review</button>}{!packageQuery.isError&&<button className="secondary" onClick={()=>void packageQuery.refetch()}>Refresh package</button>}<KnownLimitations state={state}/>
  </>;
}


export function ExecutionReview({title='Review & Execute V1'}:{title?:string}){
 const {token,setToken}=useAdminAuth();
 const [version,setVersion]=useState(0),[notes,setNotes]=useState(''),[busy,setBusy]=useState(false),[message,setMessage]=useState('');
 const [,tick]=useState(0);
 useEffect(()=>{const timer=setInterval(()=>tick(v=>v+1),1000);return()=>clearInterval(timer);},[]);
 // Cache scope changes with every credential edit; credentials never enter query keys.
 const credential=useRef({value:token,revision:0});
 if(credential.current.value!==token)credential.current={value:token,revision:credential.current.revision+1};
 const scope=credential.current.revision;
 const pkg=useQuery({queryKey:['execution-review','package',version],queryFn:fetchEvidencePackage,retry:false});
 const context=useQuery({queryKey:['execution-review','context',version,scope],queryFn:()=>fetchExecutionContext(token),enabled:!!token.trim(),retry:false,gcTime:0});
 const history=useQuery({queryKey:['execution-review','history',version,scope],queryFn:()=>fetchExecutionHistory(token),enabled:!!token.trim(),retry:false,gcTime:0});
 const model=readiness({token,
   packageState:{state:pkg.isPending?'UNKNOWN':pkg.isError?'BLOCKED':'READY',pkg:pkg.data,reason:pkg.error?.message},
   planState:{state:context.isPending?'UNKNOWN':context.isError?'BLOCKED':'READY',context:context.data,reason:context.error?.message},
   auditState:{state:history.isPending?'UNKNOWN':history.isError?'BLOCKED':'READY',history:history.data,reason:history.error?.message}});
 const active=model.activeDecision;
 const refresh=()=>setVersion(v=>v+1);
 const pending=pkg.isFetching||context.isFetching||history.isFetching;
 const canDecide=model.operatorAuthenticated&&!!pkg.data&&!pending&&!busy;
 const canPass=canDecide&&model.decisionAvailable;
 const canExecute=model.executionReady&&!pending&&!busy;
 const why=!token.trim()?'Masukkan token operator yang sudah tersedia.':!model.operatorAuthenticated?'Autentikasi atau pembacaan History belum berhasil.':context.data?.completed?'Pekerjaan sudah selesai; lihat hasil dan riwayat. Publikasi ulang memerlukan rencana baru.':!model.planReady?'Rencana belum siap; periksa alasan backend.':!model.evidenceValid?'Bukti belum valid; diperlukan pengujian dan paket baru.':!active?'Menunggu keputusan manusia.':model.checks.find(c=>c.id==='EXEC')?.detail;
 async function decide(decision:'PASS'|'FAIL'|'HOLD'){
  if(!pkg.data||!canDecide||(decision==='PASS'&&!canPass))return;
  setBusy(true);setMessage('');
  try{const record=await saveEvidenceDecision({packageId:pkg.data.package_id,decision,notes,token,planBinding:context.data?.plan_binding});
   setMessage(`Keputusan ${record.decision} tersimpan di server.`);setNotes('');}
  catch(e){setMessage(e instanceof Error?e.message:'Keputusan gagal disimpan.');}
  finally{setBusy(false);refresh();}
 }
 async function execute(){
  if(!pkg.data||!active||!canExecute)return;
  setBusy(true);setMessage('');
  try{const result=await executeReviewedAction(token,pkg.data.package_id,active.decision_id);setMessage(`Eksekusi ${result.status}. Berkas berubah: ${result.files_changed.join(', ')}. Hasil tercatat di History.`);}
  catch(e){setMessage(e instanceof Error?e.message:'Eksekusi ditolak.');}
  finally{setBusy(false);refresh();}
 }
 return <>
  <header><div><div className="eyebrow">NUSANTARA V1 / TINJAU DAN JALANKAN</div><h1>{title}</h1></div><button onClick={refresh} disabled={busy||pending}>Muat ulang review</button></header>
  <p>Baca pekerjaan dan hasil pemeriksaannya, lalu pilih keputusan Anda. Bukti valid dan izin eksekusi diperiksa secara terpisah.</p>
  <section className="panel auth-panel" aria-label="Status operator"><h2>Status operator</h2>
   <label className="notes">Token operator<input type="password" autoComplete="off" value={token} onChange={e=>setToken(e.target.value)}/></label>
   <p>{model.operatorAuthenticated?'Operator terautentikasi sebagai pemegang token admin bersama.':token.trim()?'Memeriksa kredensial operator; keputusan terkunci sampai History terbaca.':'Belum ada token operator. Anda masih bisa membaca bukti; keputusan dan History memerlukan autentikasi.'}</p>
   <p>Token hanya berada di memori halaman. Keputusan disimpan di backend.</p>
  </section>
  <section className="panel" aria-label="Apa yang akan dikerjakan"><h2>1. Apa yang akan dikerjakan</h2>
   {!token.trim()?<p>Isi token operator untuk membaca tindakan yang ditawarkan.</p>:context.isPending?<p role="status">Memuat rencana...</p>:context.error?<p role="alert">{context.error.message}</p>:context.data&&<>
    <p><strong>{context.data.objective}</strong></p><p>Dampak: {context.data.expected_change}</p>
    <p>Risiko: {context.data.risk}</p><ul>{context.data.target_files.map(f=><li key={f}>{f}</li>)}</ul>
    <p>Pemulihan: {context.data.rollback}</p><p>Sumber: {context.data.source}. Diperiksa: {context.data.checked_at}</p>
   </>}
  </section>
  <section className="panel" aria-label="Ringkasan pemeriksaan"><h2>2. Apakah sudah siap</h2>
   {pkg.isPending&&<p role="status">Memuat bukti dari backend...</p>}{pkg.error&&<p role="alert">{pkg.error.message}</p>}
   {pkg.data&&<><p>Kelayakan: {model.evidenceValid?'VALID':'BLOCKED'}</p><p>{pkg.data.criteria.filter(c=>c.status==='VALID').length} dari {pkg.data.criteria.length} kriteria tervalidasi.</p><p>Sumber: backend evidence-package. Waktu pengumpulan: {pkg.data.generated_at}.</p><p>Hasil ini mencakup pengujian offline yang dideklarasikan; tidak membuktikan inferensi model atau kesiapan data operasional.</p>
    {pkg.data.blockers.length?<ul>{[...new Set(pkg.data.blockers.map(b=>plainReason(b.reason)))].map(r=><li key={r}>{r}</li>)}</ul>:<p>Tidak ada blocker integritas bukti.</p>}</>}
   <p>Rencana: {context.data?.completed?`Sudah selesai pada ${context.data.completed_at}.`:model.planReady?'Siap ditinjau.':'Belum siap atau belum terbaca.'}</p><p>Izin eksekusi: {canExecute?'Siap diperiksa ulang backend.':why}</p>
   <details><summary>Detail teknis pemeriksaan dan evidence</summary>
    <h3>Lima status terpisah</h3><ul>{model.checks.map(c=><li key={c.id}><strong>{c.id}: {c.label}</strong> — {c.detail}. {c.why}</li>)}</ul>
    {context.data&&<><h3>Pengujian yang diwajibkan</h3><ul>{context.data.tests_required.map(t=><li key={t}>{t}</li>)}</ul><pre>{JSON.stringify(context.data.plan_binding,null,2)}</pre></>}
    {pkg.data&&<pre>{JSON.stringify(pkg.data,null,2)}</pre>}
   </details>
  </section>
  <section className="panel" aria-label="Keputusan manusia"><h2>3. Keputusan pengguna</h2>
   <p>PASS menyetujui tindakan dan versi rencana ini selama 60 menit. FAIL menolak. HOLD menunda. Keputusan terbaru berlaku; seluruh keputusan sebelumnya tetap tercatat.</p>
   <p>Keputusan terkini: {active?.decision??'BELUM ADA'}.</p>
   <label className="notes">Catatan opsional<textarea value={notes} onChange={e=>setNotes(e.target.value)} maxLength={2000}/></label>
   <div className="decision-buttons">{(['PASS','FAIL','HOLD'] as const).map(d=><button key={d} disabled={d==='PASS'?!canPass:!canDecide} title={d==='PASS'&&!canPass?why:!canDecide?'Autentikasi, bukti dan History harus terbaca; tunggu permintaan selesai.':`Simpan ${d}`} onClick={()=>void decide(d)}>{d}</button>)}</div>
   {!canPass&&<p>PASS belum tersedia: {why}</p>}{history.error&&<p role="alert">{history.error.message}</p>}
   {model.staleDecision&&<p>Keputusan sebelumnya berlaku untuk paket lama dan tidak mengizinkan tindakan pada paket sekarang.</p>}
   <button disabled={!canExecute} title={canExecute?'Backend memeriksa kembali bukti, rencana, keputusan dan cakupan sebelum menulis.':why} onClick={()=>void execute()}>Jalankan tindakan yang disetujui</button>
   {!canExecute&&<p>Eksekusi belum tersedia: {why}</p>}
  </section>
  {message&&<p role="status">{message}</p>}
  <section className="panel" aria-label="History"><h2>4. Hasil dan riwayat</h2><p>History dibaca dari server dan tetap tersedia setelah reload.</p>
   {!token.trim()&&<p>Isi token operator untuk membaca History.</p>}{history.isPending&&!!token.trim()&&<p role="status">Memuat History...</p>}
   {history.data&&<>{!history.data.decisions.length&&!history.data.executions.length&&<p>History kosong; belum ada keputusan atau eksekusi.</p>}
    {[...history.data.executions].reverse().map((e,i)=><article key={i}><h3>Eksekusi {e.result}</h3><p>{e.timestamp}</p><p>{e.result==='PASS'?'Penyalinan file selesai.':e.result==='AUTHORIZED_ATTEMPT'?'Percobaan berizin dimulai; belum merupakan hasil akhir.':'Tindakan ditolak atau gagal; periksa alasan dan target sebelum pemulihan.'}</p>{e.files_changed.length>0&&<p>Berkas: {e.files_changed.join(', ')}</p>}{e.reason&&<p>{plainReason(e.reason)}</p>}<details><summary>Detail teknis eksekusi</summary><pre>{JSON.stringify(e,null,2)}</pre></details></article>)}
    {[...history.data.decisions].reverse().map(d=><article key={d.decision_id}><h3>Keputusan {d.decision}</h3><p>{d.timestamp} — {d.reviewer_principal}</p>{d.notes&&<p>{d.notes}</p>}<details><summary>Detail teknis keputusan</summary><pre>{JSON.stringify(d,null,2)}</pre></details></article>)}
   </>}
  </section>
 </>;
}
