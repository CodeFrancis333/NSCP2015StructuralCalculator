from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
import math

EPS = 1e-9
E_S = 200000.0  # MPa (steel modulus)

@dataclass
class Bar:
    x_mm: float
    y_mm: float
    dia_mm: float
    role: str   # 'tension' or 'compression'
    layer: int

@dataclass
class StirrupRect:
    x_min: float
    y_min: float
    x_max: float
    y_max: float

@dataclass
class PlacementResult:
    bars: List[Bar]
    stirrup_inside: StirrupRect

# ----------------------------
# Utility conversions
# ----------------------------

def area_of_bar(d_mm: float) -> float:
    return math.pi * (d_mm ** 2) / 4.0  # mm^2


def beta1_of_fc(fc: float) -> float:
    """ACI/NSCP beta1 approximation.
    fc in MPa. For fc <= 28 MPa => 0.85; reduce 0.05/7 MPa to min 0.65.
    """
    if fc <= 28:
        return 0.85
    red = 0.05 * ((fc - 28.0) / 7.0)
    return max(0.85 - red, 0.65)


def phi_flexure_from_strain(eps_t: float) -> float:
    """Phi for flexure per ACI/NSCP style: linear from 0.65 (<=0.002) to 0.90 (>=0.005)."""
    if eps_t <= 0.002:
        return 0.65
    if eps_t >= 0.005:
        return 0.90
    # Linear interpolation
    return 0.65 + (eps_t - 0.002) * (0.90 - 0.65) / (0.005 - 0.002)


def min_clear_spacing(db: float, agg_size: Optional[float]) -> float:
    """NSCP/ACI min clear spacing between parallel bars in a layer.
    >= max(25 mm, db, 1.33*agg_size). If agg_size is None, ignore that term.
    """
    base = max(25.0, db)
    if agg_size is not None and agg_size > 0:
        base = max(base, 1.33 * agg_size)
    return base

# ----------------------------
# Automatic rebar placement
# ----------------------------

def place_row_across_width(b_inside: float, n: int, db: float, s_clear_min: float) -> Tuple[List[float], float]:
    """Return x-center positions for n bars across available inside width.
    Places bars symmetrically. Returns (x_list, used_width).
    Origin x=0 at left concrete face; but we'll later shift to desired origin.
    """
    if n <= 0:
        return [], 0.0
    # Required total width (bar diameters + clear spaces between)
    req = n * db + (n - 1) * s_clear_min
    if req - b_inside > EPS:
        raise ValueError("Bars do not fit in one row across width with required clear spacing")
    # Remaining slop for side clearances (left/right). Distribute equally.
    side_clear_total = b_inside - req
    left_clear = right_clear = side_clear_total / 2.0
    x_positions = []
    x = left_clear + db / 2.0
    for _ in range(n):
        x_positions.append(x)
        x += db + s_clear_min
    used_width = req
    return x_positions, used_width


def place_bars(
    width: float,
    height: float,
    cover: float,
    stirrup_dia: float,
    n_tension: int,
    db_tension: float,
    n_compression: int,
    db_compression: Optional[float],
    agg_size: Optional[float],
) -> PlacementResult:
    """Place bars automatically within stirrup, validating NSCP clear spacing.

    NSCP 2015 spacing rules used here:
      - Horizontal clear spacing in a layer ≥ max(25 mm, d_b, 4/3 D_agg)  (425.2.1)
      - For multiple layers, bars in upper layers are placed directly above bottom
        layer bars, with vertical clear spacing between layers ≥ 25 mm  (425.2.2)

    Coordinate system: origin (0,0) at bottom-left of concrete section.
    """
    b = width
    h = height
    inside_x_min = cover + stirrup_dia
    inside_x_max = b - cover - stirrup_dia
    inside_y_min = cover + stirrup_dia
    inside_y_max = h - cover - stirrup_dia

    b_inside = inside_x_max - inside_x_min

    bars: List[Bar] = []

    # ---- Helpers ----
    def max_bars_one_row(b_inside: float, db: float, s_clear: float) -> int:
        if b_inside <= 0:
            return 0
        # n*db + (n-1)*s <= b_inside => n <= (b_inside + s)/(db + s)
        return max(int(math.floor((b_inside + s_clear) / (db + s_clear))), 0)

    def symmetric_row_positions(b_inside: float, n: int, db: float, s_clear: float) -> List[float]:
        # Even side clearances, min clear between bars
        req = n * db + (n - 1) * s_clear
        if req - b_inside > EPS:
            raise ValueError("Bars do not fit in one row across width with required clear spacing")
        side_clear_total = b_inside - req
        left_clear = side_clear_total / 2.0
        xs = []
        x = left_clear + db / 2.0
        for _ in range(n):
            xs.append(x)
            x += db + s_clear
        return xs

    def pick_second_row_positions(x_bot: List[float], n2: int) -> List[float]:
        """Place upper-layer bars directly above bottom-layer bars per 425.2.2,
        following your requested pattern:
          - n2=1: leftmost ("glued" to left stirrup via bottom extreme)
          - n2=2: leftmost & rightmost
          - n2=3: leftmost, middle, rightmost
          - n2>3: extremes first, remaining approximately evenly across bottom indices
        """
        m = len(x_bot)
        if n2 <= 0 or m == 0:
            return []
        idxs: List[int] = []
        if n2 == 1:
            idxs = [0]
        elif n2 == 2:
            idxs = [0, m - 1]
        elif n2 == 3:
            idxs = [0, m // 2, m - 1]
        else:
            # extremes
            idxs = [0, m - 1]
            remain = n2 - 2
            if remain > 0:
                # distribute remaining indices roughly uniformly
                for k in range(1, remain + 1):
                    idx = round(k * (m - 1) / (remain + 1))
                    idxs.append(int(idx))
            idxs = sorted(set(idxs))
            # ensure count == n2 (pad by nearest unused if needed)
            i = 0
            while len(idxs) < n2 and i < m:
                if i not in idxs:
                    idxs.insert(-1, i)
                i += 1
            idxs = sorted(idxs[:n2])
        return [x_bot[i] for i in idxs]

    # ---- Tension bars (bottom) ----
    smin_t = min_clear_spacing(db_tension, agg_size)  # horizontal clear spacing
    y1 = inside_y_min + db_tension / 2.0

    # Capacity of one row
    cap1 = max_bars_one_row(b_inside, db_tension, smin_t)
    if n_tension <= cap1:
        x_bot = symmetric_row_positions(b_inside, n_tension, db_tension, smin_t)
        x_bot = [inside_x_min + x for x in x_bot]
        for x in x_bot:
            bars.append(Bar(x_mm=x, y_mm=y1, dia_mm=db_tension, role="tension", layer=1))
    else:
        # Split into two layers: first layer as full as possible, second layer gets the remainder
        n1 = cap1
        n2 = n_tension - n1
        if n1 < 2:
            # If even one row cannot host at least 2 bars, report fit failure early
            raise ValueError("Bottom layer cannot host at least 2 bars with required clear spacing; increase width or reduce db/agg size.")
        x_bot_rel = symmetric_row_positions(b_inside, n1, db_tension, smin_t)
        x_bot = [inside_x_min + x for x in x_bot_rel]
        for x in x_bot:
            bars.append(Bar(x_mm=x, y_mm=y1, dia_mm=db_tension, role="tension", layer=1))
        # Vertical clear spacing between layers per NSCP 425.2.2 (≥25 mm)
        s_vert = 25.0
        y2 = y1 + db_tension + s_vert
        if y2 + db_tension / 2.0 > inside_y_max + EPS:
            raise ValueError("Tension bars need more vertical space (two layers don't fit)")
        # Second layer positions: directly above selected bottom bars, following requested edge/middle pattern
        x2_pick = pick_second_row_positions(x_bot_rel, n2)  # use relative coords of bottom row
        if len(x2_pick) != n2:
            raise ValueError("Internal placement issue for second layer (selection mismatch)")
        x2 = [inside_x_min + x for x in x2_pick]
        for x in x2:
            bars.append(Bar(x_mm=x, y_mm=y2, dia_mm=db_tension, role="tension", layer=2))

    # ---- Compression bars (top, optional) ----
    if n_compression > 0 and db_compression is not None and db_compression > 0:
        smin_c = min_clear_spacing(db_compression, agg_size)
        ytop1 = inside_y_max - db_compression / 2.0
        capc = max_bars_one_row(b_inside, db_compression, smin_c)
        if n_compression <= capc:
            x_top = symmetric_row_positions(b_inside, n_compression, db_compression, smin_c)
            x_top = [inside_x_min + x for x in x_top]
            for x in x_top:
                bars.append(Bar(x_mm=x, y_mm=ytop1, dia_mm=db_compression, role="compression", layer=1))
        else:
            n1c = capc
            n2c = n_compression - n1c
            x_top_rel = symmetric_row_positions(b_inside, n1c, db_compression, smin_c)
            x_top = [inside_x_min + x for x in x_top_rel]
            for x in x_top:
                bars.append(Bar(x_mm=x, y_mm=ytop1, dia_mm=db_compression, role="compression", layer=1))
            # Second compression layer downward with ≥25 mm vertical clear spacing
            s_vert_c = 25.0
            ytop2 = ytop1 - (db_compression + s_vert_c)
            if ytop2 - db_compression / 2.0 < inside_y_min - EPS:
                raise ValueError("Compression bars need more vertical space (two layers don't fit)")
            x2c_pick = pick_second_row_positions(x_top_rel, n2c)
            x2c = [inside_x_min + x for x in x2c_pick]
            for x in x2c:
                bars.append(Bar(x_mm=x, y_mm=ytop2, dia_mm=db_compression, role="compression", layer=2))

    stirrup = StirrupRect(
        x_min=inside_x_min,
        y_min=inside_y_min,
        x_max=inside_x_max,
        y_max=inside_y_max,
    )

    return PlacementResult(bars=bars, stirrup_inside=stirrup)

# ----------------------------
# Strength calculations
# ----------------------------

def centroid_of_role(bars: List[Bar], role: str) -> float:
    """Return y-centroid (mm from bottom) of bars having the given role."""
    as_total = 0.0
    y_as = 0.0
    for b in bars:
        if b.role == role:
            a = area_of_bar(b.dia_mm)
            as_total += a
            y_as += a * b.y_mm
    if as_total < EPS:
        return float("nan")
    return y_as / as_total


def sum_area(bars: List[Bar], role: str) -> float:
    return sum(area_of_bar(b.dia_mm) for b in bars if b.role == role)


def calc_flexure(
    b: float,
    h: float,
    fc: float,
    fy: float,
    bars: List[Bar],
) -> Dict:
    """Compute φMn and related parameters with explicit assumption tracing.

    We iterate over four assumption cases for (fs, f's):
      A1: (yield,  yield)
      A2: (yield,  not-yield)
      A3: (not-yield, yield)
      A4: (not-yield, not-yield)

    For each case, we solve equilibrium explicitly for c using bisection
    with the corresponding stress definitions:
      fs  = fy                      (yield)          or  600 * (d - c)/c (not-yield)
      f's = fy (compression, if inside block)        or  600 * (c - d')/c (not-yield)

    Equilibrium form (compression steel inside block a≥d'):
      0.85 f'c * β1 * c * b + A's (f's - 0.85 f'c) = As * fs

    If a < d', compression steel is outside the block and carries tension; here we
    conservatively set the net term A's(f's-0.85 f'c)≈0 for equilibrium (rare for normal beams),
    and log this condition.
    """
    beta1 = beta1_of_fc(fc)
    As_t = sum_area(bars, "tension")
    As_c = sum_area(bars, "compression")

    y_t = centroid_of_role(bars, "tension")
    y_c = centroid_of_role(bars, "compression") if As_c > EPS else float("nan")

    d = h - y_t  # mm
    d_prime = h - y_c if As_c > EPS and not math.isnan(y_c) else None  # mm from top to comp steel

    # Helper: fs given c under assumption
    def fs_of_c(c: float, assume_yield: bool) -> float:
        if assume_yield:
            return fy
        # fs = Es*0.003*(d-c)/c = 600*(d-c)/c (MPa)
        return max(min(600.0 * (d - c) / max(c, EPS), fy), -fy)

    # Helper: f's (compression steel) given c
    def fsp_of_c(c: float, assume_yield: bool) -> float:
        if d_prime is None:
            return 0.0
        if assume_yield:
            return fy
        # f's = Es*0.003*(c - d')/c = 600*(c - d')/c (compression + if c>d')
        return max(min(600.0 * (c - d_prime) / max(c, EPS), fy), -fy)

    # Result container for derivation log
    derivation = {
        "beta1": beta1,
        "d_mm": d,
        "d_prime_mm": d_prime,
        "assumptions_tried": [],
    }

    # Equilibrium residual for a given c and assumption case
    def residual(c: float, y_tension: bool, y_comp: bool) -> Tuple[float, Dict]:
        a = beta1 * c
        inside_block = (d_prime is not None) and (a + 1e-9 >= d_prime)
        fs = fs_of_c(c, y_tension)
        fsp = fsp_of_c(c, y_comp) if inside_block else 0.0
        # 0.85 f'c * a * b + As'(f's - 0.85 f'c) = As * fs
        Cc = 0.85 * fc * b * a
        term_comp = As_c * (fsp - 0.85 * fc) if inside_block else 0.0
        T = As_t * fs
        R = (Cc + term_comp) - T
        info = {
            "c": c, "a": a, "fs": fs, "fsp": fsp,
            "inside_block": inside_block, "Cc": Cc, "term_comp": term_comp,
        }
        return R, info

    def solve_for_case(y_tension: bool, y_comp: bool) -> Tuple[Optional[float], Dict]:
        # Bracket c in a reasonable range
        c_lo, c_hi = 1.0, max(50.0, 0.9 * d)
        R_lo, _ = residual(c_lo, y_tension, y_comp)
        R_hi, _ = residual(c_hi, y_tension, y_comp)
        it = 0
        while R_lo * R_hi > 0 and it < 60:
            c_hi *= 1.5
            R_hi, _ = residual(c_hi, y_tension, y_comp)
            it += 1
        if R_lo * R_hi > 0:
            return None, {"note": "Failed to bracket root"}
        info_mid = {}
        for _ in range(100):
            c_mid = 0.5 * (c_lo + c_hi)
            R_mid, info_mid = residual(c_mid, y_tension, y_comp)
            if abs(R_mid) < 1e-3:
                return c_mid, info_mid
            if R_lo * R_mid > 0:
                c_lo, R_lo = c_mid, R_mid
            else:
                c_hi, R_hi = c_mid, R_mid
        return c_mid, info_mid

    # Try cases in order A1→A4 and keep the first consistent solution
    cases = [
        (True, True,  "fs: yield, f's: yield"),
        (True, False, "fs: yield, f's: not yield"),
        (False, True, "fs: not yield, f's: yield"),
        (False, False,"fs: not yield, f's: not yield"),
    ]

    chosen = None
    c = None
    info = {}

    for yt, yc_assume, label in cases:
        c_try, info_try = solve_for_case(yt, yc_assume)
        if c_try is None:
            derivation["assumptions_tried"].append({
                "case": label, "status": "no-root",
            })
            continue
        # Evaluate actual stresses to verify assumption
        fs_val = fs_of_c(c_try, yt)
        fsp_val = fsp_of_c(c_try, yc_assume) if info_try.get("inside_block", False) else 0.0
        fs_yield_actual = abs(fs_val) >= fy - 1e-6
        fsp_yield_actual = abs(fsp_val) >= fy - 1e-6
        consistent = (fs_yield_actual == yt) and (fsp_yield_actual == yc_assume)
        derivation["assumptions_tried"].append({
            "case": label,
            "c_mm": c_try, "a_mm": info_try.get("a"),
            "fs_MPa": fs_val, "fs_yield?": fs_yield_actual,
            "fsp_MPa": fsp_val, "fsp_yield?": fsp_yield_actual,
            "inside_block": info_try.get("inside_block"),
            "consistent": consistent,
        })
        if consistent and (chosen is None):
            chosen = (yt, yc_assume, label)
            c = c_try
            info = info_try
            break

    # If none consistent, accept the last attempted as conservative result
    if chosen is None:
        yt, yc_assume, label = cases[-1][:3]
        c = derivation["assumptions_tried"][-1].get("c_mm", 0.5 * h)
        # recompute info for reporting
        _, info = residual(c, yt, yc_assume)
        chosen = (yt, yc_assume, label)

    a = info["a"]
    eps_t = max(0.003 * (d - c) / max(c, EPS), 0.0)
    phi = phi_flexure_from_strain(eps_t)

    # Forces for Mn
    fs_final = min(max(600.0 * (d - c) / max(c, EPS), -fy), fy) if not chosen[0] else fy
    T = As_t * fs_final
    Cc = 0.85 * fc * b * a

    if d_prime is not None and info.get("inside_block", False):
        fsp_final = min(max(600.0 * (c - d_prime) / max(c, EPS), -fy), fy) if not chosen[1] else fy
        Cs = As_c * max(fsp_final, 0.0)
        Mn_Nmm = Cc * (d - a / 2.0) + Cs * (d - d_prime)
    else:
        fsp_final = 0.0
        Cs = 0.0
        Mn_Nmm = Cc * (d - a / 2.0)

    return {
        "beta1": beta1,
        "d": d,
        "d_prime": d_prime,
        "a": a,
        "c": c,
        "eps_t": eps_t,
        "fs_t": fs_final,
        "fs_c": fsp_final,
        "phi": phi,
        "Mn_Nmm": Mn_Nmm,
        "derivation": derivation,
        "assumption_used": chosen[2],
    }

def calc_shear(
    b: float,
    d: float,
    fc: float,
    fy_stirrup: float,
    Vu_kN: float,
    stirrup_dia: float,
) -> Dict:
    """Compute shear check and recommended stirrup spacing for two-legged vertical ties.
    Simplified NSCP/ACI formulas:
      Vc = 0.17 * sqrt(fc) * b * d   [N]
      Vs = (Av * fy * d) / s         [N]
      Av for two-legged tie of dia φ: Av = 2 * area_bar(φ)
      φ (phi) for shear = 0.75
      s_max = min(d/2, 600 mm)
      (Provide minimum shear reinforcement per ACI: Av/s >= 0.062 * sqrt(fc) * b / fy)
    """
    Vc_N = 0.17 * math.sqrt(fc) * b * d
    phi = 0.75

    Vu_N = Vu_kN * 1000.0  # kN -> N

    Av = 2.0 * area_of_bar(stirrup_dia)
    # Required Vs to satisfy φ(Vc + Vs) >= Vu
    Vs_req_N = max(Vu_N / phi - Vc_N, 0.0)
    if Av <= EPS or d <= EPS:
        s_req = float("inf")
    else:
        s_req = Av * fy_stirrup * d / max(Vs_req_N, EPS)

    s_max = min(d / 2.0, 600.0)

    # Minimum shear reinforcement (ACI/NSCP): Av/s >= 0.062 * sqrt(fc) * b / fy
    rho_min = 0.062 * math.sqrt(fc) * b / max(fy_stirrup, EPS)
    s_from_min = Av / max(rho_min, EPS)

    s_use = min(s_req, s_max, s_from_min)

    # Compute resulting φVn provided at s_use
    Vs_prov_N = Av * fy_stirrup * d / max(s_use, EPS)
    Vn_N = Vc_N + Vs_prov_N
    phiVn_kN = phi * Vn_N / 1000.0

    return {
        "Vc_kN": Vc_N / 1000.0,
        "phi": phi,
        "s_req_mm": s_req,
        "s_min_req_mm": s_from_min,
        "s_max_mm": s_max,
        "s_use_mm": s_use,
        "phiVn_kN": phiVn_kN,
        "ok": phiVn_kN + 1e-6 >= Vu_kN,
    }

# ----------------------------
# LaTeX report builder
# ----------------------------

def latex_escape(s: str) -> str:
    rep = {
        "\\": r"\textbackslash{}",
        "_": r"\_",
        "%": r"\%",
        "&": r"\&",
        "#": r"\#",
        "$": r"\$",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    out = ""
    for ch in s:
        out += rep.get(ch, ch)
    return out


def build_latex(payload: Dict) -> str:
    """Build a standalone LaTeX doc string summarizing input, placement, and checks."""
    g = payload["geom"]
    flex = payload["checks"]["flexure"]
    shear = payload["checks"]["shear"]
    bars = payload["rebar_layout"]["bars"]

    def fnum(x, digits=3):
        if isinstance(x, (int,)):
            return str(x)
        return f"{x:.{digits}f}"

    bars_table = "".join(
        f"{i+1} & {b['role']} & {fnum(b['dia_mm'])} & {fnum(b['x_mm'])} & {fnum(b['y_mm'])} & {b['layer']}\\\n"
        for i, b in enumerate(bars)
    )

    tex = rf"""
\documentclass[11pt]{{article}}
\usepackage{{amsmath, amssymb, siunitx, geometry, booktabs}}
\geometry{{margin=1in}}
\title{{NSCP 2015 Beam Check (Auto Report)}}
\begin{{document}}
\maketitle
\section*{{Inputs}}
\begin{{tabular}}{{ll}}
$b$ (mm) & {fnum(g['b_mm'])}\\
$h$ (mm) & {fnum(g['h_mm'])}\\
cover (mm) & {fnum(g['cover_mm'])}\\
$f'_c$ (MPa) & {fnum(g['fc_MPa'])}\\
$f_y$ main (MPa) & {fnum(g['fy_main_MPa'])}\\
$f_y$ stirrups (MPa) & {fnum(g['fy_stirrup_MPa'])}\\
$\phi M_u$ target? & No (Mu given)\\
$M_u$ (kN\,m) & {fnum(g['Mu_kNm'])}\\
$V_u$ (kN) & {fnum(g['Vu_kN'])}\\
\end{{tabular}}

\section*{{Geometry & Placement}}
Effective depth $d$ (mm): {fnum(flex['d'])}.\\
$\beta_1$ = {fnum(flex['beta1'],3)}.

\medskip
Bars (centers; mm):
\begin{{tabular}}{{rrrrrr}}
\toprule
\# & role & $d_b$ & $x$ & $y$ & layer\\
\midrule
{bars_table}\bottomrule
\end{{tabular}}

\section*{{Flexure}}
$\varepsilon_t$ = {fnum(flex['eps_t'],5)}; $\phi$ = {fnum(flex['phi'],3)}.\\
$a$ = {fnum(flex['a'])} mm, $c$ = {fnum(flex['c'])} mm.\\
$\phi M_n$ = {fnum(flex['phi'] * flex['Mn_Nmm'] / 10**6)} kN\,m.\\
Demand: $M_u$ = {fnum(g['Mu_kNm'])} kN\,m.\\
Result: $\boxed{{\text{{{'OK' if payload['checks']['flexure_ok'] else 'NG'}}}}}$

\section*{{Shear}}
$V_c$ = {fnum(shear['Vc_kN'])} kN; $\phi$ = {fnum(shear['phi'])}.\\
Use two-legged $\varphi${int(g['stirrup_dia_mm'])} ties.\\
$s_\text{{req}}$ = {fnum(shear['s_req_mm'])} mm; $s_{{\min,\,code}}$ = {fnum(shear['s_min_req_mm'])} mm; $s_\text{{max}}$ = {fnum(shear['s_max_mm'])} mm.\\
Provide $s$ = {fnum(shear['s_use_mm'])} mm $\Rightarrow$ $\phi V_n$ = {fnum(shear['phiVn_kN'])} kN.\\
Demand: $V_u$ = {fnum(g['Vu_kN'])} kN.\\
Result: $\boxed{{\text{{{'OK' if shear['ok'] else 'NG'}}}}}$

\end{{document}}
"""
    return tex

# ----------------------------
# Orchestrator
# ----------------------------

def run_calculation(payload_in: Dict) -> Dict:
    """Main entry point. Takes validated input dict, returns response dict.
    Validates fit & spacing by attempting placement. Then computes flexure & shear,
    and returns LaTeX string in the response.
    """
    b = payload_in["width"]
    h = payload_in["height"]
    cover = payload_in["cover"]
    fc = payload_in["fc"]
    agg = payload_in.get("agg_size")
    stirrup_dia = float(payload_in["stirrup_dia"])  # mm
    db_t = float(payload_in["tension_bar_dia"])     # mm
    db_c = float(payload_in.get("compression_bar_dia") or 0.0)
    n_t = int(payload_in["n_tension"])
    n_c = int(payload_in.get("n_compression", 0))
    fy_main = payload_in["fy_main"]
    fy_st = payload_in["fy_stirrup"]
    Mu = payload_in["Mu"]    # kN-m
    Vu = payload_in["Vu"]    # kN

    # 1) Placement (validates spacing & fit)
    placement = place_bars(
        width=b,
        height=h,
        cover=cover,
        stirrup_dia=stirrup_dia,
        n_tension=n_t,
        db_tension=db_t,
        n_compression=n_c,
        db_compression=(db_c if n_c > 0 else None),
        agg_size=agg,
    )

    # 2) Flexure
    flex = calc_flexure(
        b=b,
        h=h,
        fc=fc,
        fy=fy_main,
        bars=placement.bars,
    )

    phiMn_kNm = flex["phi"] * flex["Mn_Nmm"] / 1e6
    flex_ok = phiMn_kNm + 1e-6 >= Mu

    # 3) Shear
    shear = calc_shear(
        b=b,
        d=flex["d"],
        fc=fc,
        fy_stirrup=fy_st,
        Vu_kN=Vu,
        stirrup_dia=stirrup_dia,
    )

    # 4) Build JSON
    out = {
        "valid": True,
        "geom": {
            "b_mm": b,
            "h_mm": h,
            "cover_mm": cover,
            "fc_MPa": fc,
            "agg_mm": agg,
            "stirrup_dia_mm": stirrup_dia,
            "tension_dia_mm": db_t,
            "compression_dia_mm": (db_c if n_c > 0 else None),
            "fy_main_MPa": fy_main,
            "fy_stirrup_MPa": fy_st,
            "Mu_kNm": Mu,
            "Vu_kN": Vu,
        },
        "rebar_layout": {
            "bars": [
                {
                    "x_mm": b_.x_mm,
                    "y_mm": b_.y_mm,
                    "dia_mm": b_.dia_mm,
                    "role": b_.role,
                    "layer": b_.layer,
                }
                for b_ in placement.bars
            ],
            "stirrup_inside": placement.stirrup_inside.__dict__,
        },
        "checks": {
            "flexure": flex,
            "flexure_ok": flex_ok,
            "flexure_capacity_kNm": phiMn_kNm,
            "shear": shear,
        },
    }

    # 5) LaTeX
    out["latex"] = build_latex(out)
    return out