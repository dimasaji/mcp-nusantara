"""Record the review against the supplied PIAK-03 PDF, without changing its text/index."""
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader
from app.core.config import settings

SOURCE=Path('data/knowledge/sop/original/PERMOHONAN_DATA_PRIBADI.pdf')
SHA='75d5b40df368e826f8dc5eace35ccc0daaaf26499b241a278962832334e8db50'
ID='sop_e4d43334bc32fa5a97972fb64bb34e9c'


def main():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==SHA, 'Source revision changed; review again'
    reader=PdfReader(SOURCE)
    text='\n'.join(page.extract_text() or '' for page in reader.pages)
    for phrase in ('Nama S.O.P PERMOHONAN DATA PRIBADI','Nomor SOP PIAK-03','Menyampaikan Surat Permohonan',
                   'Memverifikasi Data Proses dalam Database','Menerima Surat Jawaban Permohonan data dan berkas data',
                   'Proses pelayanan permohonan data selesai 3 Hari Kerja'):
        assert phrase in text, phrase
    configuration,_=settings.configuration_snapshot()
    database=configuration.knowledge.database
    conn=sqlite3.connect(database);conn.row_factory=sqlite3.Row
    row=conn.execute('SELECT * FROM documents WHERE document_id=?',(ID,)).fetchone()
    assert row is not None
    original=dict(row)
    metadata=json.loads(row['metadata_json'])
    assert metadata['source_sha256']==SHA
    for phrase in ('Surat Permohonan.','memverifikasi data dalam database','3 Hari Kerja'):
        assert phrase in row['source'], phrase
    out=Path('artifacts/v1-six');out.mkdir(parents=True,exist_ok=True)
    backup=out/'piak03-document-before.json'
    if not backup.exists():
        backup.write_text(json.dumps(original,indent=2,ensure_ascii=False),encoding='utf-8')
    chunks=conn.execute('SELECT COUNT(*) FROM chunks WHERE document_id=?',(ID,)).fetchone()[0]
    assert chunks==row['chunks_count'] and chunks>0
    now=datetime.now(timezone.utc).isoformat()
    metadata.update(official_title='PERMOHONAN DATA PRIBADI',internal_sop_id='PIAK-03',
        source_verification='MATCHED_PROVIDED_PDF',source_verified_at=now,
        verification_reason='Judul, persyaratan Surat Permohonan, alur dan 3 Hari Kerja dicocokkan dengan PDF halaman 1–2. Revisi Agustus 2018; keberlakuan saat ini belum dikonfirmasi.',
        verification_evidence='artifacts/v1-six/PERMOHONAN_DATA_PRIBADI-1.png; artifacts/v1-six/PERMOHONAN_DATA_PRIBADI-2.png')
    # UPDATE retains chunks and embeddings; INSERT OR REPLACE would cascade-delete them.
    with conn:
        conn.execute('UPDATE documents SET title=?,metadata_json=?,updated_at=? WHERE document_id=?',
                     ('PERMOHONAN DATA PRIBADI',json.dumps(metadata,ensure_ascii=False),now,ID))
        assert conn.execute('SELECT COUNT(*) FROM chunks WHERE document_id=?',(ID,)).fetchone()[0]==chunks
    result=dict(document_id=ID,title='PERMOHONAN DATA PRIBADI',sha256=SHA,pages=2,chunks=chunks,
                status='MATCHED_PROVIDED_PDF',current_revision='NOT_CONFIRMED',verified_at=now)
    (out/'sop-source-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))


if __name__=='__main__':
    main()
