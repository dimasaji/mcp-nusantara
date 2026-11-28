import type { Session } from '@/types';
import { deleteSession } from '@/store';

interface SessionListProps {
  sessions: Session[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
}

export function SessionList({
  sessions,
  activeId,
  onSelect,
  onNew,
}: SessionListProps) {
  return (
    <div className="panel sessions">
      <div className="panel-title">Percakapan</div>
      <button className="btn primary small" onClick={onNew}>
        Percakapan baru
      </button>
      <ul className="session-list">
        {sessions.map((s) => {
          const active = s.id === activeId;
          return (
            <li key={s.id} className={active ? 'session active' : 'session'}>
              <button
                className="session-name"
                onClick={() => onSelect(s.id)}
                title={s.name}
              >
                {s.name}
              </button>
              <button
                className="session-delete"
                title="Hapus"
                onClick={(e) => {
                  e.stopPropagation();
                  deleteSession(s.id);
                }}
              >
                ×
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
