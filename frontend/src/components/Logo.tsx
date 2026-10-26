export default function Logo({ onClick }: { onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-2.5 rounded-lg font-display text-xl font-extrabold tracking-tight"
      aria-label="StudyMate AI home"
    >
      <span className="grid h-9 w-9 place-items-center rounded-lg bg-flame text-ink shadow-[3px_3px_0_0_var(--color-ink)]">
        S
      </span>
      StudyMate AI
    </button>
  );
}
