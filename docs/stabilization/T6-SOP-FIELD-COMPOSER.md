# T6 — Deterministic SOP Answer Composer

**Date:** 2026-11-17

## 1. Implementation

- Module: `app/knowledge/sop_fields.py`
- Functions: `extract_sop_fields(text)` and `compose_answer(fields, question)`
- Extracts: title, requirements, procedure, duration, cost, legal_basis, product, channel
- Composes deterministic answers from extracted fields

## 2. Current Capability

| Field | Text-based SOPs | Table-based SOPs |
|---|---|---|
| Title | ✅ Extracted | ✅ Extracted (from "NAMA SOP") |
| Requirements | ⚠️ Partial (line-based) | ❌ In table cells |
| Procedure | ⚠️ Partial (line-based) | ❌ In table cells |
| Duration | ✅ Extracted (regex) | ✅ Extracted (regex) |
| Cost | ⚠️ Partial (regex) | ⚠️ Partial |
| Legal basis | ⚠️ Partial (line-based) | ❌ In table cells |
| Product | ⚠️ Partial (regex) | ❌ In table cells |
| Channel | ✅ Extracted (online/loket) | ✅ Extracted |

## 3. Limitation

SOP documents use a structured table format (activity grid) where requirements, procedures, and other fields are in table cells, not in "Persyaratan: ..." lines. The current extractor only handles text-based patterns.

## 4. Next Steps

1. Parse Docling table_data.table_cells to extract fields
2. Map table columns to SOP fields (persyaratan, prosedur, waktu, biaya, dll.)
3. Test on 5 SOP pilot (CAPIL_02, CAPIL_04, DAFDUK_01, DAFDUK_22, CAPIL_01)
4. Run make eval to compare with baseline
5. Expand to all 44 SOPs

## 5. Status

- Field extractor: ✅ Created
- Text-based extraction: ⚠️ Partial (title, duration, channel work; requirements/procedure need table parsing)
- Table-based extraction: ❌ Not implemented
- Deterministic composer: ✅ Created (compose_answer)
- Integration with Hermes fast path: ❌ Not yet wired

**Status: PARTIAL (framework ready, table parsing needed)**
