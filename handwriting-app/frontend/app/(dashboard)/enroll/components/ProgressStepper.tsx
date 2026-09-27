export function ProgressStepper({ current, total }: { current: number; total: number }) {
  return (
    <div className="mb-8 flex items-center gap-2">
      {Array.from({ length: total }).map((_, i) => (
        <div key={i} className="flex items-center gap-2">
          <div
            className={`flex h-8 w-8 items-center justify-center rounded-full text-sm ${
              i < current
                ? "bg-ink text-white"
                : i === current
                ? "border-2 border-ink text-ink"
                : "border border-ink/20 text-ink/40"
            }`}
          >
            {i + 1}
          </div>
          {i < total - 1 && <div className={`h-px w-10 ${i < current ? "bg-ink" : "bg-ink/15"}`} />}
        </div>
      ))}
      <span className="ml-3 text-sm text-ink/60">
        Sheet {Math.min(current + 1, total)} of {total}
      </span>
    </div>
  );
}
