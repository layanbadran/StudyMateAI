import { useRef, useState } from "react";
import { api } from "../api";
import type { DocumentInfo } from "../types";

interface Props {
  documents: DocumentInfo[];
  loading: boolean;
  maxMb: number;
  onChanged: () => Promise<void>;
}

export default function UploadPanel({ documents, loading, maxMb, onChanged }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState<string | null>(null);
  const [errors, setErrors] = useState<string[]>([]);

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    setErrors([]);
    const newErrors: string[] = [];

    for (const file of Array.from(files)) {
      // Quick checks in the browser. The server checks again, so these are only for speed.
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        newErrors.push(`${file.name}: only PDF files are supported.`);
        continue;
      }
      if (file.size > maxMb * 1024 * 1024) {
        newErrors.push(`${file.name}: larger than the ${maxMb} MB limit.`);
        continue;
      }
      setUploading(file.name);
      try {
        await api.uploadDocument(file);
        await onChanged();
      } catch (err) {
        newErrors.push(`${file.name}: ${err instanceof Error ? err.message : "upload failed."}`);
      }
    }
    setUploading(null);
    setErrors(newErrors);
    if (inputRef.current) inputRef.current.value = "";
  }

  async function remove(doc: DocumentInfo) {
    if (!window.confirm(`Remove "${doc.filename}"? Its text will be deleted.`)) return;
    try {
      await api.deleteDocument(doc.doc_id);
      await onChanged();
    } catch (err) {
      setErrors([err instanceof Error ? err.message : "Could not remove the document."]);
    }
  }

  return (
    <section aria-labelledby="docs-heading" className="rounded-2xl border-2 border-ink bg-white p-5">
      <h2 id="docs-heading" className="font-display text-xl font-extrabold">
        Your documents
      </h2>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          handleFiles(e.dataTransfer.files);
        }}
        className={`mt-4 rounded-xl border-2 border-dashed border-ink p-5 text-center transition ${
          dragging ? "bg-marker" : "bg-butter"
        }`}
      >
        <p className="font-semibold">Drop PDFs here</p>
        <p className="mt-1 text-sm text-ink/75">PDF only, up to {maxMb} MB each</p>
        <button
          onClick={() => inputRef.current?.click()}
          disabled={uploading !== null}
          className="mt-3 rounded-lg border-2 border-ink bg-flame px-4 py-2 text-sm font-semibold shadow-[3px_3px_0_0_var(--color-ink)] disabled:opacity-60"
        >
          Choose files
        </button>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          multiple
          className="sr-only"
          aria-label="Choose PDF files"
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      {uploading && (
        <p role="status" className="mt-3 flex items-center gap-2 text-sm font-medium">
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-ink border-t-transparent motion-reduce:animate-none" />
          Reading and indexing {uploading}. The first upload can take a minute while the search model loads.
        </p>
      )}

      {errors.length > 0 && (
        <ul role="alert" className="mt-3 space-y-1 rounded-lg border-2 border-ember bg-orange-50 p-3 text-sm text-ember">
          {errors.map((e, i) => (
            <li key={i}>{e}</li>
          ))}
        </ul>
      )}

      <ul className="mt-4 space-y-2">
        {loading && <li className="text-sm text-ink/70">Loading your documents…</li>}
        {!loading && documents.length === 0 && (
          <li className="text-sm text-ink/70">
            No documents yet. Upload a PDF to start asking questions.
          </li>
        )}
        {documents.map((doc) => (
          <li key={doc.doc_id} className="flex items-center justify-between gap-3 rounded-lg border-2 border-ink/20 px-3 py-2">
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold" title={doc.filename}>
                {doc.filename}
              </p>
              <p className="text-xs text-ink/70">
                {doc.pages} {doc.pages === 1 ? "page" : "pages"} · {doc.chunks} passages
              </p>
            </div>
            <button
              onClick={() => remove(doc)}
              className="shrink-0 rounded-md px-2 py-1 text-sm font-semibold text-ember hover:bg-orange-100"
              aria-label={`Remove ${doc.filename}`}
            >
              Remove
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
