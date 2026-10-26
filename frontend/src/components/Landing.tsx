import Logo from "./Logo";

export default function Landing({ onStart }: { onStart: () => void }) {
  return (
    <div>
      {/* Hero */}
      <section className="bg-marker">
        <div className="mx-auto max-w-6xl px-5 pb-16 pt-5 sm:px-8">
          <nav className="flex items-center justify-between">
            <Logo />
            <button
              onClick={onStart}
              className="rounded-lg border-2 border-ink px-4 py-2 text-sm font-semibold hover:bg-ink hover:text-marker"
            >
              Open workspace
            </button>
          </nav>

          <div className="mt-14 grid items-center gap-12 lg:grid-cols-[1.1fr_1fr]">
            <div>
              <h1 className="font-display text-5xl font-extrabold leading-[1.05] tracking-tight sm:text-6xl">
                Ask your lecture notes. Get answers with page numbers.
              </h1>
              <p className="mt-6 max-w-xl text-lg leading-relaxed">
                Upload your own PDFs and ask questions in plain language. StudyMate AI finds the
                relevant passages, answers from them only, and shows exactly where each answer
                came from.
              </p>
              <div className="mt-8 flex flex-wrap items-center gap-4">
                <button
                  onClick={onStart}
                  className="rounded-xl border-2 border-ink bg-flame px-7 py-3.5 text-lg font-semibold text-ink shadow-[5px_5px_0_0_var(--color-ink)] transition active:translate-x-[3px] active:translate-y-[3px] active:shadow-[2px_2px_0_0_var(--color-ink)]"
                >
                  Upload your first PDF
                </button>
                <span className="text-sm font-medium">Works with English and Arabic notes</span>
              </div>
            </div>

            {/* Illustration of the product (static example, not live data) */}
            <div className="relative" aria-hidden="true">
              <div className="rounded-2xl border-2 border-ink bg-paper p-6 shadow-[8px_8px_0_0_var(--color-ink)]">
                <p className="text-xs font-semibold text-ember">Example</p>
                <p className="mt-3 rounded-xl bg-butter px-4 py-3 text-sm font-medium">
                  What does the second law say about entropy?
                </p>
                <p className="mt-4 text-sm leading-relaxed">
                  In an isolated system, total entropy never decreases.{" "}
                  <span className="marker font-semibold">Entropy measures disorder</span>, and
                  spontaneous processes move toward higher entropy{" "}
                  <span className="rounded bg-ink px-1.5 py-0.5 text-xs font-semibold text-marker">
                    1
                  </span>
                  .
                </p>
                <div className="mt-4 flex items-center gap-2 border-t-2 border-dashed border-ink/25 pt-4 text-sm">
                  <span className="rounded bg-ink px-1.5 py-0.5 text-xs font-semibold text-marker">
                    1
                  </span>
                  <span className="font-semibold">Thermodynamics-Lecture-4.pdf</span>
                  <span className="text-ink/70">page 12</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="mx-auto max-w-6xl px-5 py-16 sm:px-8">
        <h2 className="font-display text-3xl font-extrabold tracking-tight">How it works</h2>
        <ol className="mt-8 grid gap-6 md:grid-cols-3">
          {[
            ["1", "Upload your PDFs", "Add lecture notes, slides exported as PDF, or readings. Each file stays in your own private space."],
            ["2", "Ask a question", "Type it the way you'd ask a classmate. The app searches by meaning, not just exact words."],
            ["3", "Check the sources", "Every answer lists the file and page it came from. If your notes don't cover it, the app says so."],
          ].map(([n, title, text]) => (
            <li key={n} className="rounded-2xl border-2 border-ink bg-butter p-6">
              <span className="grid h-8 w-8 place-items-center rounded-full bg-ink font-display font-extrabold text-marker">
                {n}
              </span>
              <h3 className="mt-4 font-display text-xl font-extrabold">{title}</h3>
              <p className="mt-2 leading-relaxed">{text}</p>
            </li>
          ))}
        </ol>

        <div className="mt-10 rounded-2xl border-2 border-ink p-6">
          <h3 className="font-display text-xl font-extrabold">Your files stay yours</h3>
          <p className="mt-2 max-w-3xl leading-relaxed">
            The PDF itself is not saved. Only its text, split into small pieces, is kept so it can
            be searched. You can remove any document from the workspace at any time and its text
            is deleted with it.
          </p>
        </div>
      </section>
    </div>
  );
}
