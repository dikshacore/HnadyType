"use client";

export function HandwritingPreview({ svgMarkup, loading }: { svgMarkup: string | null; loading: boolean }) {
  return (
    <div className="flex min-h-[400px] items-center justify-center rounded-lg border border-ink/10 bg-white p-6">
      {loading ? (
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-ink/20 border-t-ink" />
      ) : svgMarkup ? (
        <div className="w-full" dangerouslySetInnerHTML={{ __html: svgMarkup }} />
      ) : (
        <p className="text-sm text-ink/40">Your handwriting preview will appear here as you type.</p>
      )}
    </div>
  );
}
