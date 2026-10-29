"""Read-only V1 prerequisites. Inventory is never reported as live inference."""
import asyncio
import os
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Header, Query

from app.core.runtime_identity import BUILD_ID
from app.security.auth import require_admin

router = APIRouter(prefix='/runtime', tags=['runtime'])


def require_readiness_operator(x_admin_token: str | None = Header(default=None)):
    require_admin(x_admin_token)


def get_runtime_owner():
    from app.core.config import settings
    return settings


def get_readiness_knowledge():
    from app.api.routes import _knowledge
    return _knowledge


def get_provider_factory():
    from app.models.ollama import OllamaProvider
    return OllamaProvider


def storage_check(knowledge, document_id):
    """Open the existing SQLite store read-only, including its committed WAL."""
    path = Path(knowledge.rag._store.db_path).resolve()
    try:
        with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=1)) as conn:
            count = conn.execute('SELECT count(*) FROM documents').fetchone()[0]
        storage = {'status': 'READABLE', 'documents_indexed': count}
    except (OSError, sqlite3.Error):
        return {'status': 'UNAVAILABLE'}, {'status': 'NOT_CHECKED'}
    document = {'status': 'NOT_CHECKED'}
    if document_id:
        from app.knowledge.sop_review import SOPReview
        try:
            detail = SOPReview(knowledge, read_only=True).detail(document_id)
            document = {'status': 'APPROVED' if detail['status'] == 'Aktif' else 'BLOCKED',
                        'review_status': detail['status'], 'version_id': detail['version_id'],
                        'metadata_confirmed': detail['metadata_confirmed']}
        except (ValueError, sqlite3.Error):
            document = {'status': 'UNAVAILABLE'}
    return storage, document


@router.get('/readiness')
async def runtime_readiness(authorized=Depends(require_readiness_operator),
                            document_id: str | None = Query(default=None, min_length=1, max_length=256),
                            owner=Depends(get_runtime_owner), knowledge=Depends(get_readiness_knowledge),
                            provider_factory=Depends(get_provider_factory)):
    configuration, revision = owner.configuration_snapshot()
    provider_name, model = configuration.llm.provider, configuration.llm.model
    checks = {'api': {'status': 'AVAILABLE'}, 'provider': {'status': 'NOT_CHECKED'},
              'model': {'status': 'NOT_CHECKED'}, 'inference': {'status': 'NOT_VERIFIED'}}
    if provider_name != 'ollama':
        checks['provider'] = {'status': 'LOCAL_PROVIDER_REQUIRED'}
    else:
        provider = provider_factory(nusantara_config=configuration)
        try:
            health = await asyncio.wait_for(provider.health_check(), timeout=10)
            checks['provider'] = {'status': 'UNAVAILABLE' if health['status'] == 'unavailable' else 'CONNECTED'}
            checks['model'] = {'status': 'AVAILABLE' if health['available'] else
                               'NOT_CHECKED' if health['status'] == 'unavailable' else 'MISSING'}
        except Exception:
            checks['provider'] = {'status': 'UNAVAILABLE'}
        finally:
            try:
                await asyncio.wait_for(provider.close(), timeout=2)
            except Exception:
                pass
    try:
        checks['storage'], checks['document'] = await asyncio.wait_for(
            asyncio.to_thread(storage_check, knowledge, document_id), timeout=5)
    except Exception:
        checks['storage'], checks['document'] = {'status': 'UNAVAILABLE'}, {'status': 'NOT_CHECKED'}
    observed = owner.model_control_status()
    _, current_revision = owner.configuration_snapshot()
    consistent = current_revision == revision == observed['revision']
    if consistent and observed['status'] == 'INFERENCE_VERIFIED':
        checks['inference'] = {'status': 'OBSERVED', 'verified_at': observed.get('verified_at'),
                               'scope': 'CURRENT_MODEL_REVISION_PROCESS_300_SECONDS'}
    prerequisites = (consistent and checks['model']['status'] == 'AVAILABLE'
                     and checks['storage']['status'] == 'READABLE'
                     and (not document_id or checks['document']['status'] == 'APPROVED'))
    return {'status': 'CONFIGURATION_CHANGED' if not consistent else
                     'PREREQUISITES_READY' if prerequisites else 'BLOCKED',
            'provider': provider_name, 'model': model, 'configuration_revision': revision,
            'process_id': os.getpid(), 'build_id': BUILD_ID,
            'build_verification': 'SOURCE_SNAPSHOT', 'checked_at': datetime.now(UTC).isoformat(),
            'checks': checks, 'operational_acceptance': 'NOT_VERIFIED',
            'scope': 'READ_ONLY_PROBE_NO_GENERATION_NO_E2E'}
