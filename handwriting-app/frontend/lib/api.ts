const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

function authHeaders(): HeadersInit {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed with status ${res.status}`);
  }
  return res.json();
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export async function signup(email: string, password: string): Promise<TokenResponse> {
  const res = await fetch(`${API_BASE}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return handle(res);
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return handle(res);
}

export interface SheetStatus {
  sheet_id: string;
  sheet_index: number;
  status: "uploaded" | "processing" | "processed" | "failed";
  error_message?: string | null;
}

export async function uploadSheet(profileId: string, sheetIndex: number, file: File): Promise<SheetStatus> {
  const formData = new FormData();
  formData.append("sheet_index", String(sheetIndex));
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/enrollment/${profileId}/sheets`, {
    method: "POST",
    headers: authHeaders(),
    body: formData,
  });
  return handle(res);
}

export async function listSheets(profileId: string): Promise<SheetStatus[]> {
  const res = await fetch(`${API_BASE}/enrollment/${profileId}/sheets`, {
    headers: authHeaders(),
  });
  return handle(res);
}

export interface Glyph {
  id: string;
  char_key: string;
  svg_key: string;
  raster_key: string | null;
  classifier_confidence: number | null;
  needs_review: boolean;
  user_confirmed: boolean;
}

export async function listGlyphs(profileId: string, onlyNeedsReview = false): Promise<Glyph[]> {
  const url = new URL(`${API_BASE}/profiles/${profileId}/glyphs`);
  if (onlyNeedsReview) url.searchParams.set("only_needs_review", "true");
  const res = await fetch(url.toString(), { headers: authHeaders() });
  return handle(res);
}

export async function reviewGlyph(glyphId: string, userConfirmed: boolean, correctedCharKey?: string): Promise<Glyph> {
  const res = await fetch(`${API_BASE}/profiles/glyphs/${glyphId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ user_confirmed: userConfirmed, corrected_char_key: correctedCharKey }),
  });
  return handle(res);
}

export async function generateHandwriting(profileId: string, text: string, inkColor = "#1a1a2e"): Promise<string> {
  const res = await fetch(`${API_BASE}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ profile_id: profileId, text, ink_color: inkColor, output_format: "svg" }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed with status ${res.status}`);
  }
  return res.text(); // raw SVG markup
}
