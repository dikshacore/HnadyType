"use client";

export function ExportToolbar({ onExport, disabled }: { onExport: (format: "png" | "pdf" | "svg") => void; disabled: boolean }) {
  return (
    <div className="flex items-center gap-2 border-b border-ink/10 pb-3">
      {/* Reserved for later: ink color picker, template selector, image insertion */}
      <span className="text-sm text-ink/50">Export as:</span>
      {(["png", "pdf", "svg"] as const).map((format) => (
        <button
          key={format}
          onClick={() => onExport(format)}
          disabled={disabled}
          className="rounded-lg border border-ink/20 px-3 py-1.5 text-sm uppercase disabled:opacity-40"
        >
          {format}
        </button>
      ))}
    </div>
  );
}
