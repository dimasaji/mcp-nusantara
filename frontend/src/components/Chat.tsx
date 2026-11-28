import { useState, useCallback } from 'react';
import type { ChatMessage, ChatResponse } from '@/types';
import { sendChat, citationItems } from '@/api';
import { MessageBubble } from './MessageBubble';
import { InputArea } from './InputArea';

interface ChatProps {
  sessionId: string;
  messages: ChatMessage[];
  onMessagesChange: (msgs: ChatMessage[]) => void;
  onTouch: () => void;
}

export function Chat({ sessionId, messages, onMessagesChange, onTouch }: ChatProps) {
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [streamText, setStreamText] = useState('');

  const abortRef = useState<AbortController | null>(null)[0];

  const stop = useCallback(() => {
    if (abortRef) abortRef.abort();
    setSending(false);
    setError(null);
  }, [abortRef]);

  const retry = useCallback(() => {
    setError(null);
    setSending(false);
  }, []);

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || sending) return;
    setError(null);
    setStreamText('');
    setSending(true);

    const userMsg: ChatMessage = {
      id: crypto.randomUUID?.() ?? Math.random().toString(36),
      role: 'user',
      content: text,
      createdAt: new Date().toISOString(),
    };
    const next = [...messages, userMsg];
    onMessagesChange(next);
    onTouch();
    setInput('');

    const controller = new AbortController();
    try {
      const data: ChatResponse = await sendChat(text, sessionId, {
        signal: controller.signal,
        onDelta: (t: string) => setStreamText((prev) => prev + t),
      });

      const citations = citationItems(data.knowledge.items ?? []);
      const assistantMsg: ChatMessage = {
        id: crypto.randomUUID?.() ?? Math.random().toString(36),
        role: 'assistant',
        content: data.answer,
        createdAt: new Date().toISOString(),
        citations,
        mode: data.answer_mode,
        intent: data.intent?.intent ?? null,
        latencyMs: data.latency_ms,
      };
      onMessagesChange([...next, assistantMsg]);
      onTouch();
    } catch (err: any) {
      setError(err.message ?? 'Terjadi kesalahan saat memproses pertanyaan.');
      const failMsg: ChatMessage = {
        id: crypto.randomUUID?.() ?? Math.random().toString(36),
        role: 'assistant',
        content: err.message ?? 'Terjadi kesalahan saat memproses pertanyaan.',
        createdAt: new Date().toISOString(),
        error: true,
      };
      onMessagesChange([...next, failMsg]);
      onTouch();
    } finally {
      setSending(false);
    }
  }, [input, sending, messages, sessionId, onMessagesChange, onTouch]);

  return (
    <div className="chat">
      <div className="messages" ref={undefined}>
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} />
        ))}
        {streamText && !sending ? (
          <MessageBubble
            key="streaming"
            message={{
              id: 'streaming',
              role: 'assistant',
              content: streamText,
              createdAt: new Date().toISOString(),
            }}
          />
        ) : null}
        {error && sending ? (
          <div className="alert error">{error}</div>
        ) : null}
      </div>
      <InputArea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onSend={handleSend}
        disabled={sending}
        onStop={stop}
        onRetry={retry}
      />
    </div>
  );
}
