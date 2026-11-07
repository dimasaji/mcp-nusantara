"""Opt-in real worker through the core skill entrypoint, isolated DB/embedding."""
import os
import time
from pathlib import Path

import pytest


@pytest.mark.skipif(os.getenv('NUSANTARA_NATIVE_SKILL_TEST') != '1', reason='Configured local worker/models/OCR required')
def test_real_intake_skill_to_cited_facts_after_fixture_approval(tmp_path):
    from test_review_publication_v1 import _approve_fixture
    from test_sop_review import engine_at

    from app.knowledge.sop_review import SOPReview
    from app.skills.composition import OPERATOR_PERMISSIONS

    source = Path(__file__).parents[1] / ('reports/remediation/20261027-priority-fixes/database-before/0/source-documents/'
        'f9ad8a5dbdc7e16570122966ccad6dcfc3c36f447385789ae9b051a0838d7f1f.pdf')
    db = tmp_path / 'chat.db'
    engine = engine_at(db)
    result = engine.intake_document('SOP.pdf', source.read_bytes())
    assert result['preparation']['status'] == 'executed', result['preparation']['error']
    identifier = result['document_id']
    def invoke(owner, name, arguments):
        return owner.skills.execute(name, arguments, role='operator',
            permissions=set(OPERATOR_PERMISSIONS), requested_by='native-fixture')
    deadline = time.monotonic() + 300
    while time.monotonic() < deadline:
        inspected = invoke(engine, 'documents.inspect', {'document_id': identifier})
        assert inspected.status == 'executed', inspected.error
        if inspected.output['status'] not in {'QUEUED', 'PROCESSING'}:
            break
        time.sleep(.5)
    assert inspected.output['status'] == 'COMPLETE', inspected.output
    assert inspected.output['activity_count'] == 17
    assert inspected.output['page_count'] == 3
    review = SOPReview(engine)
    detail = review.detail(identifier)
    assert detail['approval'] is None
    arguments = {'document_id': identifier, 'version_id': detail['version_id'], 'question': 'Berapa lama?'}
    assert invoke(engine, 'sop.facts', arguments).output['status'] == 'not_approved'
    _approve_fixture(review, detail)  # Synthetic reviewer in isolated test storage.
    restarted = engine_at(db)
    duration = invoke(restarted, 'sop.facts', arguments)
    assert duration.status == 'executed', duration.error
    assert duration.output['facts']['fallback'] == 'Menurut SOP: 4 Hari Kerja.'
    assert duration.output['facts']['pages'] == [3]
    requirements = invoke(restarted, 'sop.facts', {**arguments, 'question': 'Apa persyaratannya?'})
    assert 'Surat Keterangan Lahir' in requirements.output['facts']['quote']
    assert 'Alamat Email' in requirements.output['facts']['quote']
