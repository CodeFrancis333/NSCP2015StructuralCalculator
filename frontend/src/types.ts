export type CatalogItem = { slug: string; name: string };

// src/types.ts

// ---------- Shared shapes ----------
export interface StirrupRect {
  x_min: number;
  y_min: number;
  x_max: number;
  y_max: number;
}

export interface Bar {
  x_mm: number;
  y_mm: number;
  dia_mm: number;
  role: "tension" | "compression";
  layer: number;
}

// ---------- Request ----------
export interface BeamRequest {
  width: number;
  height: number;
  cover: number;
  fc: number;
  agg_size?: number | null;
  stirrup_dia: number;
  tension_bar_dia: number;
  compression_bar_dia?: number | null;
  n_tension: number;
  n_compression?: number;
  fy_main: number;
  fy_stirrup: number;
  Mu: number; // kN·m
  Vu: number; // kN
}

// ---------- Response pieces ----------
export interface Flexure {
  beta1: number;
  d: number;
  d_prime: number | null;
  a: number;
  c: number;
  eps_t: number;
  fs_t: number;
  fs_c: number;
  phi: number;
  Mn_Nmm: number;
  assumption_used: string;
  derivation: unknown;
}

export interface Shear {
  Vc_kN: number;
  phi: number;
  s_req_mm: number;
  s_min_req_mm: number;
  s_max_mm: number;
  s_use_mm: number;
  phiVn_kN: number;
  ok: boolean;
}

export interface Reinforcement {
  tension_As_mm2: number;
  d_mm: number;
  rho: number;
  rho_min: number;
  rho_max: number;
  As_min_mm2: number;
  used_rho_min_for_capacity: boolean;
}

// ---------- Full response ----------
export interface BeamResponse {
  valid: boolean;
  geom: {
    b_mm: number;
    h_mm: number;
    cover_mm: number;
    fc_MPa: number;
    agg_mm?: number | null;
    stirrup_dia_mm: number;
    tension_dia_mm: number;
    compression_dia_mm?: number | null;
    fy_main_MPa: number;
    fy_stirrup_MPa: number;
    Mu_kNm: number;
    Vu_kN: number;
  };
  rebar_layout: {
    bars: Bar[];
    stirrup_inside: StirrupRect;
  };
  checks: {
    flexure: Flexure;
    flexure_ok: boolean;
    flexure_capacity_kNm: number;
    shear: Shear;
  };
  reinforcement?: Reinforcement; // present after your rho logic
  latex?: string;                 // backend returns this too
}

