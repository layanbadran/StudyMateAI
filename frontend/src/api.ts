import type { ChatAnswer, DocumentInfo, Health } from "./types";

// A random ID per browser. The backend uses it to keep each user's documents separate.
function getSessionId(): string {
  const key = "studymate_session";
  let id = localStorage.getItem(key);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(key, id);
  }
  return id;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      ...options,
      headers: { ...options.headers, "X-Session-ID": getSessionId() },
    });
  } catch {
    throw new Error(
      "Can't reach the StudyMate server. Make sure the backend is running on port 8000."
    );
  }

  if (!response.ok) {
    let message = `Something went wrong (status ${response.status}).`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") message = body.detail;
      else if (response.status === 422) message = "That request wasn't valid. Check your input.";
    } catch {
      /* the response had no JSON body */
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<Health>("/api/health"),

  listDocuments: async () =>
    (await request<{ documents: DocumentInfo[] }>("/api/documents")).documents,

  uploadDocument: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<DocumentInfo>("/api/documents", { method: "POST", body: form });
  },

  deleteDocument: (docId: string) =>
    request<{ deleted: string }>(`/api/documents/${docId}`, { method: "DELETE" }),

  ask: (question: string) =>
    request<ChatAnswer>("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    }),
};
