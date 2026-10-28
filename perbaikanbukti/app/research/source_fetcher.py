"""Bounded HTTPS acquisition; exact DNS-pinned public addresses, no redirects/proxies.

This only acquires candidate content. It never ingests or promotes trusted data.
"""
from __future__ import annotations

import http.client
import ipaddress
import socket
import ssl
from urllib.parse import urlsplit

from app.research.knowledge_discovery import SourceRejected, SourceValidator


class _PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self, host: str, address: str, timeout: float):
        super().__init__(host, timeout=timeout, context=ssl.create_default_context())
        self.address = address

    def connect(self):
        raw = socket.create_connection((self.address, 443), self.timeout)
        try:
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except Exception:
            raw.close()
            raise


class SourceFetcher:
    def __init__(self, validator: SourceValidator, *, max_bytes: int = 1_000_000,
                 timeout_s: float = 10, resolver=socket.getaddrinfo, connection=_PinnedHTTPS):
        self.validator = validator
        self.max_bytes, self.timeout_s = max_bytes, timeout_s
        self.resolver, self.connection = resolver, connection

    def fetch(self, uri: str) -> str:
        u = urlsplit(uri)
        ok, why = self.validator.validate(uri)
        if (not ok or u.scheme != "https" or not u.hostname or u.username or u.password
                or u.fragment or u.port not in (None, 443)
                or u.hostname.lower() not in self.validator.allowed_hosts):
            raise SourceRejected("URL tidak diizinkan: " + why)
        addresses = self.resolver(u.hostname, 443, type=socket.SOCK_STREAM)
        ips = {str(row[4][0]) for row in addresses}
        if not ips or any(not ipaddress.ip_address(ip).is_global for ip in ips):
            raise SourceRejected("sumber harus memiliki alamat jaringan publik")
        conn = self.connection(u.hostname, sorted(ips)[0], self.timeout_s)
        try:
            conn.request("GET", (u.path or "/") + ("?" + u.query if u.query else ""), headers={
                "Accept": "text/plain,text/html,application/xhtml+xml", "Accept-Encoding": "identity",
                "User-Agent": "Nusantara-Candidate-Discovery/1.0"})
            response = conn.getresponse()
            if response.status != 200:
                raise SourceRejected("sumber tidak merespons 200; redirect tidak diikuti")
            if response.getheader("Content-Encoding", "identity").lower() != "identity":
                raise SourceRejected("compressed responses are not accepted")
            content_type = response.getheader("Content-Type", "").split(";")[0].lower()
            if content_type not in {"text/plain", "text/html", "application/xhtml+xml"}:
                raise SourceRejected("format sumber tidak didukung")
            body = response.read(self.max_bytes + 1)
            if len(body) > self.max_bytes:
                raise SourceRejected("sumber terlalu besar")
            return body.decode("utf-8", errors="replace")
        finally:
            conn.close()
