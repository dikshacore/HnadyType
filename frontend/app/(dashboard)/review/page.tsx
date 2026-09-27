"use client";

import useSWR from "swr";
import { listGlyphs, reviewGlyph } from "@/lib/api";
import { GlyphGrid } from "./components/GlyphGrid";

const PROFILE_ID = typeof window !== "undefined" ? localStorage.getItem("profile_id") ?? "" : "";

export default function ReviewPage() {
  const { data: glyphs, mutate, isLoading } = useSWR(
    PROFILE_ID ? ["glyphs", PROFILE_ID] : null,
    () => listGlyphs(PROFILE_ID)
  );

  async function handleConfirm(glyphId: string) {
    await reviewGlyph(glyphId, true);
    mutate();
  }

  async function handleFlag(glyphId: string) {
    // In the full version this opens a re-crop modal; for now it just
    // marks the glyph unconfirmed so it stays visible in the flagged list.
    await reviewGlyph(glyphId, false);
    mutate();
  }

  const needsReviewCount = glyphs?.filter((g) => g.needs_review && !g.user_confirmed).length ?? 0;

  return (
    <div className="max-w-4xl">
      <h1 className="mb-2 text-2xl font-medium">Review your handwriting</h1>
      <p className="mb-6 text-sm text-ink/60">
        {needsReviewCount > 0
          ? `${needsReviewCount} letters could use a second look before you generate text.`
          : "Everything looks captured well. You're ready to generate text."}
      </p>

      {isLoading && <p className="text-sm text-ink/50">Loading…</p>}
      {glyphs && <GlyphGrid glyphs={glyphs} onConfirm={handleConfirm} onFlag={handleFlag} />}
    </div>
  );
}
