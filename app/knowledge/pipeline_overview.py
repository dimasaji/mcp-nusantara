"""SOP progress projection from current version-bound review state."""
import json
import logging
from collections import Counter

from .document_tools import DocumentTools
from .sop_review import SOPReview

WORKFLOW_STATES = ('ACTIVE', 'QUEUED', 'PROCESSING', 'REVIEW_REQUIRED',
                   'APPROVAL_REQUIRED', 'BLOCKED', 'UNKNOWN')
logger = logging.getLogger(__name__)


def _document_progress(engine, document, review, tools):
    identifier = document['document_id']
    for _ in range(3):
        detail = review.detail(identifier)
        extraction = tools.status(identifier, detail['version_id'])
        current = review.detail(identifier)
        if (current['version_id'], current['extraction_job_id']) != (
                detail['version_id'], extraction.get('job_id')):
            continue
        detail = current
        payload = None
        if extraction.get('job_id'):
            with engine._pipeline_db() as conn:
                row = conn.execute('SELECT payload FROM document_extractions WHERE job_id=?',
                                   (extraction['job_id'],)).fetchone()
            payload = json.loads(row['payload']) if row and row['payload'] else None
            if payload and extraction['status'] == 'COMPLETE':
                if review.extracted_version(detail['source_version_id'], payload) != detail['version_id']:
                    continue
        is_pdf = detail['source_type'] == '.pdf'
        extracting = is_pdf and extraction['status'] in {'QUEUED', 'PROCESSING'}
        extraction_failed = is_pdf and extraction['status'] in {'FAILED', 'PARTIAL', 'STOPPING'}
        indexed = document['status'] == 'READY' and document['chunks_count'] > 0
        clean_profile = (payload or {}).get('text_cleaning') if is_pdf else document.get('text_cleaning')
        requirements = {item['key']: item['satisfied'] for item in detail['approval_requirements']}
        reviewed = all(requirements.get(key, False) for key in (
            'content_checked', 'metadata_checked', 'metadata_publication_allowed',
            'metadata_revision_valid', 'no_open_problems'))
        active = detail['status'] == 'Aktif'
        blocked_decision = (detail.get('publication_decision') or {}).get('kind') in {'reject', 'defer', 'revoke'}
        if not detail['source_available'] or extraction_failed or detail['problems'] or blocked_decision:
            state = 'BLOCKED'
        elif extracting:
            state = extraction['status']
        elif active:
            state = 'ACTIVE'
        elif detail['can_approve']:
            state = 'APPROVAL_REQUIRED'
        else:
            state = 'REVIEW_REQUIRED'
        stages = {
            'source': 'SUCCEEDED' if detail['source_available'] else 'FAILED',
            'extraction': ('FAILED' if extraction_failed else 'RUNNING' if extracting else
                           'SUCCEEDED' if not is_pdf or extraction['status'] == 'COMPLETE' else 'WAITING'),
            'cleaning': 'SUCCEEDED' if clean_profile else 'WAITING' if extracting else 'UNKNOWN',
            'indexing': 'SUCCEEDED' if indexed else 'WAITING',
            'review': 'SUCCEEDED' if reviewed else 'FAILED' if detail['problems'] else 'WAITING',
            'approval': 'SUCCEEDED' if active else 'FAILED' if blocked_decision else 'WAITING',
            'availability': 'SUCCEEDED' if active else 'WAITING',
        }
        action = ('chat' if active else 'wait' if extracting else
                  'prepare' if is_pdf and extraction['status'] == 'NOT_PROCESSED' else 'review')
        return {'review_status': detail['status'], 'title': detail['title'], 'workflow': {
            'state': state, 'version_id': detail['version_id'], 'stages': stages,
            'extraction_status': extraction['status'] if is_pdf else 'NOT_REQUIRED',
            'cleaning_profile': (clean_profile or {}).get('profile'),
            'reason': extraction.get('error') or detail['status'], 'next_action': action,
        }}
    raise ValueError('DOCUMENT_VERSION_CHANGED')


def enrich_pipeline_status(engine, status):
    """Count current documents and latest failed sources separately."""
    review = SOPReview(engine)
    tools = DocumentTools(engine, operator=True)
    for document in status.get('documents', []):
        try:
            document.update(_document_progress(engine, document, review, tools))
        except Exception as exc:
            logger.warning('SOP progress unavailable: document=%s error_type=%s',
                           document['document_id'], type(exc).__name__)
            document.update(review_status='Status perlu diperiksa', workflow={
                'state': 'UNKNOWN', 'version_id': None, 'stages': {},
                'extraction_status': 'UNKNOWN', 'cleaning_profile': None,
                'reason': 'Status dokumen belum dapat dibaca. Buka pemeriksaan dokumen.',
                'next_action': 'review',
            })
    counts = Counter(doc['workflow']['state'] for doc in status.get('documents', []))
    with engine._pipeline_db() as conn:
        failures = [dict(row) for row in conn.execute(
            "SELECT run_id,filename,reason,source_path FROM knowledge_pipeline_runs "
            "WHERE rowid IN (SELECT MAX(rowid) FROM knowledge_pipeline_runs GROUP BY source_sha256) "
            "AND status='FAILED' ORDER BY rowid DESC")]
    status['sop_summary'] = {
        'scope': 'CURRENT_KNOWLEDGE', 'total': len(status.get('documents', [])),
        'counts': {state: counts[state] for state in WORKFLOW_STATES},
        'failed_sources': [{'run_id': row['run_id'], 'filename': row['filename'],
                            'reason': row['reason'], 'retryable': bool(row['source_path'])}
                           for row in failures],
    }
    return status
