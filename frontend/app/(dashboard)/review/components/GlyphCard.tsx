"use client";

import { useState } from "react";
import type { Glyph } from "@/lib/api";

export function GlyphCard({ glyph, onConfirm, onFlag }: {
  glyph: Glyph;
  onConfirm: (glyphId: string) => void;
  onFlag: (glyphId: string) => void;
}) {
  const [dismissed, setDismissed] = useState(false);
  if (dismissed) return null;

  return (
    <div
      className={`flex flex-col items-center gap-2 rounded-lg border p-3 ${
        glyph.needs_review ? "border-amber-300 bg-amber-50" : "border-ink/10 bg-white"
      }`}
    >
      <div className="flex h-16 w-16 items-center justify-center rounded bg-ink/5 text-xs text-ink/40">
        {/* Real version renders raster_key or an <img src={svgUrl} /> here */}
        {glyph.char_key}
      </div>
      <span className="text-xs text-ink/60">{glyph.char_key}</span>
      {glyph.needs_review && <span className="text-xs text-amber-700">Needs a look</span>}
      <div className="flex gap-1">
        <button
          onClick={() => { onConfirm(glyph.id); setDismissed(true); }}
          className="rounded bg-ink px-2 py-1 text-xs text-white"
        >
          Looks good
        </button>
        <button
          onClick={() => onFlag(glyph.id)}
          className="rounded border border-ink/20 px-2 py-1 text-xs"
        >
          Re-crop
        </button>
      </div>
    </div>
  );
}
