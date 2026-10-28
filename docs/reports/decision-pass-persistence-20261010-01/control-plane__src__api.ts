import {parseSnapshot,PendingIntentionSchema,type Snapshot,type Attestation,type PendingIntention} from './schemas';
import {z} from 'zod';

const ModelStatusSchema=z.object({model:z.string(),provider:z.string(),revision:z.number().int(),
  process_id:z.number().int(),consistency_scope:z.literal('CURRENT_PROCESS_ONLY'),
  availability:z.string(),status:z.string(),selection_enabled:z.boolean(),source_build_id:z.string().optional(),
  selection_source:z.string(),last_request:z.record(z.string(),z.unknown()).nullable()});
export type ModelStatus=z.infer<typeof ModelStatusSchema>;
async function runtimeFetch(path:string,options:RequestInit={}){
  const response=await fetch(path,{credentials:'omit',cache:'no-store',redirect:'error',...options});
  if(!response.ok)throw new Error(response.status===403?'Akses ditolak. Periksa token operator.':
    response.status===404&&path.startsWith('/v1/control-plane/model')?'Endpoint kendali model belum tersedia (404). Runtime yang terhubung belum menyediakan API ini; operator perlu memeriksa build layanan.':
    response.status===409?'Konfigurasi berubah atau pemilihan tidak didukung. Muat ulang status.':
    response.status===422?'Pilihan tidak valid atau model tidak tersedia.':`Layanan belum tersedia (${response.status}).`);
  return response.json() as Promise<unknown>;
}
export async function fetchModelStatus(){return ModelStatusSchema.parse(await runtimeFetch('/v1/control-plane/model-status'));}
export async function fetchAvailableModels(token:string){
  if(!token.trim())throw new Error('Token operator diperlukan.');
  return z.object({models:z.array(z.string()),observed_revision:z.number().int()}).parse(
    await runtimeFetch('/v1/control-plane/models',{headers:{'X-Admin-Token':token}}));
}
export async function selectOperatorModel(model:string,revision:number,token:string){
  if(!token.trim())throw new Error('Token operator diperlukan.');
  return ModelStatusSchema.parse(await runtimeFetch('/v1/control-plane/model-selection',{
    method:'POST',headers:{'Content-Type':'application/json','X-Admin-Token':token},
    body:JSON.stringify({model,expected_revision:revision})}));
}
const PublicChatSchema=z.object({session_id:z.string(),response:z.string(),model:z.string(),
  provider_status:z.string(),latency_ms:z.number(),timestamp:z.string(),
  trust:z.object({supports_claim:z.boolean(),confidence:z.number(),risk_level:z.string(),requires_human:z.boolean(),evidence_count:z.number(),evidence_available:z.boolean()}).strict(),
  grounding:z.object({enabled:z.boolean(),grounded:z.boolean(),reason:z.string()}).strict(),
  understanding:z.object({intent:z.string()}).strict(),problem:z.object({goal:z.string().nullable()}).strict(),
  evidence:z.array(z.object({document_id:z.string(),title:z.string(),chunk:z.string(),score:z.number()}).strict())}).strict();
export type PublicChat=z.infer<typeof PublicChatSchema>;
export async function sendUserChat(user_input:string,session_id:string){
  const controller=new AbortController();
  let timeout:ReturnType<typeof setTimeout>|undefined;
  try{
    const deadline=new Promise<never>((_,reject)=>{
      timeout=setTimeout(()=>{
        reject(new Error('Batas waktu 30 detik tercapai. Backend mungkin masih memproses permintaan ini; pembatalan di browser tidak menjamin pembatalan di server. Coba lagi hanya secara manual.'));
        controller.abort(); // Browser abort does not guarantee backend/provider cancellation.
      },30000);
    });
    const result=PublicChatSchema.safeParse(await Promise.race([
      runtimeFetch('/v1/chat',{method:'POST',signal:controller.signal,
        headers:{'Content-Type':'application/json'},body:JSON.stringify({user_input,session_id})}),
      deadline,
    ]));
    if(!result.success)throw new Error('Jawaban tidak sesuai kontrak layanan. Silakan coba kembali.');
    return result.data;
  }finally{if(timeout!==undefined)clearTimeout(timeout);}
}

const InspectionPreviewSchema = z.object({
  scope:z.literal('inspection-preview'),profile:z.literal('NORMAL'),
  source:z.literal('/v2/dev/inspection-preview'),captured_at:z.string().datetime({offset:true}),
  runtime_identity:z.literal('NOT_VERIFIED'),active_process_build:z.literal('NOT_VERIFIED'),
  provider_model_correlation:z.literal('NOT_VERIFIED'),
  inspection_preview:z.object({
    goal:z.string(),understanding:z.string(),intent:z.literal('INSPECT'),target:z.string(),
    status:z.literal('PREVIEW_READY'),root_cause:z.literal('UNKNOWN'),
    discovery:z.array(z.string()),likely_files:z.array(z.string()),
    plan:z.array(z.object({action:z.literal('STATIC_SOURCE_INSPECTION'),step:z.string()})),
    expected_evidence:z.array(z.string()),risk:z.literal('LOW'),
    write_required:z.literal('NO'),runtime_required:z.literal('NO'),
    provider_required:z.literal('NO'),database_required:z.literal('NO'),
    human_decision:z.literal('NOT REQUIRED'),next_step:z.string(),
    requirements_scope:z.literal('PROPOSED_NEXT_STATIC_INSPECTION'),
    goal_resolution_requirements:z.literal('UNKNOWN_PENDING_DISCOVERY'),
    file_evidence:z.literal('CANDIDATES_NOT_INSPECTED'),authorized_operations:z.array(z.never()).length(0),
    boundaries:z.array(z.string()),
  }),
});
export type InspectionPreviewResult = z.infer<typeof InspectionPreviewSchema>;
export async function fetchInspectionPreview(goal:string,adminToken:string,signal?:AbortSignal):Promise<InspectionPreviewResult>{
  if(!adminToken.trim())throw new Error('Admin token required. Preview was not requested.');
  const input=goal.trim();
  if(!input||input.length>4000)throw new Error('Enter a goal of 1–4000 characters.');
  const response=await fetch('/v2/dev/inspection-preview',{method:'POST',credentials:'omit',cache:'no-store',
    redirect:'error',signal,headers:{'Content-Type':'application/json','X-Admin-Token':adminToken},
    body:JSON.stringify({user_input:input})});
  if(!response.ok)throw new Error(response.status===403?'Preview rejected (403). Check authorization and preview scope.':
    response.status===422?'Preview rejected (422). Choose a supported goal; execution requests are unavailable.':
    `Preview unavailable (${response.status}). No test or decision inferred.`);
  const result=InspectionPreviewSchema.parse(await response.json());
  if(result.inspection_preview.goal!==input)throw new Error('Preview goal mismatch. No evidence accepted.');
  return result;
}
export type SnapshotResult={state:Snapshot;latencyMs:number;fetchedAt:string;source:string};
export async function fetchSnapshot(signal?:AbortSignal):Promise<SnapshotResult>{
  const start=performance.now();
  const response=await fetch('/v1/control-plane/snapshot',{method:'GET',credentials:'omit',cache:'no-store',signal});
  if(!response.ok)throw new Error(`Evidence API unavailable (${response.status}). No healthy state inferred.`);
  const state=parseSnapshot(await response.json());
  return {state,latencyMs:Math.round(performance.now()-start),fetchedAt:new Date().toISOString(),source:'/v1/control-plane/snapshot'};
}
export async function submitIntention(state:Attestation):Promise<PendingIntention>{
  const response=await fetch('/v1/control-plane/intention',{method:'POST',credentials:'omit',cache:'no-store',
    headers:{'Content-Type':'application/json'},body:JSON.stringify({scope:state.scope,evidence_version:state.evidence_version})});
  if(!response.ok)throw new Error(`Intention rejected (${response.status}). No authority granted. Do not retry automatically.`);
  const result=PendingIntentionSchema.parse(await response.json());
  if(result.scope!==state.scope||result.evidence_version!==state.evidence_version)throw new Error('Intention context mismatch. No authority inferred.');
  return result;
}


export type EvidencePackage={package_id:string;generated_at:string;read_scope:string;runtime_status:string;pass_allowed:boolean;
  evidence:{id:string;path:string;classification:string;validation_status:string;sha256:string|null;bytes:number|null;reason:string|null;results_path?:string;results_sha256?:string;result_artifacts?:{path:string;sha256:string;bytes:number}[]}[];
  criteria:{id:string;summary:string;status:string;evidence:string[];tests:string[];reason:string|null}[];blockers:{id:string;reason:string}[]};
export type DecisionRecord={decision_id:string;package_id:string;decision:'PASS'|'FAIL'|'HOLD';reviewer_principal:string;authentication:string;
  timestamp:string;notes:string;test_evidence:string[];blockers:{id:string;reason:string}[];record_hash:string};
const DECISION_FIELDS=new Set(['package_id','decision','notes']);
function decisionValidationMessage(detail:unknown):string{
  if(!Array.isArray(detail))return 'Request format was rejected (422). Ask the runtime owner to inspect the sanitized validation detail.';
  const messages=new Set<string>();
  for(const item of detail){
    if(!item||typeof item!=='object')continue;
    const error=item as {loc?:unknown;type?:unknown};
    const location=Array.isArray(error.loc)?error.loc.filter((part):part is string=>typeof part==='string').find(part=>DECISION_FIELDS.has(part)):undefined;
    const field=location?` ${location}`:'';
    const type=typeof error.type==='string'?error.type:'';
    const reason=type==='missing'?' is required.':type==='extra_forbidden'?' is not an accepted field.':
      type==='string_pattern_mismatch'?' has an invalid package ID format.':type==='enum'?' must be PASS, FAIL, or HOLD.':
      type==='string_too_long'?' exceeds the 2,000 character limit.':type==='string_type'?' must be text.':' failed validation.';
    messages.add(`${field}${reason}`.trim());
  }
  return messages.size?`Request format was rejected (422): ${[...messages].join(' ')}`:
    'Request format was rejected (422). Ask the runtime owner to inspect the sanitized validation detail.';
}
async function decisionRequestError(response:Response):Promise<Error>{
  if(response.status===403)return new Error('Access denied (403). Check the operator token in Developer Console.');
  if(response.status===422){
    let detail:unknown;
    try{detail=(await response.json() as {detail?:unknown}).detail;}catch{/* The response body may not be JSON. */}
    return new Error(decisionValidationMessage(detail));
  }
  return new Error(response.status===409?'Evidence package changed or PASS is blocked. Refresh and review the current package.':`Decision was not saved (${response.status}).`);
}
export async function fetchEvidencePackage():Promise<EvidencePackage>{
  const r=await fetch('/v1/control-plane/evidence-package',{credentials:'omit',cache:'no-store',redirect:'error',headers:{'Content-Type':'application/json'}});
  if(!r.ok)throw new Error(`Evidence package unavailable (${r.status}).`);
  const value=await r.json() as EvidencePackage;
  if(!/^evp_sha256_[a-f0-9]{64}$/.test(value.package_id)||!Array.isArray(value.criteria)||value.criteria.length!==15)throw new Error('Evidence package failed structural validation.');
  return value;
}
export async function fetchDecisionRecords(token:string,packageId?:string):Promise<DecisionRecord[]>{
  if(!token.trim())return [];
  const query=packageId?`?package_id=${encodeURIComponent(packageId)}`:'';
  const r=await fetch(`/v1/control-plane/decisions${query}`,{credentials:'omit',cache:'no-store',redirect:'error',headers:{'X-Admin-Token':token,'Content-Type':'application/json'}});
  if(!r.ok)throw new Error(r.status===403?'Decision audit unavailable (403). Check the operator token in Developer Console.':`Decision audit unavailable (${r.status}).`);
  const result=await r.json() as {records:DecisionRecord[];audit_status:string};
  if(result.audit_status!=='VALIDATED_HASH_CHAIN'||!Array.isArray(result.records))throw new Error('Decision audit chain is not verified.');
  return result.records;
}
export async function saveEvidenceDecision(input:{packageId:string;decision:'PASS'|'FAIL'|'HOLD';notes:string;token:string}):Promise<DecisionRecord>{
  const r=await fetch('/v1/control-plane/decisions',{method:'POST',credentials:'omit',cache:'no-store',redirect:'error',
    headers:{'Content-Type':'application/json','X-Admin-Token':input.token},
    body:JSON.stringify({package_id:input.packageId,decision:input.decision,notes:input.notes})});
  if(!r.ok)throw await decisionRequestError(r);
  const record=await r.json() as DecisionRecord;
  if(record.package_id!==input.packageId||record.decision!==input.decision||!record.decision_id||!record.record_hash)throw new Error('Saved decision context mismatch.');
  return record;
}
