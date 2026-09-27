"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ProgressStepper } from "./components/ProgressStepper";
import { SheetUpload } from "./components/SheetUpload";
import { uploadSheet, listSheets, SheetStatus } from "@/lib/api";

const TOTAL_SHEETS = 3;

// TODO: replace with the real profile id once the dashboard/profile-select
// flow exists -- for a single-profile-per-account MVP this can come
// straight from the signup response instead.
const DEMO_PROFILE_ID = typeof window !== "undefined" ? localStorage.getItem("profile_id") ?? "" : "";

export default function EnrollPage() {
  const router = useRouter();
  const [currentSheet, setCurrentSheet] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleUpload(file: File) {
    setUploading(true);
    setError(null);
    try {
      await uploadSheet(DEMO_PROFILE_ID, currentSheet, file);
      if (currentSheet < TOTAL_SHEETS - 1) {
        setCurrentSheet((s) => s + 1);
      } else {
        await waitForProcessing();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed -- try again.");
    } finally {
      setUploading(false);
    }
  }

  async function waitForProcessing() {
    setProcessing(true);
    const poll = async (): Promise<void> => {
      const sheets: SheetStatus[] = await listSheets(DEMO_PROFILE_ID);
      const allDone = sheets.length === TOTAL_SHEETS && sheets.every((s) => s.status === "processed");
      const anyFailed = sheets.some((s) => s.status === "failed");

      if (anyFailed) {
        setError("Some sheets couldn't be processed. Check the review screen to see what needs a re-scan.");
        setProcessing(false);
        return;
      }
      if (allDone) {
        setProcessing(false);
        router.push("/review");
        return;
      }
      setTimeout(poll, 2000);
    };
    poll();
  }

  if (processing) {
    return (
      <div className="flex max-w-lg flex-col items-center gap-3 py-24 text-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-ink/20 border-t-ink" />
        <p className="text-sm text-ink/70">
          Processing your handwriting — segmenting letters and matching them to the sheets you wrote…
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl">
      <h1 className="mb-2 text-2xl font-medium">Teach us your handwriting</h1>
      <p className="mb-6 text-sm text-ink/60">
        Print each sheet, write the lines by hand, then photograph or scan it back in.
      </p>

      <ProgressStepper current={currentSheet} total={TOTAL_SHEETS} />

      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

      <SheetUpload sheetIndex={currentSheet} onUpload={handleUpload} uploading={uploading} />
    </div>
  );
}
