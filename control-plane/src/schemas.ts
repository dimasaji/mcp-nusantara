import {z} from 'zod';
const status=z.string().min(1);
const refs=z.array(z.string());
export const EvidenceReferenceSchema=z.object({id:z.string(),reference:z.string(),sha256:z.string().nullable(),status});
export const PhaseStateSchema=z.object({id:z.string(),name:z.string(),status,evidence:refs,kind:z.enum(['EXISTING','PROPOSED'])});
export const ContractStateSchema=z.object({id:z.string(),status,evidence:refs});
export const GateStateSchema=z.object({id:z.string(),status,evidence:refs});
export const RuntimeIdentitySchema=z.object({configured_model:z.string().nullable(),effective_model:z.string().nullable(),selected_provider:z.string().nullable(),actual_model:z.string().nullable(),build_id:z.string().nullable(),process_id:z.number().nullable(),identity_status:z.string().nullable(),timestamp:z.string().nullable().optional(),scope:z.string(),current_status:status,evidence:refs});
export const RAGProfileSchema=z.object({profile_id:z.string(),profile_version:z.number(),invocation_id:z.string(),timestamp:z.string(),consumer:z.string(),correlation:z.object({request_id:z.string(),session_id:z.string(),execution_id:z.string()}),retrieval_strategy:z.string(),effective_values:z.object({top_k:z.number(),candidate_count:z.number(),semantic_weight:z.number(),lexical_weight:z.number(),rerank_requested:z.boolean(),rerank_enabled:z.boolean(),actual_reranker:z.string(),embedding_identity:z.record(z.string(),z.unknown()),knowledge_source:z.record(z.string(),z.unknown())}).passthrough(),thresholds:z.record(z.string(),z.unknown()),reranker_identity:z.record(z.string(),z.unknown()),provenance:z.record(z.string(),z.record(z.string(),z.unknown())),execution_outcome:z.record(z.string(),z.unknown())}).passthrough();
export const VerificationResultSchema=z.object({id:z.string(),tests:z.number().optional(),failures:z.number().optional(),errors:z.number().optional(),skipped:z.number().optional(),status,evidence:refs});
export const WorktreeStateSchema=z.object({status,branch:z.string().optional(),head:z.string().optional(),tracked:z.number().optional(),untracked:z.number().optional(),staged:z.number().optional(),files:z.array(z.object({path:z.string(),state:z.string(),ownership:status}))});
export const GovernanceStateSchema=z.object({read_only:z.literal(true),commit:status,push:status,acceptance:z.object({R2:status,R3:status}),scope:z.string(),rollback:z.string(),r3_integrity:z.record(z.string(),z.unknown()),evidence:refs});
export const SystemHealthSchema=z.object({schema_version:z.literal(1),timestamp:z.string(),status,system:z.string(),current_phase:z.string(),phases:z.array(PhaseStateSchema),contract:ContractStateSchema,gates:z.array(GateStateSchema),evidence:z.array(EvidenceReferenceSchema),verification:z.array(VerificationResultSchema),runtime:RuntimeIdentitySchema,rag:z.object({status,profile:RAGProfileSchema.nullable(),evidence:refs}),worktree:WorktreeStateSchema,protected_assets:z.array(z.object({path:z.string(),sha256:z.string().optional(),status,evidence:refs})),warnings:z.array(z.string()),blockers:z.array(z.string()),governance:GovernanceStateSchema});
export type PhaseState=z.infer<typeof PhaseStateSchema>; export type ContractState=z.infer<typeof ContractStateSchema>; export type GateState=z.infer<typeof GateStateSchema>; export type EvidenceReference=z.infer<typeof EvidenceReferenceSchema>; export type RuntimeIdentity=z.infer<typeof RuntimeIdentitySchema>; export type RAGProfile=z.infer<typeof RAGProfileSchema>; export type VerificationResult=z.infer<typeof VerificationResultSchema>; export type WorktreeState=z.infer<typeof WorktreeStateSchema>; export type GovernanceState=z.infer<typeof GovernanceStateSchema>; export type SystemHealth=z.infer<typeof SystemHealthSchema>;

const digest=z.string().regex(/^[a-f0-9]{64}$/);
export const AttestationSchema=z.object({
  projection_contract:z.literal('ATTESTATION_FOUNDATION_V1'),
  evidence_id:z.literal('r2-a9-auth-process'),evidence_type:z.literal('SCOPED_IN_PROCESS'),
  source:z.string(),scope:z.literal('R2-A8:ATTESTATION:ONE_GENERATION'),created_at:z.string().datetime({offset:true}),
  status:z.literal('NOT_VERIFIED'),evidence_version:digest,live_actions:z.literal('LOCKED'),
  operator_policy:z.enum(['NOT_PROVISIONED','EXPLICIT_LOCAL_POLICY']),
  binding:z.object({scope:z.literal('R2-A8:ATTESTATION:ONE_GENERATION'),target:z.literal('127.0.0.1:8000'),
    pid:z.number().int().positive(),process_start:z.number().positive(),runtime_instance:z.string().min(1),
    source_snapshot:z.string().min(1),scoped_loaded_code:z.string().min(1),configuration_digest:digest,
    endpoint:z.object({origin:z.string(),connection_origin:z.string()}).strict(),profile:z.literal('ATTESTATION'),
    active_process_build:z.literal('NOT_DIRECTLY_VERIFIED'),runtime_identity:z.literal('NOT_VERIFIED')}).strict(),
  reviews:z.array(z.object({review_id:z.string(),state:z.enum(['PENDING','APPROVED','REJECTED','HOLD','ARMED','EXECUTING','COMPLETED','ABORTED']),expires_at:z.string().datetime({offset:true})}).strict()).max(32),
  provider_receipt:z.object({request_id:z.string(),invocation_id:z.string().nullable(),runtime_instance_id:z.string(),pid:z.number(),
    source_snapshot:z.string(),scoped_loaded_code:z.string(),provider_id:z.string(),
    provider_endpoint:z.object({origin:z.string(),connection_origin:z.string()}).strict(),actual_model:z.string().nullable(),
    started_at:z.string(),completed_at:z.string(),response_observed:z.boolean(),application_response_sent:z.boolean(),
    dispatch_count:z.number(),outcome:z.string(),external_client_observed:z.boolean(),full_application_build_verified:z.literal(false)}).strict().nullable(),
}).strict();
export type Attestation=z.infer<typeof AttestationSchema>;
export type Snapshot=SystemHealth|Attestation;
export function isAttestation(value:Snapshot):value is Attestation {return 'projection_contract' in value;}
export function parseSnapshot(value:unknown):Snapshot {
  if(typeof value==='object'&&value!==null&&('projection_contract' in value||'evidence_type' in value))return AttestationSchema.parse(value);
  return SystemHealthSchema.parse(value);
}
export const PendingIntentionSchema=z.object({review_id:z.string(),scope:z.literal('R2-A8:ATTESTATION:ONE_GENERATION'),
  evidence_version:digest,state:z.literal('PENDING'),expires_at:z.string().datetime({offset:true})}).strict();
export type PendingIntention=z.infer<typeof PendingIntentionSchema>;
