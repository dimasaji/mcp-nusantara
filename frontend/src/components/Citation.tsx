import type { Citation } from '@/types';

interface CitationProps {
  citations: Citation[];
}

export function CitationList({ citations }: CitationProps) {
  if (!citations || citations.length === 0) return null;
  return (
    <div className="card citations">
      <div className="card-title">Sumber / Sitasi</div>
      <ul>
        {citations.map((c, i) => (
          <li key={`${c.document_id}-${i}`}>
            {c.title}{' '}
            {c.source_file && ` (${c.source_file})`}
            {c.page_no != null ? ` — halaman ${c.page_no}` : ''}
          </li>
        ))}
      </ul>
    </div>
  );
}
