# Nusantara AI Production Knowledge Base

## Source directory

Place production documents under:

data/knowledge/source/

Recommended structure:

data/knowledge/source/
├── ktp_el/
├── kartu_keluarga/
├── kia/
├── akta_kelahiran/
├── akta_kematian/
├── perkawinan/
├── perceraian/
├── pindah_datang/
├── perubahan_data/
└── layanan_online/

## Supported

- PDF
- DOCX
- TXT
- Markdown
- JSON
- HTML

## Commands

Self test:

python -m app.knowledge.production_kb self-test

Ingest:

python -m app.knowledge.production_kb ingest

Statistics:

python -m app.knowledge.production_kb stats

Search:

python -m app.knowledge.production_kb search "Apa itu KTP-el?"

## Database

data/knowledge/production_knowledge.db

## Safety

The production database is intentionally separated from:

data/knowledge/nusantara_knowledge.db

The existing Knowledge Engine is therefore not modified by ingestion.

Every source document receives:

- SHA-256 source hash
- deterministic document ID
- chunk IDs
- text hashes
- service classification
- content type classification
- ingestion timestamp

The ingestion process also creates database backups.
