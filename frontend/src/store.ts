import type { Session, ChatMessage } from '@/types';

const SESSIONS_KEY = 'nusantara_sessions';
const MESSAGES_PREFIX = 'nusantara_msgs_';
const ACTIVE_SESSION_KEY = 'nusantara_active_session';

export function listSessions(): Session[] {
  if (typeof localStorage === 'undefined') return [];
  try {
    const raw = localStorage.getItem(SESSIONS_KEY);
    if (!raw) return [];
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

export function saveSessions(sessions: Session[]): void {
  if (typeof localStorage === 'undefined') return;
  localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions));
}

export function getActiveSessionId(): string | null {
  if (typeof localStorage === 'undefined') return null;
  return localStorage.getItem(ACTIVE_SESSION_KEY);
}

export function setActiveSessionId(id: string | null): void {
  if (typeof localStorage === 'undefined') return;
  if (id) localStorage.setItem(ACTIVE_SESSION_KEY, id);
  else localStorage.removeItem(ACTIVE_SESSION_KEY);
}

export function createSession(name: string): Session {
  const now = new Date().toISOString();
  const session: Session = {
    id: crypto.randomUUID?.() ?? Math.random().toString(36).slice(2),
    name,
    updatedAt: now,
  };
  const sessions = [session, ...listSessions()].slice(0, 50);
  saveSessions(sessions);
  setActiveSessionId(session.id);
  return session;
}

export function updateSessionTouch(id: string): void {
  const sessions = listSessions().map((s) =>
    s.id === id ? { ...s, updatedAt: new Date().toISOString(), name: s.name } : s,
  );
  saveSessions(sessions);
  setActiveSessionId(id);
}

export function deleteSession(id: string): void {
  const sessions = listSessions().filter((s) => s.id !== id);
  saveSessions(sessions);
  const active = getActiveSessionId();
  if (active === id) {
    setActiveSessionId(sessions.length > 0 ? sessions[0].id : null);
    if (sessions.length === 0) {
      localStorage.removeItem(MESSAGES_PREFIX + id);
    }
  }
  localStorage.removeItem(MESSAGES_PREFIX + id);
}

export function loadMessages(sessionId: string): ChatMessage[] {
  if (typeof localStorage === 'undefined') return [];
  try {
    const raw = localStorage.getItem(MESSAGES_PREFIX + sessionId);
    if (!raw) return [];
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

export function saveMessages(sessionId: string, messages: ChatMessage[]): void {
  if (typeof localStorage === 'undefined') return;
  localStorage.setItem(MESSAGES_PREFIX + sessionId, JSON.stringify(messages));
}

export function newConversation(): Session {
  return createSession('Percakapan baru ' + new Date().toLocaleDateString('id-ID'));
}
