"""Observe real provider wording without creating a review trial or decision."""
import asyncio
import json
import os
import sys
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from dotenv import dotenv_values
from app.core.nusantara_config import load_nusantara_config
from app.models.ollama import OllamaProvider
from app.knowledge.grounding import EvidenceGroundingGuard
from app.knowledge.sop_review import sop_prompt, sop_wording_supported
from app.knowledge.document_context import select_blocks, project_activity_blocks

async def main():
    snapshot = json.loads((ROOT / 'reports/remediation/20261027-priority-fixes/live-sop-review-snapshot.json').read_text(encoding='utf-8'))
    config = load_nusantara_config(dotenv_environment=dotenv_values(ROOT / '.env', interpolate=False), environment=os.environ, project_root=ROOT)
    provider = OllamaProvider(nusantara_config=config)
    question = 'Apakah SOP ini menyebutkan nomor WhatsApp petugas? Jika tidak ada, katakan belum ditemukan dalam SOP.'
    with sqlite3.connect(config.knowledge.database.as_uri() + '?mode=ro', uri=True) as connection:
        row = connection.execute("SELECT payload FROM document_extractions WHERE document_id=? AND status='COMPLETE' ORDER BY rowid DESC LIMIT 1", (snapshot['document_id'],)).fetchone()
    document = json.loads(row[0])
    blocks = document['blocks']
    full_size = sum(len(block['content'].encode('utf-8')) + 80 for block in blocks)
    if full_size > config.llm.generation.context_length - 1100 - len(question.encode('utf-8')):
        blocks = project_activity_blocks(document, question)
    text, included, omitted = select_blocks(blocks, question, config.llm.generation.context_length)
    if any(block.get('selected_columns') for block in included):
        text = 'Konteks tabel dipilih menurut pertanyaan; kolom/baris lain tersedia pada pembacaan dokumen lengkap.\n' + text
    system, prompt = sop_prompt(text, question, [], config.llm.generation.context_length)
    try:
        generated = await provider.generate({'system': system, 'prompt': prompt, 'temperature': 0.1, 'max_tokens': 128})
    except Exception as error:
        response = getattr(error.__cause__, 'response', None)
        result = {'error_type': type(error).__name__,
                  'provider_http_status': response.status_code if response is not None else None,
                  'provider_error': response.json().get('error') if response is not None else None}
        Path(__file__).with_name('provider-error.json').write_text(json.dumps(result), encoding='utf-8')
        print(json.dumps(result), flush=True)
        raise SystemExit(1)
    answer = str(generated.get('content', '')).strip()
    checked = EvidenceGroundingGuard().validate(answer, [{'text': text, 'chunk': text, 'score': 1.}], '')
    result = {'model_answer': answer, 'grounded': checked.grounded, 'reason': checked.reason,
              'pilot_wording_supported': sop_wording_supported(answer, text), 'omitted_blocks': omitted}
    Path(__file__).with_name('model-probe.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=True, indent=2))

asyncio.run(main())
