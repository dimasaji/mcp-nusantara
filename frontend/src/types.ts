export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt: string;
  citations?: Citation[];
  mode?: string;
  intent?: string;
  latencyMs?: number;
  error?: boolean;
}

export interface Citation {
  title: string;
  source_file: string;
  page_no?: number | null;
  document_id?: string;
  service?: string;
}

export interface ChatResponse {
  status: string;
  answer: string;
  answer_mode: string;
  session_id: string;
  intent: any;
  context: any;
  knowledge: { count: number; items: any[] };
  verification: { citation_valid: boolean; evidence_count: number; verified: boolean; issues: string[] };
  processing_status: string;
  latency_ms: number;
}

export interface Session {
  id: string;
  name: string;
  updatedAt: string;
}
