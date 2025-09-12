export type CatalogItem = { slug: string; name: string };

export type BeamRequest = {
  width: number; height: number; cover: number;
  fc: number; agg_size?: number | null;
  stirrup_dia: number; tension_bar_dia: number; compression_bar_dia?: number | null;
  n_tension: number; n_compression?: number;
  fy_main: number; fy_stirrup: number;
  Mu: number; Vu: number;
};

export type Bar = {
  x_mm: number; y_mm: number; dia_mm: number; role: 'tension'|'compression'; layer: number;
};
export type StirrupRect = { x_min: number; y_min: number; x_max: number; y_max: number };

export type BeamResponse = {
  valid: boolean;
  geom: { b_mm: number; h_mm: number; cover_mm: number };
  rebar_layout: { bars: Bar[]; stirrup_inside: StirrupRect };
  checks: {
    flexure_ok: boolean; flexure_capacity_kNm: number;
    shear: { ok: boolean; phiVn_kN: number; s_use_mm: number };
  };
  latex: string;
};
