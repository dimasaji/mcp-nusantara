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
  const result=PublicChatSchema.safeParse(await runtimeFetch('/v1/chat',{method:'POST',
    headers:{'Content-Type':'application/json'},body:JSON.stringify({user_input,session_id})}));
  if(!result.success)throw new Error('Jawaban tidak sesuai kontrak layanan. Silakan coba kembali.');
  return result.data;
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


export type HumanAcceptanceRecord = {
  record_type: 'HUMAN_ACCEPTANCE_UI_ONLY_NO_AUTHORITY';
  identity_status: 'NOT_VERIFIED';
  decision: 'APPROVE' | 'REJECT' | 'HOLD';
  reason: string;
  notes: string;
  fingerprint: string;
  timestamp: string;
};

function parseHumanAcceptance(value: unknown): HumanAcceptanceRecord | null {
  if (!value || typeof value !== 'object') return null;
  const r = value as Record<string, unknown>;
  if (
    r.record_type !== 'HUMAN_ACCEPTANCE_UI_ONLY_NO_AUTHORITY' ||
    r.identity_status !== 'NOT_VERIFIED' ||
    !['APPROVE', 'REJECT', 'HOLD'].includes(String(r.decision)) ||
    typeof r.reason !== 'string' ||
    typeof r.notes !== 'string' ||
    typeof r.fingerprint !== 'string' ||
    typeof r.timestamp !== 'string'
  ) throw new Error('Invalid human acceptance record; no authority inferred.');
  return r as HumanAcceptanceRecord;
}

export async function saveHumanAcceptance(input: {
  decision: 'APPROVE' | 'REJECT' | 'HOLD';
  reason: string;
  notes: string;
  fingerprint: string;
}): Promise<HumanAcceptanceRecord> {
  const response = await fetch('/v1/control-plane/human-acceptance', {
    method: 'POST',
    credentials: 'omit',
    cache: 'no-store',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
  if (!response.ok) {
    throw new Error(`Decision was not saved (${response.status}). No authority granted.`);
  }
  const record = parseHumanAcceptance(await response.json());
  if (!record || record.fingerprint !== input.fingerprint ||
      record.decision !== input.decision) {
    throw new Error('Saved decision context mismatch.');
  }
  return record;
}

export async function fetchHumanAcceptance(
  fingerprint: string,
): Promise<HumanAcceptanceRecord | null> {
  const response = await fetch('/v1/control-plane/human-acceptance/read', {
    method: 'POST',
    credentials: 'omit',
    cache: 'no-store',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ fingerprint }),
  });
  if (!response.ok) {
    throw new Error(`Could not read saved decision (${response.status}).`);
  }
  const result = await response.json() as {
    record: unknown;
    identity_status: string;
  };
  if (result.identity_status !== 'NOT_VERIFIED') {
    throw new Error('Identity status mismatch.');
  }
  const record = parseHumanAcceptance(result.record);
  if (record && record.fingerprint !== fingerprint) {
    throw new Error('Saved decision fingerprint mismatch.');
  }
  return record;
}
