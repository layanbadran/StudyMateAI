import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { Message } from "../types";
import SourceList from "./SourceList";

const EXAMPLES = [
  "Summarize the main ideas in my notes",
  "What are the key definitions I should memorize?",
  "Explain the most difficult concept in simple words",
];

// Turns "[1]" markers in the answer into small numbered badges.
function AnswerText({ text }: { text: string }) {
  const parts = text.split(/(\[\d+\])/g);
  return (
    <p dir="auto" className="whitespace-pre-wrap leading-relaxed">
      {parts.map((part, i) =>
        /^\[\d+\]$/.test(part) ? (
          <span key={i} className="mx-0.5 rounded bg-ink px-1.5 py-0.5 text-xs font-semibold text-marker">
            {part.slice(1, -1)}
          </span>
        ) : (
          <span key={i}>{part}</span>
        )
      )}
    </p>
  );
}

export default function Chat({ hasDocuments, canAsk }: { hasDocuments: boolean; canAsk: boolean }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, busy]);

  async function send(text: string) {
    const q = text.trim();
    if (!q || busy) return;
    setQuestion("");
    setMessages((m) => [...m, { id: crypto.randomUUID(), role: "user", text: q }]);
    setBusy(true);
    try {
      const res = await api.ask(q);
      setMessages((m) => [
        ...m,
        { id: crypto.randomUUID(), role: "assistant", text: res.answer, sources: res.sources, grounded: res.grounded },
      ]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        { id: crypto.randomUUID(), role: "error", text: err instanceof Error ? err.message : "Something went wrong." },
      ]);
    } finally {
      setBusy(false);
    }
  }

  const disabled = !hasDocuments || !canAsk;
  const placeholder = !hasDocuments
    ? "Upload a PDF to start asking questions"
    : !canAsk
    ? "Add your Anthropic API key to the backend to enable answers"
    : "Ask a question about your notes";

  return (
    <section aria-labelledby="chat-heading" className="flex h-[70vh] min-h-[480px] flex-col rounded-2xl border-2 border-ink bg-white">
      <h2 id="chat-heading" className="border-b-2 border-ink px-5 py-3 font-display text-xl font-extrabold">
        Ask your notes
      </h2>

      <div className="flex-1 space-y-4 overflow-y-auto p-5" aria-live="polite">
        {messages.length === 0 && (
          <div className="py-6">
            <p className="font-display text-2xl font-extrabold">
              {hasDocuments ? "What do you want to understand?" : "Start by adding a PDF"}
            </p>
            <p className="mt-2 max-w-md text-ink/80">
              {hasDocuments
                ? "Answers come only from your documents, with the page they were found on."
                : "Upload lecture notes on the left. Then ask questions about them here."}
            </p>
            {hasDocuments && canAsk && (
              <div className="mt-5 flex flex-wrap gap-2">
                {EXAMPLES.map((ex) => (
                  <button
                    key={ex}
                    onClick={() => setQuestion(ex)}
                    className="rounded-full border-2 border-ink bg-butter px-3 py-1.5 text-sm font-medium hover:bg-marker"
                  >
                    {ex}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {messages.map((m) =>
          m.role === "user" ? (
            <div key={m.id} className="flex justify-end">
              <p dir="auto" className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-sm bg-ink px-4 py-2.5 text-paper">
                {m.text}
              </p>
            </div>
          ) : m.role === "error" ? (
            <div key={m.id} role="alert" className="rounded-2xl border-2 border-ember bg-orange-50 px-4 py-3 text-ember">
              <p className="font-semibold">Couldn't get an answer</p>
              <p className="text-sm">{m.text}</p>
            </div>
          ) : (
            <div
              key={m.id}
              className={`max-w-[92%] rounded-2xl rounded-bl-sm border-2 px-4 py-3 ${
                m.grounded ? "border-ink bg-white" : "border-flame bg-butter"
              }`}
            >
              {!m.grounded && <p className="mb-1 text-sm font-semibold text-ember">Not found in your documents</p>}
              <AnswerText text={m.text} />
              {m.sources && <SourceList sources={m.sources} />}
            </div>
          )
        )}

        {busy && (
          <p role="status" className="flex items-center gap-2 text-sm font-medium">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-flame border-t-transparent motion-reduce:animate-none" />
            Searching your notes and writing an answer…
          </p>
        )}
        <div ref={endRef} />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(question);
        }}
        className="flex items-end gap-3 border-t-2 border-ink p-4"
      >
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send(question);
            }
          }}
          dir="auto"
          rows={2}
          maxLength={2000}
          disabled={disabled}
          placeholder={placeholder}
          aria-label="Your question"
          className="min-h-[3rem] flex-1 resize-none rounded-xl border-2 border-ink bg-paper px-3 py-2 disabled:cursor-not-allowed disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={disabled || busy || question.trim() === ""}
          className="rounded-xl border-2 border-ink bg-flame px-5 py-3 font-semibold shadow-[3px_3px_0_0_var(--color-ink)] disabled:cursor-not-allowed disabled:opacity-50"
        >
          Ask
        </button>
      </form>
    </section>
  );
}
