import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import type { DocumentInfo, Health } from "./types";
import Chat from "./components/Chat";
import Landing from "./components/Landing";
import Logo from "./components/Logo";
import UploadPanel from "./components/UploadPanel";

export default function App() {
  const [view, setView] = useState<"landing" | "workspace">("landing");
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [health, setHealth] = useState<Health | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setDocuments(await api.listDocuments());
      setServerError(null);
    } catch (err) {
      setServerError(err instanceof Error ? err.message : "Could not load your documents.");
    } finally {
      setLoadingDocs(false);
    }
  }, []);

  useEffect(() => {
    if (view !== "workspace") return;
    refresh();
    api.health().then(setHealth).catch(() => setHealth(null));
  }, [view, refresh]);

  if (view === "landing") return <Landing onStart={() => setView("workspace")} />;

  return (
    <div className="min-h-screen">
      <header className="border-b-2 border-ink bg-marker">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-3 sm:px-8">
          <Logo onClick={() => setView("landing")} />
          <span className="hidden text-sm font-medium sm:block">Your private study workspace</span>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-4 px-5 py-6 sm:px-8">
        {serverError && (
          <div role="alert" className="rounded-xl border-2 border-ember bg-orange-50 px-4 py-3 text-ember">
            <p className="font-semibold">Server problem</p>
            <p className="text-sm">{serverError}</p>
          </div>
        )}
        {health && !health.anthropic_configured && (
          <div role="alert" className="rounded-xl border-2 border-flame bg-butter px-4 py-3">
            <p className="font-semibold">Answers are turned off</p>
            <p className="text-sm">
              The backend has no ANTHROPIC_API_KEY. Add it to <code>backend/.env</code> and restart
              the backend. You can still upload documents in the meantime.
            </p>
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
          <UploadPanel
            documents={documents}
            loading={loadingDocs}
            maxMb={health?.max_upload_mb ?? 20}
            onChanged={refresh}
          />
          <Chat
            hasDocuments={documents.length > 0}
            canAsk={health?.anthropic_configured ?? false}
          />
        </div>
      </main>
    </div>
  );
}
