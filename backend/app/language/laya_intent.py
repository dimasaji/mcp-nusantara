"""Optional loopback Laya client. Outputs retrieval hints, never policy decisions."""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
import re
import time

import httpx


SECTION_TERMS = {
    'persyaratan': 'persyaratan dokumen berkas yang diperlukan',
    'prosedur': 'prosedur alur tahapan langkah pelayanan',
    'durasi': 'waktu penyelesaian durasi hari kerja',
    'kanal': 'kanal pengajuan daring online loket',
    'lainnya': '',
}
QUESTION = {'intent': {
    'type': 'choice',
    'instructions': ('Classify only the CURRENT user question about a public service. '
        'Use conversation context to interpret follow-ups, not to override the current question. '
        'Respect negation. Select lainnya for unclear, multiple equally requested aspects, '
        'unrelated questions or instructions to execute/approve. Do not identify a service or assert facts.'),
    'criteria': {
        'persyaratan': 'Required documents or conditions: what must be brought or prepared; syarat, berkas.',
        'prosedur': 'Sequence of steps or process to follow; prosedur, alur, tahapan.',
        'durasi': 'How long processing takes or when it finishes; lama, waktu penyelesaian.',
        'kanal': 'Where or by what channel to apply, online, website, in person; kanal pengajuan.',
        'lainnya': 'Ambiguous, several equally requested aspects, unrelated, approval/execution commands, other.',
    },
}}


def hint_eligible(text):
    """Abstain on known difficult/out-of-scope forms; leave the existing path in charge."""
    if re.search(r"\b(?:tidak|bukan|jangan|nggak|ngga|gak|not|never|without|don't|approve|execute|execution|pass|jalankan|hapus|setujui)\b", text, re.I):
        return False
    aspects = [r'\b(?:syarat|persyaratan|berkas|documents|paperwork)\b',
        r'\b(?:prosedur|tahapan|langkah|steps)\b',
        r'\b(?:lama|durasi|processing time|how long)\b',
        r'\b(?:kanal|channel|online|loket)\b']
    return sum(bool(re.search(pattern, text, re.I)) for pattern in aspects) < 2


def intent_request(text, service_context=None, recent_turns=None):
    context = service_context or {}
    turns = [{'role': item.get('role'), 'content': str(item.get('content', ''))[-600:]}
             for item in (recent_turns or [])[-4:] if item.get('role') in {'user', 'assistant'}]
    return {'model': 'multilingual', 'state': json.dumps({
        'previous_service': {key: str(context[key])[:200] for key in ('topic', 'document_id') if key in context},
        'recent_turns': turns, 'current_question': text,
    }, ensure_ascii=False), 'questions': QUESTION, 'max_len': 1024, 'head_max_len': 256}


@dataclass(frozen=True)
class LayaIntentHint:
    status: str
    label: str | None = None
    probability: float = 0.0
    margin: float = 0.0
    terms: str = ''
    latency_ms: float = 0.0


class LayaIntentAdapter:
    def __init__(self, configuration, *, transport=None):
        self.configuration = configuration
        # No socket, torch import, checkpoint or subprocess in the backend.
        self.client = httpx.Client(base_url=configuration.base_url, timeout=configuration.timeout_s,
            trust_env=False, follow_redirects=False, transport=transport,
            limits=httpx.Limits(max_connections=2, max_keepalive_connections=2)) if configuration.enabled else None

    def classify(self, text, service_context=None, recent_turns=None):
        if self.client is None:
            return LayaIntentHint('DISABLED')
        started = time.perf_counter()
        try:
            # A long current turn must not be silently truncated into a different question.
            if not isinstance(text, str) or not text.strip() or len(text) > 1600:
                return LayaIntentHint('INPUT_UNSUPPORTED')
            if not hint_eligible(text):
                return LayaIntentHint('COMPLEX_OR_OUT_OF_SCOPE')
            response = self.client.post('/v1/systemone', json=intent_request(text, service_context, recent_turns))
            response.raise_for_status()
            body = response.json()
            if not isinstance(body, dict) or not isinstance(body.get('usage', {}), dict):
                raise ValueError('INVALID_INTENT_RESPONSE')
            if body.get('usage', {}).get('truncated'):
                return LayaIntentHint('TRUNCATED')
            answer = body['answers']['intent']
            probabilities = answer['probabilities']
            if answer['type'] != 'choice' or set(probabilities) != set(SECTION_TERMS):
                raise ValueError('INVALID_INTENT_RESPONSE')
            if any(isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p) or not 0 <= p <= 1
                   for p in probabilities.values()):
                raise ValueError('INVALID_PROBABILITIES')
            if abs(sum(probabilities.values()) - 1) > .01:
                raise ValueError('INVALID_PROBABILITIES')
            ranked = sorted(probabilities, key=probabilities.get, reverse=True)
            label = answer['choice']
            if label != ranked[0]:
                raise ValueError('INCONSISTENT_CHOICE')
            probability, margin = probabilities[label], probabilities[label] - probabilities[ranked[1]]
            elapsed = (time.perf_counter() - started) * 1000
            accepted = (label != 'lainnya' and probability >= self.configuration.min_probability
                        and margin >= self.configuration.min_margin)
            return LayaIntentHint('ACCEPTED' if accepted else 'ABSTAIN', label, probability, margin,
                SECTION_TERMS[label] if accepted else '', elapsed)
        except httpx.TimeoutException:
            status = 'TIMEOUT'
        except httpx.HTTPError:
            status = 'UNAVAILABLE'
        except (KeyError, TypeError, ValueError):
            status = 'INVALID_RESPONSE'
        return LayaIntentHint(status, latency_ms=(time.perf_counter() - started) * 1000)

    def close(self):
        if self.client is not None:
            self.client.close()
