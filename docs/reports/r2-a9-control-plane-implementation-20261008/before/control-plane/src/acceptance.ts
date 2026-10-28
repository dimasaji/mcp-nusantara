import type {SystemHealth} from './schemas';

export const stages = ['System', 'Evidence', 'Test', 'Review', 'Decision'] as const;
export type Stage = typeof stages[number];
export const stagePath: Record<Stage, string> = {System:'/overview', Evidence:'/evidence', Test:'/test', Review:'/review', Decision:'/decision'};
export type HumanResult = 'NOT TESTED' | 'PASS' | 'FAIL' | 'BLOCKED';
export type Decision = 'APPROVE' | 'REJECT' | 'HOLD';
export const humanCases = [
  {id:'open', title:'Can I open the Control Plane?', expected:'The console loads and tells me where to begin.'},
  {id:'gates', title:'Can I inspect R3.1–R3.14?', expected:'All 14 recorded gates and their evidence sources can be inspected.'},
  {id:'runtime', title:'Is unverified runtime shown honestly?', expected:'Current runtime remains NOT VERIFIED; historical receipts do not prove it is running now.'},
  {id:'sources', title:'Can I find the evidence source?', expected:'Each gate has a source, an integrity result and a clear explanation.'},
  {id:'limits', title:'Can I read the known limitations?', expected:'Fixture, temporary storage, Git coverage and protected-file limitations remain visible.'},
  {id:'separate', title:'Are my results separate from engineering evidence?', expected:'Human tests start NOT TESTED. Only my selections change human results.'},
  {id:'refresh', title:'Does refreshing keep the review consistent?', expected:'Unchanged evidence preserves my review; changed evidence requires a new review.'},
  {id:'boundary', title:'Is the decision boundary clear?', expected:'A session decision does not change R2/R3, authorize production, or modify engineering state.'},
] as const;
export type Receipt = {decision:Decision; reason:string; notes:string; timestamp:string; fingerprint:string};
export type Session = {fingerprint:string|null; systemReviewed:boolean; inspected:string[]; evidenceReviewed:boolean; reviewReviewed:boolean; results:Record<string,HumanResult>; receipt:Receipt|null};
export function emptySession(fingerprint:string|null=null):Session {
  return {fingerprint,systemReviewed:false,inspected:[],evidenceReviewed:false,reviewReviewed:false,results:Object.fromEntries(humanCases.map(c=>[c.id,'NOT TESTED'])),receipt:null};
}
// Exclude capture/latency timestamps and volatile Git counts, retain material evidence.
export function evidenceKey(s:SystemHealth):string {
  return JSON.stringify({phases:s.phases, gates:s.gates, evidence:s.evidence, runtime:s.runtime,
    rag:s.rag, protected:s.protected_assets, warnings:s.warnings, governance:s.governance});
}
export function gateEvidenceReady(s:SystemHealth):boolean {
  return Array.from({length:14},(_,i)=>`R3.${i+1}`).every(id=>{
    const gate=s.gates.find(g=>g.id===id);
    return gate?.status==='PASS' && gate.evidence.length>0 && gate.evidence.every(ref=>{
      const e=s.evidence.find(e=>e.id===ref);
      return e?.status==='VERIFIED_ARTIFACT' && !!e.sha256;
    });
  });
}
export function counts(session:Session) {
  const values=humanCases.map(c=>session.results[c.id]??'NOT TESTED');
  return {pass:values.filter(v=>v==='PASS').length,fail:values.filter(v=>v==='FAIL').length,
    blocked:values.filter(v=>v==='BLOCKED').length,untested:values.filter(v=>v==='NOT TESTED').length};
}
export function workflow(session:Session) {
  const system=session.systemReviewed;
  const inspected=Array.from({length:14},(_,i)=>`R3.${i+1}`).filter(id=>session.inspected.includes(id)).length;
  const evidence=system&&inspected===14&&session.evidenceReviewed;
  const missingTests=humanCases.filter(c=>!(['PASS','FAIL','BLOCKED'] as string[]).includes(session.results[c.id]));
  const tested=evidence&&missingTests.length===0;
  const reviewed=tested&&session.reviewReviewed;
  const complete:Record<Stage,boolean>={System:system,Evidence:evidence,Test:tested,Review:reviewed,Decision:reviewed&&!!session.receipt};
  const available:Record<Stage,boolean>={System:true,Evidence:system,Test:evidence,Review:tested,Decision:reviewed};
  const missing:string[]=[];
  if(!system)missing.push('Acknowledge the System summary and limitations.');
  if(inspected<14)missing.push(`Inspect all 14 R3 evidence sources (${inspected}/14 inspected).`);
  if(!session.evidenceReviewed)missing.push('Acknowledge all inspected evidence sources and their limitations.');
  if(missingTests.length)missing.push(`Record an explicit PASS, FAIL or BLOCKED for ${missingTests.length} human test case(s): ${missingTests.map(c=>c.title).join('; ')}.`);
  if(!session.reviewReviewed)missing.push('Acknowledge the Review of evidence, human results and all unresolved limitations.');
  const systemMissing=system?[]:['Acknowledge the System summary and limitations.'];
  const evidenceMissing=[...systemMissing,...(inspected<14?[`Inspect all 14 R3 evidence sources (${inspected}/14 inspected).`]:[]),...(!session.evidenceReviewed?['Acknowledge all inspected evidence sources and their limitations.']:[])];
  const testMissing=[...evidenceMissing,...(missingTests.length?[`Record an explicit PASS, FAIL or BLOCKED for ${missingTests.length} human test case(s): ${missingTests.map(c=>c.title).join('; ')}.`]:[])];
  const blockers:Record<Stage,string[]>={System:[],Evidence:systemMissing,Test:evidenceMissing,Review:testMissing,Decision:[...testMissing,...(!session.reviewReviewed?['Acknowledge the Review of evidence, human results and all unresolved limitations.']:[])]};
  const next=stages.find(s=>!complete[s])??'Decision';
  return {available,complete,next,missing,blockers,inspected,missingTests};
}
export function canApprove(s:SystemHealth, session:Session):boolean {
  return session.fingerprint===evidenceKey(s) && workflow(session).available.Decision &&
    gateEvidenceReady(s) && counts(session).pass===humanCases.length &&
    Array.from({length:14},(_,i)=>`R3.${i+1}`).every(id=>session.inspected.includes(id));
}
export function limitations(s:SystemHealth):string[] {
  return [...new Set([...s.warnings,
    ...s.protected_assets.filter(a=>a.status!=='UNCHANGED').map(a=>`${a.path}: ${a.status}. Current protected-file integrity is not established; do not repair or recreate sidecars from this UI.`),
    ...(s.runtime.current_status==='NOT_VERIFIED'?['Current runtime identity is NOT VERIFIED. A live API or historical receipt is insufficient.']:[])])];
}
