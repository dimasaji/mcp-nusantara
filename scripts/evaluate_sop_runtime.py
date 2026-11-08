"""Evaluate a running local Nusantara API against independently checked PDF facts.

No upload, approval or index mutation. Chat requests are real and may be stored by
normal chat history. Reports omit questions, responses, source text and tokens.
"""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
from uuid import uuid4


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate_cases(cases):
    if not isinstance(cases, list) or not cases:
        raise ValueError('Dataset must contain cases')
    ids = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError('Each case must be an object')
        for key in ('id', 'question', 'document_id', 'version_id'):
            if not isinstance(case.get(key), str) or not case[key].strip() or 'GANTI_' in case[key]:
                raise ValueError('Missing or placeholder field: ' + key)
        if case['id'] in ids:
            raise ValueError('Duplicate case id')
        ids.add(case['id'])
        if not isinstance(case.get('abstain', False), bool):
            raise ValueError('abstain must be boolean')
        for key in ('required', 'forbidden'):
            values = case.get(key, [])
            if not isinstance(values, list) or any(not isinstance(v, str) or not normalize(v) for v in values):
                raise ValueError(key + ' must contain nonempty phrases')
        if not case.get('required') or (not case.get('abstain') and not case.get('pages')):
            raise ValueError('Positive cases require independent facts and citation pages')
        pages = case.get('pages', [])
        if not isinstance(pages, list) or any(type(p) is not int or p < 1 for p in pages):
            raise ValueError('pages must contain positive integers')
        for key in ('selected', 'require_ollama'):
            if not isinstance(case.get(key, False), bool):
                raise ValueError(key + ' must be boolean')
        if 'conversation' in case and (not isinstance(case['conversation'], str) or not case['conversation']):
            raise ValueError('conversation must be nonempty')
    return cases


def normalize(text):
    return ' '.join(re.findall(r'\w+', text.casefold()))


def contains(text, phrase):
    return ' ' + normalize(phrase) + ' ' in ' ' + text + ' '


def grade(case, response):
    text = normalize(response.get('response', ''))
    evidence = [e for e in response.get('evidence', []) if e.get('document_id') == case['document_id']]
    grounding = response.get('grounding', {})
    checks = {'forbidden_absent': all(not contains(text, v) for v in case.get('forbidden', []))}
    if case.get('abstain'):
        checks['abstention'] = (grounding.get('reason') == 'grounded_abstention' and grounding.get('grounded') is True
                                or grounding.get('reason') == 'no_evidence' and grounding.get('grounded') is False
                                and response.get('trust', {}).get('supports_claim') is False)
        checks['abstention_phrase'] = all(contains(text, v) for v in case['required'])
    else:
        checks.update(retrieved=bool(evidence),
                      facts=all(contains(text, v) for v in case['required']),
                      citations=set(case['pages']).issubset({p for e in evidence for p in e.get('pages', [])}),
                      grounded=grounding.get('grounded') is True,
                      supported=response.get('trust', {}).get('supports_claim') is True)
    if case.get('require_ollama'):
        checks['ollama_generation'] = response.get('provider_status') == 'ollama'
    return checks


def evaluate(cases, request, expected_build=None):
    validate_cases(cases)
    health = request('GET', '/health', None)
    build = health.get('build_id')
    if not build or (expected_build and build != expected_build):
        raise ValueError('Runtime build missing or different from expected build')
    results, sessions = [], {}
    for case in cases:
        path = '/v1/knowledge/pipeline/reviews/' + quote(case['document_id'], safe='')
        before = request('GET', path, None)
        checks = {'source_active': before.get('status') == 'Aktif',
                  'source_version': before.get('version_id') == case['version_id']}
        start = time.monotonic()
        provider = None
        if all(checks.values()):
            group = case.get('conversation', uuid4().hex)
            payload = {'user_input': case['question'], 'session_id': sessions.setdefault(group, 'web-' + uuid4().hex),
                       'request_id': uuid4().hex}
            if case.get('selected'):
                payload['document_ids'] = [case['document_id']]
            response = request('POST', '/v1/chat', payload)
            checks.update(grade(case, response))
            provider = response.get('provider_status')
            after = request('GET', path, None)
            checks['source_stable'] = (after.get('status') == 'Aktif' and
                                       after.get('version_id') == before.get('version_id'))
        results.append({'id': case['id'], 'checks': checks, 'passed': all(checks.values()),
                        'provider_status': provider, 'elapsed_ms': round((time.monotonic() - start) * 1000)})
    same_build = request('GET', '/health', None).get('build_id') == build
    return {'transport': 'LIVE_HTTP', 'build_id': build, 'expected_build_checked': bool(expected_build),
            'build_stable': same_build, 'native_embedding': 'NOT_ATTESTED',
            'passed': same_build and all(r['passed'] for r in results),
            'passed_cases': sum(r['passed'] for r in results), 'total_cases': len(results), 'cases': results}


def http_client(base, token):
    url = urlsplit(base)
    if (url.scheme != 'http' or url.hostname not in ('127.0.0.1', 'localhost', '::1')
            or url.username or url.password or url.path not in ('', '/') or url.query or url.fragment):
        raise ValueError('Use a local loopback HTTP origin')
    opener = build_opener(ProxyHandler({}), NoRedirect())
    def request(method, path, payload):
        req = Request(base.rstrip('/') + path, method=method,
                      data=None if payload is None else json.dumps(payload).encode(),
                      headers={'X-Admin-Token': token, 'Content-Type': 'application/json'})
        with opener.open(req, timeout=180) as response:
            return json.load(response)
    return request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', required=True)
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    parser.add_argument('--expected-build-id')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    try:
        token = os.environ.get('NUSANTARA_ADMIN_TOKEN')
        if not token:
            raise ValueError('Set NUSANTARA_ADMIN_TOKEN in local environment')
        cases = json.loads(Path(args.cases).read_text(encoding='utf-8'))
        report = evaluate(cases, http_client(args.base_url, token), args.expected_build_id)
        destination = Path(args.output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(destination.name + '.' + uuid4().hex + '.tmp')
        temporary.write_text(json.dumps(report, indent=2), encoding='utf-8')
        temporary.replace(destination)
        print(f"Passed {report['passed_cases']}/{report['total_cases']}; build stable={report['build_stable']}")
        return 0 if report['passed'] else 1
    except Exception as error:
        # Exception bodies/URLs may contain source data. Never echo them.
        print('Evaluation stopped: ' + type(error).__name__, file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
