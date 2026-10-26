export interface DocumentInfo {
  doc_id: string;
  filename: string;
  pages: number;
  chunks: number;
  uploaded_at: string;
}

export interface Source {
  id: number;
  filename: string;
  page: number;
  excerpt: string;
  score: number;
}

export interface ChatAnswer {
  answer: string;
  sources: Source[];
  grounded: boolean;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "error";
  text: string;
  sources?: Source[];
  grounded?: boolean;
}

export interface Health {
  status: string;
  anthropic_configured: boolean;
  max_upload_mb: number;
}
