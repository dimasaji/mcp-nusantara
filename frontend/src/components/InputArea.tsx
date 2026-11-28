interface InputAreaProps {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  onSend: () => void;
  disabled: boolean;
  onRetry?: () => void;
  onStop?: () => void;
}

export function InputArea({
  value,
  onChange,
  onSend,
  disabled,
  onRetry,
  onStop,
}: InputAreaProps) {
  return (
    <div className="input-area">
      <div className="row">
        <textarea
          className="input"
          placeholder="Ketik pertanyaan Anda (Contoh: persyaratan pembuatan KTP-el)..."
          value={value}
          onChange={onChange}
          disabled={disabled}
          rows={1}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              onSend();
            }
          }}
        />
        <div className="controls">
          {disabled && onStop ? (
            <button className="btn stop" title="Hentikan" onClick={onStop}>
              Hentikan
            </button>
          ) : disabled && onRetry ? (
            <button className="btn retry" title="Coba lagi" onClick={onRetry}>
              Coba lagi
            </button>
          ) : (
            <button className="btn primary" title="Kirim" onClick={onSend} disabled={disabled}>
              Kirim
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
