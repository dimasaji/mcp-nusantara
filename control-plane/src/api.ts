import {parseSnapshot,PendingIntentionSchema,type Snapshot,type Attestation,type PendingIntention} from './schemas';
import {z} from 'zod';

const ModelStatusSchema=z.object({model:z.string(),provider:z.string(),revision:z.number().int(),
  process_id:z.number().int(),consistency_scope:z.literal('CURRENT_PROCESS_ONLY'),
  availability:z.string(),status:z.string(),selection_enabled:z.boolean(),source_build_id:z.string().optional(),
  selectable_providers:z.array(z.enum(['ollama','openrouter'])).optional(),
  selection_source:z.string(),checked_at:z.string().optional(),verified_at:z.string().nullable().optional(),
  verification_scope:z.string().optional(),last_request:z.record(z.string(),z.unknown()).nullable()});
export type ModelStatus=z.infer<typeof ModelStatusSchema>;
async function runtimeRequest(path:string,options:RequestInit={}):Promise<Response>{
  let response:Response;
  try{response=await fetch(path,{credentials:'omit',cache:'no-store',redirect:'error',...options});}
  catch{throw new Error('Koneksi gagal. Backend tidak terhubung; periksa layanan lokal lalu muat ulang halaman.');}
  return response;
}
async function runtimeFetch(path:string,options:RequestInit={}){
  const response=await runtimeRequest(path,options);
  if(response.status===409&&path.endsWith('/execution-context')){
    const body=await response.json().catch(()=>null) as {detail?:{reason?:string}}|null;
    throw new Error(`Rencana eksekusi belum siap. ${body?.detail?.reason??'Periksa kelengkapan rencana dan staging di backend.'}`);
  }
  if(!response.ok){
    if(path.endsWith('/models')&&response.status===503){
      const body=await response.json().catch(()=>null) as {detail?:string}|null;
      throw new Error(body?.detail==='MODEL_INVENTORY_UNAVAILABLE'?'Ollama lokal tidak dapat dihubungi untuk membaca /api/tags. Periksa Ollama lalu coba lagi.':
        body?.detail==='MODEL_PRICING_CATALOG_UNAVAILABLE'?'Katalog model OpenRouter lokal tidak tersedia.':'Inventaris model runtime belum tersedia.');
    }
    throw new Error(response.status===403?'Akses ditolak. Periksa token operator.':
    response.status===404&&path.startsWith('/v1/control-plane/model')?'Endpoint kendali model belum tersedia (404). Runtime yang terhubung belum menyediakan API ini; operator perlu memeriksa build layanan.':
    response.status===409&&path.endsWith('/execution-context')?'Rencana eksekusi belum siap. Belum ada tindakan yang dapat dijalankan.':
    response.status===409&&path.endsWith('/execute-reviewed')?'Eksekusi ditolak oleh governance. Periksa evidence, keputusan, dan History.':
    response.status===409?'Konfigurasi berubah atau pemilihan tidak didukung. Muat ulang status.':
    response.status===422?'Pilihan tidak valid atau model tidak tersedia.':`Layanan belum tersedia (${response.status}).`);
  }
  return response.json() as Promise<unknown>;
}
export async function fetchModelStatus(){return ModelStatusSchema.parse(await runtimeFetch('/v1/control-plane/model-status'));}
export async function fetchRuntimeHealth(){
  const path='/health';
  let response:Response;
  try{response=await runtimeRequest(path);}
  catch{throw new Error('GET /health gagal: koneksi ke Backend tidak berhasil.');}
  if(!response.ok)throw new Error(`GET /health gagal (HTTP ${response.status}). Backend belum memberikan health yang valid.`);
  const payload=await response.json().catch(()=>null);
  const parsed=z.object({status:z.string(),service:z.string().optional(),version:z.string(),build_id:z.string().optional()}).safeParse(payload);
  if(!parsed.success)throw new Error(`GET /health gagal (HTTP ${response.status}): respons Backend tidak sesuai format health.`);
  return {...parsed.data,httpStatus:response.status};
}
const RuntimeReadinessSchema=z.object({status:z.enum(['BLOCKED','PREREQUISITES_READY','CONFIGURATION_CHANGED']),
  provider:z.string(),model:z.string(),configuration_revision:z.number().int(),process_id:z.number().int(),
  build_id:z.string(),checked_at:z.string(),checks:z.record(z.string(),z.object({status:z.string()})),
  operational_acceptance:z.literal('NOT_VERIFIED')});
export async function fetchRuntimeReadiness(token:string){
  if(!token.trim())throw new Error('Token operator diperlukan untuk memeriksa kesiapan.');
  return RuntimeReadinessSchema.parse(await runtimeFetch('/v1/runtime/readiness',{
    headers:{'X-Admin-Token':token},signal:AbortSignal.timeout(20000)}));
}
export type CostSummary={status:'AVAILABLE'|'UNAVAILABLE';source:string;reason:string;checked_at:string;
  currency?:string;period?:{scope:string;start:string|null;end:string|null};actual_usd?:string;
  reserved_usd?:string;remaining_budget_usd?:string;budget_usd?:string;per_request_cap_usd?:string;
  history?:{request_id:string;status:string;reserved_cents:number;actual_cents:number|null;created_at:string}[]};
export async function fetchCostSummary(token:string):Promise<CostSummary>{
  if(!token.trim())throw new Error('Token operator diperlukan untuk membaca biaya.');
  return runtimeFetch('/v1/control-plane/cost-summary',{headers:{'X-Admin-Token':token}}) as Promise<CostSummary>;
}
export type OperationsSummary={scope:string;source:string;pending_work:number|null;pending_review:number|null;reason:string|null;checked_at:string;
  tasks:{id:string;objective:string;status:string;updated_at:string;source:string}[]};
export async function fetchOperationsSummary(token:string):Promise<OperationsSummary>{
  if(!token.trim())throw new Error('Token operator diperlukan untuk membaca pekerjaan.');
  return runtimeFetch('/v1/control-plane/operations-summary',{headers:{'X-Admin-Token':token}}) as Promise<OperationsSummary>;
}
export type KnowledgePipelineRun={run_id:string;filename:string;source_sha256:string;status:string;reason:string|null;document_id:string|null;created_at:string;source_path:string|null};
export type KnowledgeDocument={document_id:string;title:string;chunks_count:number;status:string;source_verification:string;verification_reason?:string|null;source_sha256?:string|null;updated_at:string;review_status?:string};
export type KnowledgePipelineStatus={source:string;database:string;documents_indexed:number;pipeline_ready_documents:number;documents?:KnowledgeDocument[];watch:{enabled:boolean;folder:string;updated_at:string};runs:KnowledgePipelineRun[];checked_at:string};
export async function fetchKnowledgePipelineStatus(token:string):Promise<KnowledgePipelineStatus>{
  if(!token.trim())throw new Error('Token operator diperlukan untuk melihat History knowledge.');
  return runtimeFetch('/v1/knowledge/pipeline/status',{headers:{'X-Admin-Token':token}}) as Promise<KnowledgePipelineStatus>;
}
export async function uploadKnowledgeDocument(file:File,token:string):Promise<KnowledgePipelineRun>{
  if(!token.trim())throw new Error('Token operator diperlukan untuk menambahkan dokumen.');
  const bytes=await file.arrayBuffer();
  let response:Response;
  try{response=await fetch('/v1/knowledge/pipeline/documents',{method:'POST',credentials:'omit',cache:'no-store',redirect:'error',
    headers:{'Content-Type':'application/octet-stream','X-Admin-Token':token,'X-Document-Name':encodeURIComponent(file.name)},body:bytes});}
  catch{throw new Error('Koneksi upload terputus. File tetap dipilih. Periksa layanan lokal, lalu Coba Lagi.');}
  if(!response.ok){
    const body=await response.json().catch(()=>null) as {detail?:unknown}|null;
    const detail=typeof body?.detail==='string'?body.detail:'';
    throw new Error((response.status===401||response.status===403)?
      detail.toLowerCase().includes('out_of_scope')?'Akun operator tidak memiliki izin upload. Hubungi administrator.':
        'Token operator ditolak. Masukkan token yang benar dan Verifikasi akses, lalu Coba Lagi.':
      response.status===413?'File melebihi batas 20 MB. Pilih file yang lebih kecil.':
      response.status===422&&detail==='DOCUMENT_EMPTY'?'File kosong. Pilih dokumen yang memiliki isi.':
      response.status===415?'Format dokumen tidak didukung. Pilih PDF, DOCX, TXT, Markdown, atau HTML.':
      response.status===504?'Batas waktu pemrosesan tercapai. Periksa History sebelum mencoba lagi; server mungkin masih memproses file.':
      response.status>=500?'Layanan pemrosesan dokumen belum tersedia. File tetap dipilih; periksa backend lalu Coba Lagi.':
      `Upload ditolak (${response.status}). Periksa format dokumen dan akses operator, lalu Coba Lagi.`);
  }
  return await response.json() as KnowledgePipelineRun;
}
export async function setKnowledgeWatch(enabled:boolean,token:string){
  if(!token.trim())throw new Error('Token operator diperlukan untuk mengubah pemantauan folder.');
  return runtimeFetch(`/v1/knowledge/pipeline/watch?enabled=${enabled}`,{method:'POST',headers:{'X-Admin-Token':token}}) as Promise<{enabled:boolean;folder:string;updated_at:string}>;
}
export async function retryKnowledgeDocument(runId:string,token:string):Promise<KnowledgePipelineRun>{
  if(!token.trim())throw new Error('Token operator diperlukan untuk mencoba lagi.');
  return runtimeFetch(`/v1/knowledge/pipeline/runs/${encodeURIComponent(runId)}/retry`,{method:'POST',headers:{'X-Admin-Token':token}}) as Promise<KnowledgePipelineRun>;
}
export async function fetchAvailableModels(token:string,provider?:'ollama'|'openrouter'){
  if(!token.trim())throw new Error('Token operator diperlukan.');
  return z.object({models:z.array(z.string()),provider:z.enum(['ollama','openrouter']).optional(),observed_revision:z.number().int()}).parse(
    await runtimeFetch(`/v1/control-plane/models${provider?`?provider=${provider}`:''}`,{headers:{'X-Admin-Token':token}}));
}
export async function selectOperatorModel(model:string,revision:number,token:string,provider?:'ollama'|'openrouter'){
  if(!token.trim())throw new Error('Token operator diperlukan.');
  return ModelStatusSchema.parse(await runtimeFetch('/v1/control-plane/model-selection',{
    method:'POST',headers:{'Content-Type':'application/json','X-Admin-Token':token},
    body:JSON.stringify({model,...(provider?{provider}:{}),expected_revision:revision})}));
}
const PublicChatSchema=z.object({session_id:z.string(),response:z.string(),model:z.string(),
  provider_status:z.string(),latency_ms:z.number(),timestamp:z.string(),
  trust:z.object({supports_claim:z.boolean(),confidence:z.number(),risk_level:z.string(),requires_human:z.boolean(),evidence_count:z.number(),evidence_available:z.boolean()}).strict(),
  grounding:z.object({enabled:z.boolean(),grounded:z.boolean(),reason:z.string()}).strict(),
  understanding:z.object({intent:z.string()}).strict(),problem:z.object({goal:z.string().nullable()}).strict(),
  evidence:z.array(z.object({document_id:z.string(),title:z.string(),chunk:z.string().transform(()=>''),score:z.number(),pages:z.array(z.number().int().positive()).optional(),block_ids:z.array(z.string()).optional()}).strict())}).strict();
export type PublicChat=z.infer<typeof PublicChatSchema>;
export async function fetchChatHistory(session:string,token=''){
  return z.object({session_id:z.string(),turns:z.array(z.object({request_id:z.string().regex(/^[a-f0-9]{32}$/).optional(),retry_of:z.string().regex(/^[a-f0-9]{32}$/).optional(),question:z.string(),answer:PublicChatSchema.nullable(),error:z.string().nullable(),status:z.enum(['SUCCEEDED','FAILED','PROCESSING','UNKNOWN']),timestamp:z.string()}))}).parse(
    await runtimeFetch('/v1/chat/history',{headers:{'X-Chat-Session':session,...(token?{'X-Admin-Token':token}:{})}}));
}
export class ChatSendError extends Error{
  constructor(message:string,readonly status:number,readonly retrySafe:boolean){super(message);this.name='ChatSendError';}
}
export type ChatOptions={signal?:AbortSignal;onDelta?:(text:string)=>void;documentIds?:string[];token?:string;sopVersion?:string;sopCase?:string};
export async function sendUserChat(user_input:string,session_id:string,request_id:string=crypto.randomUUID().replaceAll('-',''),retry_of?:string,timeoutMs=90000,options:ChatOptions={}){
  const controller=new AbortController();
  const abort=()=>controller.abort();
  options.signal?.addEventListener('abort',abort,{once:true});
  if(options.signal?.aborted)controller.abort();
  let timeout:ReturnType<typeof setTimeout>|undefined;
  try{
    const deadline=new Promise<never>((_,reject)=>{
      timeout=setTimeout(()=>{
        // Settle the deadline before abort can synchronously reject fetch.
        reject(new ChatSendError(`Batas waktu ${Math.floor(timeoutMs/1000)} detik tercapai. Backend mungkin masih memproses; pembatalan browser tidak menjamin pembatalan di server. Periksa History atau gunakan ID permintaan yang sama agar server tidak mengirim ulang.`,0,false));
        controller.abort();
      },timeoutMs);
    });
    const response=await Promise.race([fetch('/v1/chat',{method:'POST',signal:controller.signal,credentials:'omit',cache:'no-store',redirect:'error',
        headers:{'Content-Type':'application/json',...(options.token&&options.documentIds?.length?{'X-Admin-Token':options.token}:{})},body:JSON.stringify({user_input,session_id,request_id,...(retry_of?{retry_of}:{}),...(options.onDelta?{stream:true}:{}),...(options.documentIds?.length?{document_ids:options.documentIds}:{}),...(options.sopVersion?{sop_version:options.sopVersion,sop_case:options.sopCase}:{})})}),deadline]);
    if(!response.ok){
      let body:{detail?:unknown}|null=null;
      try{body=await response.json() as {detail?:unknown};}catch{/* HTTP status remains authoritative when the body is unreadable. */}
      const detail=typeof body?.detail==='string'?body.detail:'';
      const message=response.status===409&&detail==='CHAT_REQUEST_IN_PROGRESS'?'Permintaan sebelumnya masih diproses. Muat ulang History; request tidak dikirim ulang.':
        response.status===409&&detail.startsWith('SOP belum aktif.')?detail:
        response.status===409&&detail.startsWith('Masalah pembacaan SOP:')?detail:
        response.status===409&&detail==='CHAT_REQUEST_OUTCOME_UNKNOWN'?'Hasil permintaan sebelumnya belum dapat dipastikan setelah proses berhenti. Request tidak dikirim ulang.':
        response.status===409&&detail==='CHAT_RETRY_NOT_SAFE'?'Hasil provider belum pasti; percobaan baru ditahan agar tidak menggandakan biaya.':
          response.status===409&&options.sopVersion&&detail.startsWith('Konteks SOP tidak muat utuh')?detail:
        response.status===504?'Batas waktu pemrosesan tercapai. Periksa History sebelum mencoba lagi.':
        response.status===503&&detail==='RETRIEVAL_UNAVAILABLE'?'Pencarian dokumen gagal. Sumber belum dapat diperiksa; coba lagi setelah layanan Knowledge pulih.':
        response.status===503&&response.headers?.get('X-Chat-Retry-Safe')==='pre-provider'?'Model belum tersedia. Periksa Ollama, lalu kirim ulang pertanyaan setelah pulih.':
        response.status>=500?`Layanan Chat gagal (${response.status}). Request ini tidak akan dikirim ulang otomatis.`:
        `Pertanyaan belum berhasil diproses (${response.status}).`;
      throw new ChatSendError(message,response.status,[503,504].includes(response.status)&&response.headers?.get('X-Chat-Retry-Safe')==='pre-provider');
    }
    async function readAnswer():Promise<unknown>{
      if(!response.headers?.get('content-type')?.includes('application/x-ndjson'))return response.json();
      if(!response.body)throw new Error('Aliran jawaban tidak tersedia.');
      const reader=response.body.getReader(),decoder=new TextDecoder();let buffer='';
      try{
        while(true){
          const {done,value}=await reader.read();buffer+=decoder.decode(value,{stream:!done});
          const lines=buffer.split('\n');buffer=lines.pop()??'';
          for(const line of lines){
            if(!line.trim())continue;
            const event=JSON.parse(line) as {type:string;text?:string;answer?:unknown;status?:number;retry_safe?:boolean;message?:string};
            // Only the final projection is authorized for display. Ignore raw
            // deltas even from an older backend while P0 buffering is deployed.
            if(event.type==='error')throw new ChatSendError(event.message??'Chat gagal.',event.status??500,event.retry_safe===true);
            if(event.type==='final')return event.answer;
          }
          if(done)throw new Error('Aliran jawaban terputus sebelum selesai. Periksa History.');
        }
      }finally{await reader.cancel().catch(()=>{});reader.releaseLock();}
    }
    const result=PublicChatSchema.safeParse(await Promise.race([readAnswer(),deadline]));
    if(!result.success)throw new Error('Jawaban tidak sesuai kontrak layanan. Silakan coba kembali.');
      if(!result.data.response.trim())throw new Error('Model tidak menghasilkan jawaban. Sumber dokumen tidak dapat menggantikan jawaban; periksa status model lalu coba kembali.');
    return result.data;
  }catch(error){if(controller.signal.aborted&&options.signal?.aborted)throw new ChatSendError('Permintaan dihentikan. Jawaban sementara tidak disimpan sebagai jawaban final.',0,false);throw error;}
  finally{if(timeout!==undefined)clearTimeout(timeout);options.signal?.removeEventListener('abort',abort);}
}

const InspectionPreviewSchema = z.object({
  scope:z.literal('inspection-preview'),profile:z.literal('NORMAL'),
  source:z.literal('/v1/dev/inspection-preview'),captured_at:z.string().datetime({offset:true}),
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
  const response=await fetch('/v1/dev/inspection-preview',{method:'POST',credentials:'omit',cache:'no-store',
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
export type PlanBinding={plan_id:string;version:string;action:string};
export type DecisionRecord={plan_binding?:PlanBinding;decision_id:string;package_id:string;decision:'PASS'|'FAIL'|'HOLD';reviewer_principal:string;authentication:string;
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
  if(response.status===409){
    let detail:unknown;
    try{detail=(await response.json() as {detail?:unknown}).detail;}catch{/* Keep a safe status-only explanation. */}
    if(typeof detail==='string'&&detail.startsWith('EVIDENCE_PACKAGE_CHANGED'))
      return new Error('The evidence package changed. Refresh the package and review it again before deciding.');
    if(detail&&typeof detail==='object'&&(detail as {code?:unknown}).code==='PASS_BLOCKED'){
      const blockers=(detail as {blockers?:unknown}).blockers;
      const reasons=Array.isArray(blockers)?blockers.map(item=>{
        if(!item||typeof item!=='object')return '';
        const blocker=item as {id?:unknown;reason?:unknown};
        return `${typeof blocker.id==='string'?blocker.id:'Evidence'}: ${typeof blocker.reason==='string'?blocker.reason:'verification is incomplete'}`;
      }).filter(Boolean):[];
      return new Error(reasons.length?`PASS blocked — ${reasons.join('; ')}`:'PASS is blocked because required evidence is incomplete.');
    }
    return new Error('The server rejected this decision (409). Refresh the package and review the current evidence.');
  }
  return new Error(`Decision was not saved (${response.status}).`);
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
export async function saveEvidenceDecision(input:{packageId:string;decision:'PASS'|'FAIL'|'HOLD';notes:string;token:string;planBinding?:PlanBinding}):Promise<DecisionRecord>{
  const r=await fetch('/v1/control-plane/decisions',{method:'POST',credentials:'omit',cache:'no-store',redirect:'error',
    headers:{'Content-Type':'application/json','X-Admin-Token':input.token},
    body:JSON.stringify({package_id:input.packageId,decision:input.decision,notes:input.notes,...(input.planBinding?{plan_binding:input.planBinding}:{})})});
  if(!r.ok)throw await decisionRequestError(r);
  const record=await r.json() as DecisionRecord;
  if(record.package_id!==input.packageId||record.decision!==input.decision||
     !/^dec_[a-f0-9]{32}$/.test(record.decision_id)||! /^[a-f0-9]{64}$/.test(record.record_hash))
    throw new Error('Server response did not contain a valid saved decision receipt.');
  return record;
}


const WorkApprovalWorkflowSchema=z.object({version:z.literal('nusantara.controlled-work.v1'),scope:z.literal('CONTROLLED_FILE_WRITE'),source:z.string(),
 approval_validity_seconds:z.number().int().positive().max(86400),approval_executes_work:z.literal(false),
 steps:z.array(z.object({id:z.enum(['PREPARE','VERIFY','DECIDE','AUTHORIZE','EXECUTE','AUDIT']),label:z.string(),actor:z.string(),description:z.string()}).strict()).length(6),
 decisions:z.array(z.object({code:z.enum(['PASS','FAIL','HOLD']),label:z.string(),description:z.string()}).strict()).length(3)}).strict().superRefine((value,ctx)=>{
 if(value.steps.map(step=>step.id).join(',')!=='PREPARE,VERIFY,DECIDE,AUTHORIZE,EXECUTE,AUDIT')ctx.addIssue({code:'custom',path:['steps'],message:'Urutan alur persetujuan tidak didukung.'});
 if(value.decisions.map(decision=>decision.code).sort().join(',')!=='FAIL,HOLD,PASS')ctx.addIssue({code:'custom',path:['decisions'],message:'Pilihan keputusan tidak lengkap.'});
});
export type WorkApprovalWorkflow=z.infer<typeof WorkApprovalWorkflowSchema>;
export type ExecutionContext={workflow?:WorkApprovalWorkflow;plan_origin?:{kind:'DEVELOPER_OPERATION'|'UNKNOWN';actor_identity:'NOT_RECORDED'};change_id:string;expected_change:string;target_files:string[];operation:string;plan_binding:PlanBinding;objective:string;risk:string;tests_required:string[];rollback:string;checked_at:string;source:string;completed?:boolean;completed_at?:string|null};
export type ExecutionHistory={decisions:DecisionRecord[];executions:{timestamp:string;change_id:string;package_id:string|null;decision_id:string|null;result:string;files_changed:string[];reason:string|null}[];decision_audit:string;execution_audit:string};
export async function fetchExecutionContext(token:string):Promise<ExecutionContext>{
 const context=await runtimeFetch('/v1/control-plane/execution-context',{headers:{'X-Admin-Token':token}}) as ExecutionContext;
 if(context.workflow!==undefined)context.workflow=WorkApprovalWorkflowSchema.parse(context.workflow);
 return context;
}
export async function fetchExecutionHistory(token:string):Promise<ExecutionHistory>{
 const result=await runtimeFetch('/v1/control-plane/history',{headers:{'X-Admin-Token':token}}) as ExecutionHistory;
 if(result.decision_audit!=='VALIDATED_HASH_CHAIN'||!Array.isArray(result.decisions)||!Array.isArray(result.executions))throw new Error('History belum dapat dipercaya: validasi audit backend tidak lengkap.');
 return result;
}
export async function executeReviewedAction(token:string,packageId:string,decisionId:string){
 return runtimeFetch('/v1/control-plane/execute-reviewed',{method:'POST',headers:{'Content-Type':'application/json','X-Admin-Token':token},
 body:JSON.stringify({package_id:packageId,decision_id:decisionId})}) as Promise<{status:string;files_changed:string[]}>;
}

