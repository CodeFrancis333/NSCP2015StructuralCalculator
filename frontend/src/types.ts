// src/types.ts

export type CatalogItem = { slug: string; name: string };

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
  Mu: number;             // kN·m
  Vu?: number | null;     // kN (optional)
  lightweight?: boolean;  // default false (λ = 1.0)
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

export type GoverningLimit = "strength" | "table" | "minimum";

export interface Shear {
  // Core
  phi: number;
  lambda_concrete: number; // λ = 1.0 (normal) or 0.75 (lightweight)
  Vc_kN: number;

  // Strength/spacing
  Vs_req_kN: number;       // required Vs from strength
  Vs_threshold_kN: number; // 0.33*sqrt(fc)*b*d (table branch)
  table_case: string;      // human text which branch applied
  s_req_mm: number;        // from strength
  s_min_req_mm: number;    // from minimum Av/s
  s_table_max_mm: number;  // from table limit (min(d/2,600) or min(d/4,300))
  s_use_mm: number;        // governing spacing actually used
  governing_limit: GoverningLimit;

  // Provided capacity @ s_use
  Vs_prov_kN: number;
  phiVn_kN: number;
  ok: boolean;

  // Cross-sectional dimension limit (Sec. 422.5.1.2)
  dim_limit_phiV_kN: number;
  ok_dim: boolean;

  // Echo of inputs helpful in report/debug
  inputs: {
    b_mm: number;
    d_mm: number;
    fc_MPa: number;
    fyt_MPa: number;
    stirrup_phi_mm: number;
    Av_mm2: number;
  };

  // Text note for 409.4.3
  support_shear_note: string;
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
    Vu_kN?: number | null;  // may be null/undefined if not provided
    lightweight?: boolean;
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
  reinforcement: Reinforcement; // backend now always sends this
  latex?: string;
}
