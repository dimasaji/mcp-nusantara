"""Focused context/evaluation contracts, runnable with Python's unittest."""
import unittest
from types import SimpleNamespace

from app.knowledge.pdf_sop import requested_step
from app.knowledge.document_answers import document_answer_facts
from app.knowledge.document_context import project_activity_blocks, select_blocks


def large_document():
    rows = [{'number': number, 'activity': f'Memeriksa berkas tahap {number} lalu mencatat hasil pemeriksaan',
             'kelengkapan': 'Berkas warga', 'waktu': '5 menit', 'output': 'Hasil pemeriksaan',
             'keterangan': '', 'page': 2, 'block_id': 'grid'} for number in range(1, 41)]
    return {'blocks': [{'block_id': 'grid', 'type': 'table', 'content': 'Tabel lengkap ' * 1000,
                        'page_numbers': [2]}], 'activity_rows': rows}


class ContextPathTests(unittest.TestCase):
    def test_numbered_step_uses_only_that_verified_row_with_page_and_header(self):
        doc = large_document()
        projected = project_activity_blocks(doc, 'Bagaimana langkah ke-5?')
        self.assertEqual(projected[0]['selected_rows'], [5])
        self.assertEqual(projected[0]['page_numbers'], [2])
        self.assertIn('Uraian Kegiatan', projected[0]['content'])
        text, included, omitted = select_blocks(projected, 'Bagaimana langkah ke-5?', 1800)
        self.assertIn('berkas tahap 5', text)
        self.assertNotIn('berkas tahap 6', text)
        self.assertEqual(included[0]['block_id'], 'grid')
        self.assertEqual(len(included[0]['omitted_rows']), 39)
        self.assertEqual(omitted, [])

    def test_numbered_step_facts_do_not_return_the_whole_procedure(self):
        doc = large_document()
        item = SimpleNamespace(document_id='fixture', title='SOP contoh', source='Tabel sumber', score=1.,
            metadata={'sop_rows': doc['activity_rows']})
        facts = document_answer_facts('Bagaimana langkah ke-5?', [item])
        self.assertIn('berkas tahap 5', facts['fallback'])
        self.assertNotIn('berkas tahap 6', facts['fallback'])
        self.assertEqual(facts['pages'], [2])

    def test_ranges_are_not_silently_reduced_to_first_step(self):
        for phrase in ('5–7', '5/6', '5 s.d. 7', '5 sampai selesai', '5 dan 6', '5—7'):
            with self.subTest(phrase=phrase):
                self.assertIsNone(requested_step('Jelaskan langkah ' + phrase))

    def test_step_facets_use_own_cells_and_missing_step_clarifies(self):
        doc = large_document()
        doc['activity_rows'][4]['kelengkapan'] = 'Lembar verifikasi internal'
        item = SimpleNamespace(document_id='fixture', title='SOP contoh', score=1.,
                               metadata={'sop_rows': doc['activity_rows']})
        self.assertEqual(document_answer_facts('Berapa lama langkah ke-5?', [item])['fallback'],
                         'Menurut SOP: 5 menit.')
        self.assertIn('Lembar verifikasi internal',
                      document_answer_facts('Apa kelengkapan langkah ke-5?', [item])['fallback'])
        self.assertTrue(document_answer_facts('Bagaimana langkah ke-99?', [item])['clarify'])
        self.assertTrue(document_answer_facts('Berapa biaya langkah ke-5?', [item])['clarify'])
        self.assertTrue(document_answer_facts('Berapa biaya dokumen langkah ke-5?', [item])['clarify'])
        self.assertEqual(document_answer_facts('Berapa lama dokumen langkah ke-5?', [item])['facet'], 'duration')
        projected = project_activity_blocks(doc, 'Apa syarat langkah ke-5?')
        self.assertNotIn('Kelengkapan pemohon', projected[0]['content'])


class RuntimeEvaluationTests(unittest.TestCase):
    def setUp(self):
        from scripts.evaluate_sop_runtime import evaluate, grade, validate_cases
        self.evaluate, self.grade, self.validate = evaluate, grade, validate_cases
        self.case = {'id': 'duration', 'question': 'Berapa lama?', 'document_id': 'doc',
                     'version_id': 'version', 'required': ['3 hari kerja'], 'pages': [2],
                     'forbidden': ['99 hari']}
        self.response = {'response': 'Menurut SOP: 3 hari kerja.', 'provider_status': 'evidence_fast_path',
                         'grounding': {'grounded': True}, 'trust': {'supports_claim': True},
                         'evidence': [{'document_id': 'doc', 'pages': [2]}]}

    def test_rejects_empty_dataset_and_vacuous_positive_case(self):
        for cases in ([], [{}], [{**self.case, 'required': []}], [{**self.case, 'pages': []}]):
            with self.assertRaises(ValueError):
                self.validate(cases)

    def test_facts_citations_model_and_abstention_are_independent(self):
        self.assertTrue(all(self.grade(self.case, self.response).values()))
        self.assertFalse(self.grade(self.case, {**self.response, 'response': '99 hari'})['facts'])
        self.assertFalse(self.grade(self.case, {**self.response, 'evidence': []})['citations'])
        self.assertFalse(self.grade({**self.case, 'require_ollama': True}, self.response)['ollama_generation'])
        self.assertFalse(self.grade({**self.case, 'abstain': True}, self.response)['abstention'])

    def test_live_request_contract_checks_version_build_and_redacts_text(self):
        import json
        calls = []
        def request(method, path, payload):
            calls.append((method, path, payload))
            if path == '/health':
                return {'build_id': 'build'}
            if method == 'GET':
                return {'status': 'Aktif', 'version_id': 'version'}
            return self.response
        report = self.evaluate([self.case], request, 'build')
        self.assertTrue(report['passed'])
        payload = next(p for m, _, p in calls if m == 'POST')
        self.assertNotIn('document_ids', payload)
        self.assertEqual(payload['user_input'], self.case['question'])
        serialized = json.dumps(report)
        self.assertNotIn(self.case['question'], serialized)
        self.assertNotIn(self.response['response'], serialized)
        self.assertEqual(report['native_embedding'], 'NOT_ATTESTED')
        with self.assertRaises(ValueError):
            self.evaluate([self.case], request, 'other-build')

    def test_changed_source_version_cannot_pass(self):
        reviews = []
        def request(method, path, payload):
            if path == '/health':
                return {'build_id': 'build'}
            if method == 'GET':
                reviews.append(path)
                return {'status': 'Aktif', 'version_id': 'version' if len(reviews) == 1 else 'changed'}
            return self.response
        report = self.evaluate([self.case], request)
        self.assertFalse(report['passed'])
        self.assertFalse(report['cases'][0]['checks']['source_stable'])

    def test_client_rejects_remote_and_credential_urls(self):
        from scripts.evaluate_sop_runtime import http_client
        for url in ('https://example.com', 'http://user:pass@localhost', 'http://localhost/remote'):
            with self.assertRaises(ValueError):
                http_client(url, 'fixture-token')

    def test_numeric_phrases_match_whole_tokens_and_abstention_requires_text(self):
        wrong = {**self.response, 'response': '13 hari kerja'}
        self.assertFalse(self.grade(self.case, wrong)['facts'])
        wrong = {**self.response, 'response': '199 hari'}
        self.assertTrue(self.grade(self.case, wrong)['forbidden_absent'])
        abstain = {**self.case, 'abstain': True, 'required': ['tidak ditemukan']}
        wrong = {**self.response, 'response': 'Wajib membawa 99 dokumen.',
                 'grounding': {'reason': 'no_evidence', 'grounded': True}}
        self.assertFalse(all(self.grade(abstain, wrong).values()))
        right = {**self.response, 'response': 'Informasi tidak ditemukan.',
                 'grounding': {'reason': 'no_evidence', 'grounded': False},
                 'trust': {'supports_claim': False}}
        self.assertTrue(all(self.grade(abstain, right).values()))

    def test_loopback_client_disables_environment_proxies(self):
        from unittest.mock import patch
        from scripts.evaluate_sop_runtime import http_client, ProxyHandler
        with patch('scripts.evaluate_sop_runtime.build_opener') as build:
            http_client('http://127.0.0.1:8000', 'fixture-token')
        handlers = build.call_args.args
        self.assertTrue(any(isinstance(h, ProxyHandler) and h.proxies == {} for h in handlers))


if __name__ == '__main__':
    unittest.main()
