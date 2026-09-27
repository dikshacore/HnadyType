"use client";

import { useState } from "react";
import { CameraCapture } from "./CameraCapture";

/**
 * Lightweight client-side check before upload: verifies the photo is
 * reasonably sized/lit so obviously-bad captures are caught early instead
 * of round-tripping to the server. Real corner/fiducial detection (see
 * backend preprocessing.find_fiducial_corners) needs actual CV, which is
 * heavier than we want to ship to the browser today -- swap this for an
 * opencv.js-based check once it's worth the bundle size.
 */
function quickQualityCheck(file: File): Promise<{ ok: boolean; message?: string }> {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      if (img.width < 800 || img.height < 800) {
        resolve({ ok: false, message: "Photo resolution looks low -- try moving closer or using a better camera." });
      } else {
        resolve({ ok: true });
      }
      URL.revokeObjectURL(img.src);
    };
    img.onerror = () => resolve({ ok: false, message: "Couldn't read that image -- try a different file." });
    img.src = URL.createObjectURL(file);
  });
}

interface Props {
  sheetIndex: number;
  onUpload: (file: File) => Promise<void>;
  uploading: boolean;
}

export function SheetUpload({ sheetIndex, onUpload, uploading }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);

  async function handleFile(selected: File) {
    const check = await quickQualityCheck(selected);
    setWarning(check.ok ? null : check.message ?? null);
    setFile(selected);
    setPreviewUrl(URL.createObjectURL(selected));
  }

  return (
    <div className="flex flex-col gap-4">
      <a
        href={`/enrollment-sheets/sheet_${sheetIndex + 1}.pdf`}
        target="_blank"
        rel="noreferrer"
        className="text-sm font-medium text-ink underline underline-offset-2"
      >
        Download sheet {sheetIndex + 1} PDF to print
      </a>

      {previewUrl ? (
        <div className="flex flex-col gap-3">
          <img src={previewUrl} alt="Sheet preview" className="max-h-96 rounded-lg border border-ink/10" />
          {warning && <p className="text-sm text-amber-600">{warning}</p>}
          <div className="flex gap-2">
            <button
              onClick={() => file && onUpload(file)}
              disabled={uploading}
              className="rounded-lg bg-ink px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              {uploading ? "Uploading…" : "Use this photo"}
            </button>
            <button
              onClick={() => { setFile(null); setPreviewUrl(null); }}
              className="rounded-lg border border-ink/20 px-4 py-2 text-sm"
            >
              Retake
            </button>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          <label className="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-ink/20 px-6 py-10 text-center hover:border-ink/40">
            <span className="text-sm text-ink/70">Drag a photo here, or click to choose a file</span>
            <input
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
            />
          </label>
          <CameraCapture onCapture={handleFile} />
        </div>
      )}
    </div>
  );
}
