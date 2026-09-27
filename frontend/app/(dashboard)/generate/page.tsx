"use client";

import { useEffect, useState } from "react";
import { generateHandwriting } from "@/lib/api";
import { HandwritingPreview } from "./components/HandwritingPreview";
import { ExportToolbar } from "./components/ExportToolbar";

const PROFILE_ID = typeof window !== "undefined" ? localStorage.getItem("profile_id") ?? "" : "";
const DEBOUNCE_MS = 400;

export default function GeneratePage() {
  const [text, setText] = useState("");
  const [svgMarkup, setSvgMarkup] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!text.trim()) {
      setSvgMarkup(null);
      return;
    }
    setLoading(true);
    setError(null);
    const timeout = setTimeout(async () => {
      try {
        const svg = await generateHandwriting(PROFILE_ID, text);
        setSvgMarkup(svg);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Couldn't generate a preview.");
      } finally {
        setLoading(false);
      }
    }, DEBOUNCE_MS);
    return () => clearTimeout(timeout);
  }, [text]);

  function handleExport(format: "png" | "pdf" | "svg") {
    // Wire this up to a dedicated download endpoint once PNG/PDF
    // rasterization is implemented server-side (see routers/generate.py).
    console.log(`Export as ${format} not wired up yet.`);
  }

  return (
    <div className="grid max-w-5xl grid-cols-2 gap-8">
      <div className="flex flex-col gap-3">
        <h1 className="text-2xl font-medium">Write something</h1>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Type or paste text here…"
          className="min-h-[300px] rounded-lg border border-ink/15 bg-white p-4 text-sm outline-none focus:border-ink/40"
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
      </div>

      <div className="flex flex-col gap-3">
        <ExportToolbar onExport={handleExport} disabled={!svgMarkup} />
        <HandwritingPreview svgMarkup={svgMarkup} loading={loading} />
      </div>
    </div>
  );
}
