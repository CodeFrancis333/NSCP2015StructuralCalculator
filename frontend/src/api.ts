import type { BeamRequest, BeamResponse, CatalogItem } from "./types";

const BASE = "/api/v1";

export async function getCatalog(): Promise<CatalogItem[]> {
  try {
    const r = await fetch(`${BASE}/catalog/`);
    const data = await r.json();
    return data.calculators as CatalogItem[];
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
  const r = await fetch(`${BASE}/beams/calc`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await r.json();
  if (!r.ok) throw new Error(typeof data === "object" ? JSON.stringify(data, null, 2) : String(data));
  return data as BeamResponse;
}
