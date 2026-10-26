import type { Source } from "../types";

export default function SourceList({ sources }: { sources: Source[] }) {
  if (sources.length === 0) return null;
  return (
    <div className="mt-4 border-t-2 border-dashed border-ink/25 pt-3">
      <p className="text-sm font-semibold">Sources</p>
      <ul className="mt-2 space-y-2">
        {sources.map((s) => (
          <li key={s.id}>
            <details className="rounded-lg bg-butter px-3 py-2">
              <summary className="cursor-pointer text-sm font-medium">
                <span className="mr-2 rounded bg-ink px-1.5 py-0.5 text-xs font-semibold text-marker">
                  {s.id}
                </span>
                {s.filename}, page {s.page}
              </summary>
              <p dir="auto" className="mt-2 text-sm leading-relaxed text-ink/85">
                {s.excerpt}
                {s.excerpt.length >= 500 ? "…" : ""}
              </p>
            </details>
          </li>
        ))}
      </ul>
    </div>
  );
}
