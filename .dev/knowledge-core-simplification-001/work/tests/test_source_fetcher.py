import socket

import pytest

from app.research.knowledge_discovery import CandidateStore, SourceRejected, SourceValidator
from app.research.source_fetcher import SourceFetcher


def resolver(address):
    return lambda *args, **kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, 443))]


@pytest.mark.parametrize("address", ["127.0.0.1", "10.0.0.1", "169.254.169.254", "::1", "192.168.1.1"])
def test_ssrf_rejected_before_connect(address):
    fetcher = SourceFetcher(SourceValidator({"example.org"}), resolver=resolver(address),
                            connection=lambda *args: pytest.fail("network connection must not occur"))
    with pytest.raises(SourceRejected):
        fetcher.fetch("https://example.org/doc")


def test_subdomain_requires_its_own_exact_allowlist_entry():
    fetcher = SourceFetcher(SourceValidator({"example.org"}),
                            resolver=lambda *a, **k: pytest.fail("DNS must not run"))
    with pytest.raises(SourceRejected):
        fetcher.fetch("https://unreviewed.example.org/doc")


def test_pinned_connection_size_redirect_and_provenance(tmp_path):
    calls = []

    class Response:
        status = 200
        body = b"Trusted source example content for a candidate."
        def getheader(self, key, default=""):
            return "text/plain" if key == "Content-Type" else default
        def read(self, limit):
            return self.body[:limit]

    class Connection:
        def __init__(self, *args):
            calls.append(args)
        def request(self, *args, **kwargs):
            pass
        def getresponse(self):
            return Response()
        def close(self):
            pass

    validator = SourceValidator({"example.org"})
    fetcher = SourceFetcher(validator, resolver=resolver("93.184.216.34"), connection=Connection)
    content = fetcher.fetch("https://example.org/doc")
    assert calls[0][:2] == ("example.org", "93.184.216.34")
    store = CandidateStore(validator, tmp_path / "candidates.json")
    first = store.propose("gap", "https://example.org/doc", content, title="Example", topic="test", provided_by="reviewer")
    assert store.propose("gap", first.uri, content, title="Example", topic="test", provided_by="reviewer").candidate_id == first.candidate_id
    assert CandidateStore(validator, tmp_path / "candidates.json").get(first.candidate_id).status == "candidate"
    Response.status = 302
    with pytest.raises(SourceRejected):
        fetcher.fetch(first.uri)
    Response.status = 200
    fetcher.max_bytes = 10
    with pytest.raises(SourceRejected):
        fetcher.fetch(first.uri)
