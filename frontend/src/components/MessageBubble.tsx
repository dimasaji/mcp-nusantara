import type { ChatMessage } from '@/types';
import { CitationList } from './Citation';

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const time = message.createdAt
    ? new Date(message.createdAt).toLocaleTimeString('id-ID', {
        hour: '2-digit',
        minute: '2-digit',
      })
    : '';
  return (
    <div className={`message ${isUser ? 'user' : 'assistant'}`}>
      <div className="bubble">
        <div className="content" style={{ whiteSpace: 'pre-wrap' }}>
          {message.content}
        </div>
        {!isUser && (
          <>
            {message.mode && (
              <span className="meta">
                Mode: {message.mode}&nbsp;•&nbsp;{message.latencyMs} ms
              </span>
            )}
            <CitationList citations={message.citations ?? []} />
            <div className="actions">
              <button
                className="icon-btn"
                title="Salin balasan"
                onClick={() => copy(message.content)}
              >
                Salin
              </button>
            </div>
          </>
        )}
      </div>
      <div className="meta-row">
        <span className="role">{isUser ? 'Anda' : 'Nusantara'}</span>
        <span className="time">{time}</span>
      </div>
    </div>
  );
}

function copy(text: string) {
  navigator.clipboard.writeText(text).catch(() => {});
}
