"""Compose trusted local document/SOP capabilities, without starting a new model."""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.approval import ApprovalQueue, AuditTrail
from app.governance.tools import Decision, GovernedToolRegistry, ToolClass, default_tool_policy

from .runtime import SkillDefinition, SkillRuntime

OPERATOR_PERMISSIONS = frozenset({'knowledge.read', 'knowledge.process'})


class SkillInput(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class DocumentInput(SkillInput):
    document_id: str = Field(min_length=1, max_length=256)


class PrepareInput(DocumentInput):
    version_id: str = Field(pattern=r'^[a-f0-9]{64}$')


class FactsInput(PrepareInput):
    question: str = Field(min_length=1, max_length=20000)


class SearchInput(SkillInput):
    query: str = Field(min_length=1, max_length=20000)
    top_k: int = Field(default=5, ge=1, le=20)


class JobOutput(SkillInput):
    job_id: str
    status: Literal['QUEUED', 'PROCESSING', 'COMPLETE']


class InspectionOutput(SkillInput):
    document_id: str
    version_id: str
    status: str
    review_status: str
    activity_count: int
    page_count: int
    warnings: list[str]


class SearchOutput(SkillInput):
    evidence: list[dict[str, Any]]


class FactsOutput(SkillInput):
    status: Literal['answered', 'unsupported', 'no_evidence', 'not_approved']
    facts: dict[str, Any] | None = None


def prepare_uploaded_source(engine, result, filename):
    if Path(filename).suffix.lower() != '.pdf' or result.get('status') not in {'READY', 'DUPLICATE'}:
        return result
    from app.knowledge.sop_review import SOPReview
    detail = SOPReview(engine).detail(result['document_id'])
    outcome = engine.skills.execute('documents.prepare',
        {'document_id': result['document_id'], 'version_id': detail['version_id']},
        role='operator', permissions=set(OPERATOR_PERMISSIONS), requested_by='document-intake')
    return {**result, 'preparation': asdict(outcome)}


def _policy(spec, role):
    if spec.permission.startswith('knowledge.') and role != 'operator':
        return Decision.DENY, 'operator required'
    if spec.tool_name == 'documents.prepare' and role == 'operator':
        return Decision.ALLOW, 'authorized local unpublished preparation'
    return default_tool_policy(spec, role)


def build_skill_runtime(engine):
    from app.knowledge.document_tools import DocumentReadError, DocumentTools
    from app.knowledge.sop_review import SOPReview
    from app.security.v1_knowledge import V1KnowledgeBoundary

    path = Path(engine.rag._store.db_path).resolve().parent / 'skills-audit.jsonl'
    runtime = SkillRuntime(GovernedToolRegistry(ApprovalQueue(AuditTrail(path)), policy=_policy))

    def prepare(data):
        return DocumentTools(engine, operator=True).process(data.document_id, data.version_id)

    def inspect_document(data):
        tools = DocumentTools(engine, operator=True)
        review = SOPReview(engine)
        for _ in range(3):
            detail = review.detail(data.document_id)
            try:
                status = tools.status(data.document_id, detail['version_id'])
                payload = tools.inspect(data.document_id, detail['version_id']) if status['status'] != 'NOT_PROCESSED' else {}
            except DocumentReadError as exc:
                if str(exc).startswith(('DOCUMENT_VERSION_CHANGED', 'DOCUMENT_VERSION_NOT_FOUND')):
                    continue
                raise
            if review.detail(data.document_id)['version_id'] != detail['version_id']:
                continue
            return {'document_id': data.document_id, 'version_id': detail['version_id'],
                    'status': payload.get('status', status['status']), 'review_status': detail['status'],
                    'activity_count': len(payload.get('activity_rows', [])),
                    'page_count': payload.get('page_count', len(detail['pages'])), 'warnings': payload.get('warnings', [])}
        raise DocumentReadError('DOCUMENT_VERSION_CHANGED')

    def search(data):
        boundary = V1KnowledgeBoundary(engine, operator=True, provider='ollama')
        evidence = boundary.search_knowledge(data.query, top_k=data.top_k)
        boundary.validate_response({'evidence': [{'document_id': e.document_id} for e in evidence]})
        return {'evidence': [e.model_dump(mode='json') for e in evidence]}

    def facts(data):
        from app.knowledge.document_answers import document_answer_facts
        review = SOPReview(engine)
        detail = review._check(data.document_id, data.version_id)
        if detail['status'] != 'Aktif':
            return {'status': 'not_approved'}
        boundary = V1KnowledgeBoundary(engine, operator=True, provider='ollama', document_ids=[data.document_id])
        evidence = boundary.search_knowledge(data.question)
        if not evidence:
            return {'status': 'no_evidence'}
        result = document_answer_facts(data.question, evidence)
        boundary.validate_response({'evidence': [{'document_id': e.document_id} for e in evidence]})
        if review._check(data.document_id, data.version_id)['status'] != 'Aktif':
            return {'status': 'not_approved'}
        return {'status': 'answered' if result else 'unsupported', 'facts': result}

    for name, domain, description, input_model, output_model, permission, handler in [
        ('documents.prepare', 'documents', 'Queue local PDF extraction; never approve.', PrepareInput, JobOutput, 'knowledge.process', prepare),
        ('documents.inspect', 'documents', 'Inspect document extraction status and quality.', DocumentInput, InspectionOutput, 'knowledge.read', inspect_document),
        ('knowledge.search', 'knowledge', 'Search approved internal knowledge locally.', SearchInput, SearchOutput, 'knowledge.read', search),
        ('sop.facts', 'sop', 'Read cited facts from an approved SOP version.', FactsInput, FactsOutput, 'knowledge.read', facts),
    ]:
        runtime.register(SkillDefinition(name, domain, '1.0', description, input_model, output_model,
            permission=permission, tool_class=ToolClass.WRITE if name == 'documents.prepare' else ToolClass.READ), handler)
    return runtime
