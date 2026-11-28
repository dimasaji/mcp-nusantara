import type { ChatResponse, Citation } from '@/types';

const BACKEND_URL =
  import.meta.env.VITE_NUSANTARA_BACKEND_URL ||
  (typeof window !== 'undefined'
    ? window.location.origin
    : 'http://127.0.0.1:8021');

export function backendChatUrl(): string {
  return BACKEND_URL.replace(/\/$/, '') + '/v1/chat';
}

export interface ChatOptions {
  onDelta?: (text: string) => void;
  signal?: AbortSignal;
  timeoutMs?: number;
}

export async function sendChat(
  user_input: string,
  session_id: string,
  options: ChatOptions = {},
): Promise<ChatResponse> {
  const controller = new AbortController();
  const signal = options.signal ?? controller.signal;

  const timeoutMs = options.timeoutMs ?? 90000;
  let timer: ReturnType<typeof setTimeout> | undefined;
  const deadline = new Promise<never>((_, reject) => {
    timer = setTimeout(() => {
      reject(new Error(`Batas waktu ${Math.floor(timeoutMs / 1000)} detik tercapai.`));
      controller.abort();
    }, timeoutMs);
  });

  try {
    const response = await Promise.race([
      fetch(backendChatUrl(), {
        method: 'POST',
        credentials: 'omit',
        cache: 'no-store',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input: user_input, session_id }),
        signal,
      }),
      deadline,
    ]);

    if (!response.ok) {
      throw new Error(`Backend merespons ${response.status}.`);
    }

    const contentType = response.headers.get('content-type') ?? '';
    if (contentType.includes('application/x-ndjson')) {
      return readNdjson(response, options.onDelta);
    }
    const data = (await response.json()) as ChatResponse;
    return data;
  } finally {
    if (timer) clearTimeout(timer);
  }
}

async function readNdjson(
  response: Response,
  onDelta?: (text: string) => void,
): Promise<ChatResponse> {
  if (!response.body) throw new Error('Aliran jawaban tidak tersedia.');
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let finalAnswer = '';
  try {
    while (true) {
      const { done, value } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      const lines = buffer.split('\n');
      buffer = lines.pop() ?? '';
      for (const line of lines) {
        if (!line.trim()) continue;
        const event = JSON.parse(line) as {
          type: string;
          text?: string;
          answer?: unknown;
          message?: string;
        };
        if (event.type === 'error') {
          throw new Error(event.message ?? 'Chat gagal.');
        }
        if (event.type === 'final') {
          finalAnswer = String(event.answer ?? '');
        } else if (event.type === 'delta' && event.text && onDelta) {
          onDelta(event.text);
        }
      }
      if (done) break;
    }
  } finally {
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
  return {
    status: 'ok',
    answer: finalAnswer,
    answer_mode: 'stream',
    session_id: '',
    intent: {},
    context: {},
    knowledge: { count: 0, items: [] },
    verification: { citation_valid: true, evidence_count: 0, verified: true, issues: [] },
    processing_status: 'completed',
    latency_ms: 0,
  };
}

export function citationItems(items: any[]): Citation[] {
  const seen = new Set<string>();
  return items
    .filter((it) => {
      const key = `${it.document_id}|${it.chunk_id}|${it.page_no}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .map((it) => ({
      title: it.title ?? '-',
      source_file: it.source_file ?? '-',
      page_no: it.page_no ?? null,
      document_id: it.document_id,
      service: it.service,
    }));
}
