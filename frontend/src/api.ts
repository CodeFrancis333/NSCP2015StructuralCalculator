// src/api.ts
import type { BeamRequest, BeamResponse, CatalogItem } from "./types";

const BASE = (import.meta as any).env?.VITE_API_BASE ?? "/api/v1";

async function parseJsonSafe(res: Response) {
  const raw = await res.text();
  try {
    return { json: JSON.parse(raw), raw };
  } catch {
    return { json: null, raw };
  }
}

export async function getCatalog(): Promise<CatalogItem[]> {
  try {
    const res = await fetch(`${BASE}/catalog/`);
    const { json, raw } = await parseJsonSafe(res);
    if (!res.ok) {
      throw new Error(
        json?.errors ? JSON.stringify(json.errors) : `HTTP ${res.status}: ${raw.slice(0, 300)}`
      );
    }
    return (json?.calculators as CatalogItem[]) ?? [];
  } catch {
    // Fallback (if backend not ready)
    return [
      { slug: "beams", name: "Beam Calculator" },
      { slug: "footing", name: "Footing Calculator" },
      { slug: "slab", name: "Slab Calculator" },
      { slug: "retaining-wall", name: "Retaining Wall Calculator" },
      { slug: "column", name: "Column Calculator" },
    ];
  }
}

export async function calcBeam(payload: BeamRequest): Promise<BeamResponse> {
  const res = await fetch(`${BASE}/beams/calc/`, { // <-- trailing slash matters
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const { json, raw } = await parseJsonSafe(res);

  if (!res.ok) {
    const msg = json?.errors
      ? JSON.stringify(json.errors)
      : `HTTP ${res.status} ${res.statusText}: ${raw.slice(0, 300)}`;
    throw new Error(msg);
  }

  if (!json || typeof json !== "object") {
    throw new Error(`Expected JSON but got: ${raw.slice(0, 300)}`);
  }

  return json as BeamResponse;
}
