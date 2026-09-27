"use client";

import type { Glyph } from "@/lib/api";
import { GlyphCard } from "./GlyphCard";

export function GlyphGrid({ glyphs, onConfirm, onFlag }: {
  glyphs: Glyph[];
  onConfirm: (glyphId: string) => void;
  onFlag: (glyphId: string) => void;
}) {
  const grouped = glyphs.reduce<Record<string, Glyph[]>>((acc, g) => {
    (acc[g.char_key] ??= []).push(g);
    return acc;
  }, {});

  return (
    <div className="flex flex-col gap-6">
      {Object.entries(grouped).map(([charKey, variants]) => (
        <div key={charKey}>
          <h3 className="mb-2 text-sm font-medium text-ink/70">{charKey}</h3>
          <div className="flex flex-wrap gap-3">
            {variants.map((g) => (
              <GlyphCard key={g.id} glyph={g} onConfirm={onConfirm} onFlag={onFlag} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
