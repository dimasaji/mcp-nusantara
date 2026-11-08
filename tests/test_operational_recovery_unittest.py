"""Maintenance must recover queued work independently of inbox failures."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch


class MaintenanceTests(unittest.TestCase):
    def test_inbox_failure_does_not_skip_persisted_queue_recovery(self):
        from app.knowledge.maintenance import maintain_knowledge
        engine = SimpleNamespace(scan_knowledge_watch=lambda: (_ for _ in ()).throw(RuntimeError('fixture inbox failed')))
        with patch('app.knowledge.document_tools.DocumentTools') as tools:
            tools.return_value.resume_queued.return_value = 2
            result = maintain_knowledge(engine)
        tools.return_value.resume_queued.assert_called_once()
        self.assertEqual(result['queue'], 'SUCCEEDED')
        self.assertEqual(result['inbox'], 'FAILED')

    def test_queue_failure_does_not_skip_inbox_scan(self):
        from app.knowledge.maintenance import maintain_knowledge
        calls = []
        engine = SimpleNamespace(scan_knowledge_watch=lambda: calls.append('scan'))
        with patch('app.knowledge.document_tools.DocumentTools') as tools:
            tools.return_value.resume_queued.side_effect = RuntimeError('fixture queue failed')
            result = maintain_knowledge(engine)
        self.assertEqual(calls, ['scan'])
        self.assertEqual(result['queue'], 'FAILED')
        self.assertEqual(result['inbox'], 'SUCCEEDED')


if __name__ == '__main__':
    unittest.main()
