"""Phase 12: transport contract, failure accounting and honest baseline comparison."""
import contextlib
import io
import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from app.evaluation import EvalCase, compare, run_cases
from scripts.run_eval import V1System, main


class Handler(BaseHTTPRequestHandler):
    requests = []
    reply = {"response": "Biaya KTP gratis", "evidence": [
        {"document_id": "ktp", "chunk": "Biaya KTP gratis", "source": "https://example.org"}]}
    code = 200

    def log_message(self, *args):
        pass

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"status":"ok","version":"test"}')

    def do_POST(self):
        self.requests.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
        self.send_response(self.code)
        if self.code == 302:
            self.send_header("Location", "/redirect")
        self.end_headers()
        self.wfile.write(json.dumps(self.reply).encode())


class LiveHarness(unittest.TestCase):
    def setUp(self):
        Handler.requests = []
        Handler.code = 200
        Handler.reply = {"response": "Biaya KTP gratis", "evidence": [
            {"document_id": "ktp", "chunk": "Biaya KTP gratis", "source": "https://example.org"}]}
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def test_v1_transport_maps_evidence_and_isolates_sessions(self):
        api = V1System(self.url)
        first = api("biaya ktp")
        api("biaya ktp")
        self.assertEqual(first["evidence"], ["Biaya KTP gratis"])
        self.assertEqual(first["retrieved_doc_ids"], ["ktp"])
        self.assertNotEqual(Handler.requests[0]["session_id"], Handler.requests[1]["session_id"])
        self.assertFalse(Handler.requests[0]["stream"])
        self.assertEqual(Handler.requests[0]["user_input"], "biaya ktp")
        self.assertNotIn("policy_decision", first)

    def test_source_url_is_not_grounding_evidence(self):
        Handler.reply = {"response": "Klaim", "evidence": [{"source": "https://example.org"}]}
        res = run_cases(V1System(self.url), [EvalCase("x", "q", requires_evidence=True)])
        self.assertEqual(res["metrics"]["groundedness"], 0)

    def test_errors_and_invalid_payloads_fail_closed(self):
        for code, reply in [(500, {"detail": "private secret"}), (200, {"response": ""}),
                            (200, {"response": "x", "evidence": "wrong"}), (302, {})]:
            with self.subTest(code=code, reply=reply):
                Handler.code, Handler.reply = code, reply
                result = run_cases(V1System(self.url), [EvalCase("x", "q")])
                self.assertEqual(result["metrics"]["reliability"], 0)
                self.assertNotIn("private secret", json.dumps(result))

    def test_first_failed_repeat_is_not_hidden(self):
        calls = 0

        def intermittent(query):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise TimeoutError("secret error")
            return {"answer": "ok"}

        result = run_cases(intermittent, [EvalCase("x", "q")], repeats=2)
        self.assertEqual(result["metrics"]["reliability"], 0.5)
        self.assertEqual(result["records"][0]["attempts"][0]["error_type"], "TimeoutError")

    def test_cli_captures_live_baseline_and_detects_regression(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            root = Path(directory)
            dataset = root / "cases.json"
            dataset.write_text(json.dumps([{"case_id": "x", "query": "biaya ktp",
                                           "expected_contains": ["gratis"], "requires_evidence": True}]))
            baseline, candidate = root / "base.json", root / "candidate.json"
            args = ["--base-url", self.url, "--dataset", str(dataset), "--repeats", "1"]
            self.assertEqual(main(args + ["--output", str(baseline)]), 0)
            self.assertEqual(json.loads(baseline.read_text())["meta"]["mode"], "live_v1")
            Handler.reply = {"response": "Tidak diketahui", "evidence": []}
            self.assertEqual(main(args + ["--output", str(candidate), "--baseline", str(baseline)]), 1)
            result = json.loads(candidate.read_text())
            self.assertEqual(result["comparison"]["verdict"], "REGRESSION")
            self.assertFalse(result["auto_accept"])

    def test_mock_baseline_cannot_be_used_for_live_comparison(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            baseline = Path(directory) / "mock.json"
            output = Path(directory) / "live.json"
            self.assertEqual(main(["--mock", "--output", str(baseline)]), 0)
            self.assertEqual(main(["--base-url", self.url, "--baseline", str(baseline), "--output", str(output)]), 2)
            self.assertFalse(output.exists())

    def test_empty_dataset_and_baseline_overwrite_rejected(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            path = Path(directory) / "empty.json"
            path.write_text("[]")
            self.assertEqual(main(["--dataset", str(path)]), 2)
            baseline = Path(directory) / "mock.json"
            self.assertEqual(main(["--mock", "--output", str(baseline)]), 0)
            before = baseline.read_bytes()
            self.assertEqual(main(["--mock", "--output", str(baseline), "--baseline", str(baseline)]), 2)
            self.assertEqual(baseline.read_bytes(), before)

    def test_url_credentials_rejected(self):
        for url in ["file:///tmp/x", "https://user:secret@example.org", "http://example.org?token=x"]:
            with self.assertRaises(ValueError):
                V1System(url)

    def test_disappearing_baseline_metric_is_not_neutral(self):
        result = compare({"groundedness": .9}, {"groundedness": None})
        self.assertEqual(result["verdict"], "REGRESSION")


if __name__ == "__main__":
    unittest.main()
