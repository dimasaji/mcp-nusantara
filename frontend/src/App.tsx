import { useState, useEffect, useCallback } from 'react';
import type { Session, ChatMessage } from '@/types';
import {
  listSessions,
  loadMessages,
  saveMessages,
  newConversation,
  getActiveSessionId,
  updateSessionTouch,
} from '@/store';
import { SessionList } from './components/SessionList';
import { Chat } from './components/Chat';

export function App() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setSessions(listSessions());
    const id = getActiveSessionId();
    if (id) {
      setActiveId(id);
      setMessages(loadMessages(id));
    }
    setReady(true);
  }, []);

  const handleNew = useCallback(() => {
    const s = newConversation();
    setSessions((prev) => {
      const exists = prev.find((x) => x.id === s.id);
      if (exists) return prev;
      return [s, ...prev];
    });
    setActiveId(s.id);
    setMessages([]);
  }, []);

  const handleSelect = useCallback(
    (id: string) => {
      setActiveId(id);
      setMessages(loadMessages(id));
      updateSessionTouch(id);
    },
    [],
  );

  const handleMessagesChange = useCallback(
    (msgs: ChatMessage[]) => {
      setMessages(msgs);
      if (activeId) {
        saveMessages(activeId, msgs);
        updateSessionTouch(activeId);
      }
    },
    [activeId],
  );

  if (!ready) return null;

  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <span className="brand-mark">N</span>
          <span className="brand-name">Nusantara V1</span>
          <span className="badge">Smart ASN</span>
        </div>
        <div className="header-actions">
          <button className="btn ghost" title="Percakapan baru" onClick={handleNew}>
            + Baru
          </button>
        </div>
      </header>

      <div className="body">
        <aside className="sidebar">
          <SessionList
            sessions={sessions}
            activeId={activeId}
            onSelect={handleSelect}
            onNew={handleNew}
          />
        </aside>

        <main className="main">
          {!activeId ? (
            <div className="empty">
              <h1>Selamat datang di Nusantara V1</h1>
              <p>
                Smart ASN yang memahami pertanyaan, menemukan pengetahuan, dan
                menghasilkan jawaban yang akurat serta bersitasi.
              </p>
              <p className="hint">
                Mulai percakapan baru atau pilih percakapan dari sebelah kiri.
              </p>
              <button className="btn primary" onClick={handleNew}>
                Mulai percakapan
              </button>
            </div>
          ) : (
            <Chat
              sessionId={activeId}
              messages={messages}
              onMessagesChange={handleMessagesChange}
              onTouch={() => updateSessionTouch(activeId)}
            />
          )}
        </main>
      </div>
    </div>
  );
}
