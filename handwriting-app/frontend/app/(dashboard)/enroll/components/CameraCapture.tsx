"use client";

import { useEffect, useRef, useState } from "react";

export function CameraCapture({ onCapture }: { onCapture: (file: File) => void }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [active, setActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function startCamera() {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" }, // rear camera on mobile
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setActive(true);
    } catch {
      setError("Couldn't access the camera. You can upload a photo instead.");
    }
  }

  function stopCamera() {
    const stream = videoRef.current?.srcObject as MediaStream | null;
    stream?.getTracks().forEach((track) => track.stop());
    setActive(false);
  }

  function capture() {
    if (!videoRef.current) return;
    const canvas = document.createElement("canvas");
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx?.drawImage(videoRef.current, 0, 0);
    canvas.toBlob((blob) => {
      if (blob) onCapture(new File([blob], "capture.jpg", { type: "image/jpeg" }));
      stopCamera();
    }, "image/jpeg", 0.92);
  }

  useEffect(() => stopCamera, []);

  return (
    <div>
      {!active ? (
        <button
          onClick={startCamera}
          className="rounded-lg border border-ink/20 px-4 py-2 text-sm hover:bg-ink/5"
        >
          Use camera
        </button>
      ) : (
        <div className="flex flex-col items-start gap-3">
          <video ref={videoRef} className="w-full max-w-md rounded-lg" muted playsInline />
          <div className="flex gap-2">
            <button onClick={capture} className="rounded-lg bg-ink px-4 py-2 text-sm font-medium text-white">
              Capture
            </button>
            <button onClick={stopCamera} className="rounded-lg border border-ink/20 px-4 py-2 text-sm">
              Cancel
            </button>
          </div>
        </div>
      )}
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
  );
}
