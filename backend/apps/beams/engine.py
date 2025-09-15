from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
import math

EPS = 1e-9
E_S = 200000.0  # MPa (steel modulus; reserved for future elastic checks)

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
# Utilities
# ----------------------------

def area_of_bar(d_mm: float) -> float:
    return math.pi * (d_mm ** 2) / 4.0  # mm^2


def beta1_of_fc(fc: float) -> float:
    """ACI/NSCP beta1 approximation (MPa)."""
    if fc <= 28:
        return 0.85
    red = 0.05 * ((fc - 28.0) / 7.0)
    return max(0.85 - red, 0.65)


def phi_flexure_from_strain(eps_t: float) -> float:
    """φ for flexure (tension-controlled ramp 0.65→0.90)."""
    if eps_t <= 0.002:
        return 0.65
    if eps_t >= 0.005:
        return 0.90
    return 0.65 + (eps_t - 0.002) * (0.90 - 0.65) / (0.005 - 0.002)


def min_clear_spacing(db: float, agg_size: Optional[float]) -> float:
    """NSCP 425.2.1: ≥ max(25 mm, db, 4/3 D_agg)."""
    base = max(25.0, db)
    if agg_size is not None and agg_size > 0:
        base = max(base, 1.33 * agg_size)
    return base


def rho_min_flexure(fc_MPa: float, fy_MPa: float) -> float:
    """NSCP 409.6.1 (metric)."""
    return max(1.4 / max(fy_MPa, EPS), 0.25 * math.sqrt(fc_MPa) / max(fy_MPa, EPS))


def rho_max_flexure(fc_MPa: float, fy_MPa: float) -> float:
    """Proxy of compression-controlled limit per brief."""
    beta1 = beta1_of_fc(fc_MPa)
    return (3.0 / 8.0) * (0.85 * beta1 * fc_MPa / max(fy_MPa, EPS))


# ----------------------------
# Automatic rebar placement
# ----------------------------

def place_row_across_width(b_inside: float, n: int, db: float, s_clear_min: float) -> Tuple[List[float], float]:
    if n <= 0:
        return [], 0.0
    req = n * db + (n - 1) * s_clear_min
    if req - b_inside > EPS:
        raise ValueError("Bars do not fit in one row across width with required clear spacing")
    side_clear_total = b_inside - req
    left_clear = side_clear_total / 2.0
    xs = []
    x = left_clear + db / 2.0
    for _ in range(n):
        xs.append(x)
        x += db + s_clear_min
    return xs, req


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
    """Place bars within the stirrup; enforce NSCP 425.2.x spacing rules."""
    b = width
    h = height
    inside_x_min = cover + stirrup_dia
    inside_x_max = b - cover - stirrup_dia
    inside_y_min = cover + stirrup_dia
    inside_y_max = h - cover - stirrup_dia

    b_inside = inside_x_max - inside_x_min

    bars: List[Bar] = []

    # ---- helpers
    def max_bars_one_row(b_inside: float, db: float, s_clear: float) -> int:
        if b_inside <= 0:
            return 0
        return max(int(math.floor((b_inside + s_clear) / (db + s_clear))), 0)

    def symmetric_row_positions(bi: float, n: int, db: float, s_clear: float) -> List[float]:
        req = n * db + (n - 1) * s_clear
        if req - bi > EPS:
            raise ValueError("Bars do not fit in one row across width with required clear spacing")
        side_clear_total = bi - req
        left_clear = side_clear_total / 2.0
        xs = []
        x = left_clear + db / 2.0
        for _ in range(n):
            xs.append(x)
            x += db + s_clear
        return xs

    def pick_second_row_positions(x_bot: List[float], n2: int) -> List[float]:
        """Upper layer above bottom indices per requested pattern."""
        m = len(x_bot)
        if n2 <= 0 or m == 0:
            return []
        if n2 == 1:
            idxs = [0]
        elif n2 == 2:
            idxs = [0, m - 1]
        elif n2 == 3:
            idxs = [0, m // 2, m - 1]
        else:
            idxs = [0, m - 1]
            remain = n2 - 2
            for k in range(1, remain + 1):
                idxs.append(int(round(k * (m - 1) / (remain + 1))))
            idxs = sorted(set(idxs))[:n2]
            while len(idxs) < n2:
                for i in range(m):
                    if i not in idxs:
                        idxs.append(i)
                        if len(idxs) == n2:
                            break
        return [x_bot[i] for i in idxs]

    # ---- tension bars (bottom)
    smin_t = min_clear_spacing(db_tension, agg_size)
    y1 = inside_y_min + db_tension / 2.0

    cap1 = max_bars_one_row(b_inside, db_tension, smin_t)
    if n_tension <= cap1:
        x_bot = symmetric_row_positions(b_inside, n_tension, db_tension, smin_t)
        x_bot = [inside_x_min + x for x in x_bot]
        for x in x_bot:
            bars.append(Bar(x_mm=x, y_mm=y1, dia_mm=db_tension, role="tension", layer=1))
    else:
        n1 = cap1
        n2 = n_tension - n1
        if n1 < 2:
            raise ValueError("Bottom layer cannot host at least 2 bars with required clear spacing; increase width or reduce db/agg size.")
        x_bot_rel = symmetric_row_positions(b_inside, n1, db_tension, smin_t)
        x_bot = [inside_x_min + x for x in x_bot_rel]
        for x in x_bot:
            bars.append(Bar(x_mm=x, y_mm=y1, dia_mm=db_tension, role="tension", layer=1))
        s_vert = 25.0
        y2 = y1 + db_tension + s_vert
        if y2 + db_tension / 2.0 > inside_y_max + EPS:
            raise ValueError("Tension bars need more vertical space (two layers don't fit)")
        x2_pick = pick_second_row_positions(x_bot_rel, n2)
        if len(x2_pick) != n2:
            raise ValueError("Internal placement issue for second layer (selection mismatch)")
        x2 = [inside_x_min + x for x in x2_pick]
        for x in x2:
            bars.append(Bar(x_mm=x, y_mm=y2, dia_mm=db_tension, role="tension", layer=2))

    # ---- compression bars (top, optional)
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
) -> Dict[str, Any]:
    """Compute φMn and related parameters with explicit assumption tracing."""
    beta1 = beta1_of_fc(fc)
    As_t = sum_area(bars, "tension")
    As_c = sum_area(bars, "compression")

    y_t = centroid_of_role(bars, "tension")
    y_c = centroid_of_role(bars, "compression") if As_c > EPS else float("nan")

    d = h - y_t  # mm
    d_prime = h - y_c if As_c > EPS and not math.isnan(y_c) else None  # mm from top to compression steel

    # Helpers: tension/compression steel stress vs c
    def fs_of_c(c: float, assume_yield: bool) -> float:
        if assume_yield:
            return fy
        return max(min(600.0 * (d - c) / max(c, EPS), fy), -fy)

    def fsp_of_c(c: float, assume_yield: bool) -> float:
        if d_prime is None:
            return 0.0
        if assume_yield:
            return fy
        return max(min(600.0 * (c - d_prime) / max(c, EPS), fy), -fy)

    derivation = {
        "beta1": beta1,
        "d_mm": d,
        "d_prime_mm": d_prime,
        "assumptions_tried": [],
    }

    def residual(c: float, y_tension: bool, y_comp: bool) -> Tuple[float, Dict[str, Any]]:
        a = beta1 * c
        inside_block = (d_prime is not None) and (a + 1e-9 >= d_prime)
        fs = fs_of_c(c, y_tension)
        fsp = fsp_of_c(c, y_comp) if inside_block else 0.0
        Cc = 0.85 * fc * b * a
        T = As_t * fs
        term_comp = As_c * (fsp - 0.85 * fc) if inside_block else 0.0
        R = (Cc + term_comp) - T
        info = {
            "c": c, "a": a, "fs": fs, "fsp": fsp,
            "inside_block": inside_block, "Cc": Cc, "term_comp": term_comp,
        }
        return R, info

    def solve_for_case(y_tension: bool, y_comp: bool) -> Tuple[Optional[float], Dict[str, Any]]:
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
        info_mid: Dict[str, Any] = {}
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

    cases = [
        (True,  True,  "fs: yield, f's: yield"),
        (True,  False, "fs: yield, f's: not yield"),
        (False, True,  "fs: not yield, f's: yield"),
        (False, False, "fs: not yield, f's: not yield"),
    ]

    chosen = None
    c = None
    info: Dict[str, Any] = {}

    for yt, yc_assume, label in cases:
        c_try, info_try = solve_for_case(yt, yc_assume)
        if c_try is None:
            derivation["assumptions_tried"].append({"case": label, "status": "no-root"})
            continue
        fs_val = fs_of_c(c_try, yt)
        fsp_val = fsp_of_c(c_try, yc_assume) if info_try.get("inside_block", False) else 0.0
        fs_yield_actual  = abs(fs_val)  >= fy - 1e-6
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

    if chosen is None:
        yt, yc_assume, label = cases[-1][:3]
        c = derivation["assumptions_tried"][-1].get("c_mm", 0.5 * h)
        _, info = residual(c, yt, yc_assume)
        chosen = (yt, yc_assume, label)

    a = info["a"]
    eps_t = max(0.003 * (d - c) / max(c, EPS), 0.0)
    phi = phi_flexure_from_strain(eps_t)

    # --- Final forces and nominal moment (use the SAME d_prime & As_c used in solving)
    fs_final = fy if chosen[0] else max(min(600.0 * (d - c) / max(c, EPS), fy), -fy)
    Cc = 0.85 * fc * b * a

    if (d_prime is not None) and info.get("inside_block", False) and (As_c > EPS):
        fsp_final = fy if chosen[1] else max(min(600.0 * (c - d_prime) / max(c, EPS), fy), -fy)
        Cs = As_c * max(fsp_final, 0.0)
        Mn_Nmm = Cc * (d - a / 2.0) + Cs * (d - d_prime)
    else:
        fsp_final = 0.0
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

# ----------------------------
# Shear (NSCP 2015)
# ----------------------------

def calc_shear(
    b: float,                # bw (mm)
    d: float,                # effective depth (mm)
    fc: float,               # MPa
    fy_stirrup: float,       # MPa
    Vu_kN: Optional[float],  # kN (may be None)
    stirrup_dia: float,      # mm (two-legged vertical ties)
    lightweight: bool = False,
) -> Dict[str, Any]:
    """
    NSCP 2015 shear checks (non-prestressed beams) with detailed outputs.

    Vn = Vc + Vs (422.5.1.1)
    Vc = (1/6)*λ*sqrt(fc)*bw*d (422.5.5)
    Vs = Av*fyt*d/s (422.5.10)  [Av=2 legs here]
    φ_shear = 0.75 (Table 421.2.1.b)

    Table 409.7.6.2.2:
      if Vs_req ≤ 0.33√fc·b·d → s_max = min(d/2, 600)
      else                    → s_max = min(d/4, 300)

    Minimum shear (409.6.3; Table 409.6.3.3):
      Av/s ≥ max(0.062√fc·b/fy, 0.35·b/fy)

    Cross-sectional dimension limit (422.5.1.2):
      Vu ≤ φ [Vc + (2/3)√fc·b·d]
    """
    phi = 0.75
    lam = 0.75 if lightweight else 1.0

    Vu_N = 0.0 if Vu_kN is None else Vu_kN * 1000.0

    Av_mm2 = 2.0 * area_of_bar(stirrup_dia)

    Vc_N = (1.0 / 6.0) * lam * math.sqrt(fc) * b * d
    Vs_req_N = max(Vu_N / phi - Vc_N, 0.0)

    # Table branch & s_table_max
    Vs_threshold_N = 0.33 * math.sqrt(fc) * b * d
    if Vs_req_N <= Vs_threshold_N + 1e-6:
        s_table_max_mm = min(d / 2.0, 600.0)
        table_case = "Vs_req ≤ 0.33√f'c·b·d ⇒ s_max = min(d/2, 600) (Tbl 409.7.6.2.2)"
    else:
        s_table_max_mm = min(d / 4.0, 300.0)
        table_case = "Vs_req > 0.33√f'c·b·d ⇒ s_max = min(d/4, 300) (Tbl 409.7.6.2.2)"

    # Minimum Av/s
    av_over_s_min = max(
        0.062 * math.sqrt(fc) * b / max(fy_stirrup, EPS),
        0.35 * b / max(fy_stirrup, EPS),
    )
    s_min_req_mm = Av_mm2 / max(av_over_s_min, EPS)

    # Strength-based spacing (finite)
    if Vs_req_N <= EPS or Av_mm2 <= EPS or d <= EPS:
        s_req_mm = s_table_max_mm  # strength does not govern → use table max
    else:
        s_req_mm = Av_mm2 * fy_stirrup * d / Vs_req_N

    # Governing spacing
    s_use_mm = min(s_req_mm, s_min_req_mm, s_table_max_mm)
    tol = 1e-6
    if abs(s_use_mm - s_req_mm) <= tol:
        governing = "strength"
    elif abs(s_use_mm - s_min_req_mm) <= tol:
        governing = "minimum"
    else:
        governing = "table"

    # Provided Vs & capacities at s_use
    Vs_prov_N = Av_mm2 * fy_stirrup * d / max(s_use_mm, EPS)
    Vn_N = Vc_N + Vs_prov_N
    phiVn_kN = phi * Vn_N / 1000.0

    ok_strength = True if Vu_kN is None else (phiVn_kN + 1e-6 >= Vu_kN)

    # Cross-sectional dimension limit
    dim_limit_phiV_kN = phi * (Vc_N + (2.0 / 3.0) * math.sqrt(fc) * b * d) / 1000.0
    ok_dim = True if Vu_kN is None else (Vu_kN <= dim_limit_phiV_kN + 1e-6)

    return {
        # core
        "phi": phi,
        "lambda_concrete": lam,
        "Vc_kN": Vc_N / 1000.0,

        # strength/spacing
        "Vs_req_kN": Vs_req_N / 1000.0,
        "Vs_threshold_kN": Vs_threshold_N / 1000.0,
        "table_case": table_case,
        "s_req_mm": s_req_mm,                 # finite
        "s_min_req_mm": s_min_req_mm,
        "s_table_max_mm": s_table_max_mm,
        "s_use_mm": s_use_mm,
        "governing_limit": governing,

        # provided capacity @ s_use
        "Vs_prov_kN": Vs_prov_N / 1000.0,
        "phiVn_kN": phiVn_kN,
        "ok": ok_strength and ok_dim,

        # dim limit (422.5.1.2)
        "dim_limit_phiV_kN": dim_limit_phiV_kN,
        "ok_dim": ok_dim,

        # inputs echo
        "inputs": {
            "b_mm": b,
            "d_mm": d,
            "fc_MPa": fc,
            "fyt_MPa": fy_stirrup,
            "stirrup_phi_mm": stirrup_dia,
            "Av_mm2": Av_mm2,
        },

        # 409.4.3 support note
        "support_shear_note": (
            "NSCP 2015 Sec. 409.4.3: For beams integral with supports, Vu may "
            "be taken at the face of support; a section at distance d from the "
            "face may be designed if 409.4.3.2(a)-(c) are satisfied."
        ),
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
    """Build a standalone LaTeX doc string summarizing input, placement, and checks,
    with blue section titles, improved spacing, and NSCP 2015 flexure provisions."""
    import math

    g = payload["geom"]
    flex = payload["checks"]["flexure"]
    shear = payload["checks"]["shear"]
    bars = payload["rebar_layout"]["bars"]

    def fnum(x, digits=3):
        # tolerant formatter: show "-" for None / NaN
        try:
            if x is None:
                return "-"
            if isinstance(x, (int,)):
                return str(x)
            xf = float(x)
            if math.isnan(xf):
                return "-"
            return f"{xf:.{digits}f}"
        except Exception:
            return "-"

    bars_table = "".join(
        f"{i+1} & {b['role']} & {fnum(b['dia_mm'])} & {fnum(b['x_mm'])} & {fnum(b['y_mm'])} & {b['layer']}\\\\\n"
        for i, b in enumerate(bars)
    )

    # Decide which table branch text to show (ASCII + LaTeX macros only)
    vs_branch_le = (shear["Vs_req_kN"] <= shear["Vs_threshold_kN"] + 1e-6)
    table_branch_tex = (
        r"$V_s^{\text{req}} \le 0.33\,\sqrt{f'_c}\,b\,d \ \Rightarrow\ s_{\max}=\min\!\big(d/2,\ 600\ \text{mm}\big)$"
        if vs_branch_le
        else r"$V_s^{\text{req}} > 0.33\,\sqrt{f'_c}\,b\,d \ \Rightarrow\ s_{\max}=\min\!\big(d/4,\ 300\ \text{mm}\big)$"
    )

    tex = rf"""
\documentclass[11pt]{{article}}
\usepackage[margin=1in]{{geometry}}
\usepackage{{amsmath, amssymb, siunitx, booktabs, xcolor}}
\definecolor{{TitleBlue}}{{RGB}}{{22, 80, 184}}
\setlength{{\parindent}}{{0pt}}
\setlength{{\parskip}}{{6pt}}
\sisetup{{detect-all=true}}

% Blue section macro with rule
\newcommand{{\sectblue}}[1]{{\vspace{{6pt}}\textcolor{{TitleBlue}}{{\large\bfseries #1}}\\[-2pt]\rule{{\linewidth}}{{0.6pt}}\vspace{{6pt}}}}

\title{{\textcolor{{TitleBlue}}{{NSCP 2015 Beam Check}}}}
\author{{}}
\date{{}}

\begin{{document}}
\maketitle
\vspace{{-18pt}}

\sectblue{{Inputs}}
\begin{{tabular}}{{ll}}
$b$ (mm) & {fnum(g['b_mm'])}\\
$h$ (mm) & {fnum(g['h_mm'])}\\
cover (mm) & {fnum(g['cover_mm'])}\\
$f'_c$ (MPa) & {fnum(g['fc_MPa'])}\\
$f_y$ main (MPa) & {fnum(g['fy_main_MPa'])}\\
$f_y$ stirrups (MPa) & {fnum(g['fy_stirrup_MPa'])}\\
$M_u$ (kN\,m) & {fnum(g['Mu_kNm'])}\\
$V_u$ (kN) & {fnum(g.get('Vu_kN'))}\\
lightweight? & {('Yes' if g.get('lightweight') else 'No')}\\
\end{{tabular}}

\sectblue{{Geometry \& Placement}}
Effective depth $d$ (mm): {fnum(flex['d'])}.\\
$\beta_1 = {fnum(flex['beta1'],3)}$.

\medskip
\begin{{tabular}}{{rrrrrr}}
\toprule
\# & role & $d_b$ (mm) & $x$ (mm) & $y$ (mm) & layer\\
\midrule
{bars_table}\bottomrule
\end{{tabular}}

\sectblue{{Flexure Results}}
$\varepsilon_t = {fnum(flex['eps_t'],5)}$ \quad $\phi = {fnum(flex['phi'],3)}$.\\
$a = {fnum(flex['a'])}\,\text{{mm}},\quad c = {fnum(flex['c'])}\,\text{{mm}}$.\\
$\phi M_n = {fnum(flex['phi'] * flex['Mn_Nmm'] / 10**6)}\ \text{{kN\,m}}$ \quad vs \quad
$M_u = {fnum(g['Mu_kNm'])}\ \text{{kN\,m}}$ \quad $\Rightarrow$ \fbox{{\textbf{{{'OK' if payload['checks']['flexure_ok'] else 'NG'}}}}}

\sectblue{{Shear (NSCP 2015)}}
$\phi$ (shear) $= {fnum(shear['phi'],2)}$ \ (Table 421.2.1.b).\\
$\lambda$ (concrete density factor) $= {fnum(shear['lambda_concrete'],2)}$.\\
$V_c = \dfrac{{1}}{{6}}\,\lambda\,\sqrt{{f'_c}}\,b\,d = {fnum(shear['Vc_kN'],1)}\ \text{{kN}}$ \ (Sec.\ 422.5.5).\\
$V_s = \dfrac{{A_v\, f_{{yt}}\, d}}{{s}}$ \ (Sec.\ 422.5.10).

\medskip
\textbf{{Spacing limits}} (Table 409.7.6.2.2): {table_branch_tex}.\\
$V_s$ threshold $= 0.33\,\sqrt{{f'_c}}\,b\,d = {fnum(shear['Vs_threshold_kN'],1)}\ \text{{kN}}$.

\medskip
\textbf{{Minimum shear reinforcement}} (Sec.\ 409.6.3; Table 409.6.3.3):\\
$A_v/s \ge \max\!\big(0.062\,\sqrt{{f'_c}}\,b/f_{{yt}},\ 0.35\,b/f_{{yt}}\big)$.

\medskip
$s_{{\text{{req}}}}$ (strength) $= {fnum(shear['s_req_mm'])}\ \text{{mm}},\quad
s_{{\min}} = {fnum(shear['s_min_req_mm'])}\ \text{{mm}},\quad
s_{{\text{{table}}}} = {fnum(shear['s_table_max_mm'])}\ \text{{mm}}.$\\
Provide $s = \fbox{{{fnum(shear['s_use_mm'])}\ \text{{mm}}}}$ \ (governing: {shear['governing_limit']}).\\
Provided: $V_s = {fnum(shear['Vs_prov_kN'],1)}\ \text{{kN}}$, \quad
$\phi V_n = {fnum(shear['phiVn_kN'],1)}\ \text{{kN}}$.\\
Demand: $V_u = {fnum(g.get('Vu_kN'))}\ \text{{kN}}$ \quad $\Rightarrow$ \textbf{{{ 'OK' if shear['ok'] else 'NG' }}}.

\medskip
\textbf{{Cross-sectional dimension limit}} (Sec.\ 422.5.1.2):\\
$V_u \le \phi\!\left(V_c + \dfrac{{2}}{{3}}\,\sqrt{{f'_c}}\,b\,d\right)$ \quad
$\Rightarrow$ \ $\phi V$ limit $= {fnum(shear['dim_limit_phiV_kN'],1)}\ \text{{kN}}$ \quad
\textbf{{{ 'OK' if shear['ok_dim'] else 'NG' }}}.\\
\emph{{Support shear location note}} (Sec.\ 409.4.3): NSCP 2015 Sec. 409.4.3 permits $V_u$ at face of support; a section at $d$ from face may be used if (a)-(c) hold.

\sectblue{{Flexure — NSCP 2015 Provisions (Summary)}}
\textbf{{425.2: Minimum spacing of reinforcement}}\\[-2pt]
\begin{{itemize}}
  \item 425.2.1: In any horizontal layer, clear spacing $\ge \max(25\ \text{{mm}},\ d_b,\ \tfrac{{4}}{{3}}\,d_{{\text{{agg}}}})$.
  \item 425.2.2: For two or more layers, upper bars directly above bottom bars; clear vertical spacing between layers $\ge 25\ \text{{mm}}$.
\end{{itemize}}

\textbf{{420.6.1.3: Specified concrete cover}} (Table 420.6.1.3.1)\\[-2pt]
\begin{{itemize}}
  \item Exposed to weather / in contact with ground: for $d_b \le 16\ \text{{mm}}$, cover $= 40\ \text{{mm}}$.
  \item Exposed to weather / in contact with ground: for $d_b \ge 20\ \text{{mm}}$, cover $= 50\ \text{{mm}}$.
  \item Not exposed to weather / not in contact with ground: cover $\approx 40\ \text{{mm}}$ (typical).
\end{{itemize}}

\textbf{{421.2: Strength reduction}}\\[-2pt]
\begin{{itemize}}
  \item $\phi_{{\text{{flexure}}}}$ per Table 421.2.1(a)/(b) and 421.2.2; tension-controlled ramp used in analysis.
\end{{itemize}}

\textbf{{422.2.2: Flexural design assumptions (concrete)}}\\[-2pt]
\begin{{itemize}}
  \item Max extreme compression fiber strain $= 0.003$.
  \item Concrete tensile strength neglected in strength calculations.
  \item Equivalent compression block with $0.85\,f'_c$ over depth $a=\beta_1 c$.
  \item $\beta_1$ per Table 422.2.2.4.3.
\end{{itemize}}

\textbf{{409.6.1: Minimum flexural reinforcement}} (non-prestressed beams)\\[-2pt]
\[
A_{{s,\min}} \ge \max\!\left(\frac{{0.25\,\sqrt{{f'_c}}}}{{f_y}}\,b_w\,d,\ \frac{{1.4}}{{f_y}}\,b_w\,d\right)
\]

\textbf{{Maximum steel ratio (proxy)}}\\[-2pt]
\[
\rho_{{\max}} \approx \frac{{3}}{{8}}\left(\frac{{0.85\,\beta_1\,f'_c}}{{f_y}}\right),\qquad
A_{{s,\max}}=\rho_{{\max}}\,b_w\,d
\]

\end{{document}}
"""
    return tex

# ----------------------------
# Orchestrator (+ JSON sanitizer)
# ----------------------------

def _json_safe(x: Any) -> Any:
    """Replace NaN/Inf with None recursively to keep JSON happy."""
    if isinstance(x, float):
        return x if math.isfinite(x) else None
    if isinstance(x, dict):
        return {k: _json_safe(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_json_safe(v) for v in x]
    return x


def run_calculation(payload_in: Dict[str, Any]) -> Dict[str, Any]:
    """Main entry point."""
    b = float(payload_in["width"])
    h = float(payload_in["height"])
    cover = float(payload_in["cover"])
    fc = float(payload_in["fc"])
    agg = payload_in.get("agg_size")
    stirrup_dia = float(payload_in["stirrup_dia"])  # mm
    db_t = float(payload_in["tension_bar_dia"])     # mm
    db_c = float(payload_in.get("compression_bar_dia") or 0.0)
    n_t = int(payload_in["n_tension"])
    n_c = int(payload_in.get("n_compression", 0))
    fy_main = float(payload_in["fy_main"])
    fy_st = float(payload_in["fy_stirrup"])
    Mu = float(payload_in["Mu"])    # kN·m
    Vu_in = payload_in.get("Vu", None)  # optional
    Vu_for_calc = None if Vu_in is None else float(Vu_in)    # kN
    lightweight = bool(payload_in.get("lightweight", False))

    # 1) Placement
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

    # 2) Ratios (tension)
    As_t = sum_area(placement.bars, "tension")
    y_t = centroid_of_role(placement.bars, "tension")
    d_eff = h - y_t

    beta1 = beta1_of_fc(fc)
    rho_max = (3.0/8.0) * (0.85 * beta1 * fc / max(fy_main, EPS))
    rho_min = max(1.4 / max(fy_main, EPS), 0.25 * math.sqrt(fc) / max(fy_main, EPS))

    rho_prov = As_t / max(b * d_eff, EPS)
    rho_over = rho_prov > rho_max + 1e-6
    rho_over_msg = None
    As_max_allowed = rho_max * b * d_eff
    As_reduction_needed_pct = 0.0
    bd_increase_needed_pct = 0.0

    if rho_over:
        rho_over_msg = (
            f"Tension steel ratio ρ={rho_prov:.5f} exceeds ρ_max={rho_max:.5f}. "
            "Reduce As or increase section so ρ ≤ ρ_max."
    )
    # How much to change things
    factor = rho_prov / max(rho_max, EPS)  # >1 means too much steel for the section
    As_reduction_needed_pct = (1.0 - 1.0 / factor) * 100.0        # ~22.6% for your case
    bd_increase_needed_pct = (factor - 1.0) * 100.0                # ~29.2% for your case

    # Enforce ρmin virtually for capacity only
    As_min = rho_min * b * d_eff
    bars_for_calc = list(placement.bars)
    used_rho_min = False
    if As_t + 1e-9 < As_min:
        deltaA = As_min - As_t
        virt_dia = math.sqrt(4.0 * deltaA / math.pi)
        x_mid = (placement.stirrup_inside.x_min + placement.stirrup_inside.x_max) / 2.0
        bars_for_calc.append(Bar(x_mm=x_mid, y_mm=y_t, dia_mm=virt_dia, role="tension", layer=1))
        used_rho_min = True

    # 3) Flexure (use bars_for_calc so ρmin affects capacity)
    flex = calc_flexure(
        b=b,
        h=h,
        fc=fc,
        fy=fy_main,
        bars=bars_for_calc,
    )

    phiMn_kNm = flex["phi"] * flex["Mn_Nmm"] / 1e6
    flex_ok = phiMn_kNm + 1e-6 >= Mu

    # 4) Shear (NSCP)
    shear = calc_shear(
        b=b,
        d=flex["d"],
        fc=fc,
        fy_stirrup=fy_st,
        Vu_kN=Vu_for_calc,
        stirrup_dia=stirrup_dia,
        lightweight=lightweight,
    )

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
            "Vu_kN": Vu_in,  # echo None/number as provided
            "lightweight": lightweight,
        },
        "reinforcement": {
            "tension_As_mm2": As_t,
            "d_mm": d_eff,
            "rho": rho_prov,
            "rho_min": rho_min,
            "rho_max": rho_max,
            "As_min_mm2": As_min,
            "used_rho_min_for_capacity": used_rho_min,
            "rho_over": rho_over,
            "rho_over_msg": rho_over_msg,
            "As_max_allowed_mm2": As_max_allowed,
            "As_reduction_needed_pct": As_reduction_needed_pct,
            "bd_increase_needed_pct": bd_increase_needed_pct,
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
            "code_compliance": {
                "rho_max_ok": (not rho_over),
            },
        },
    }

    # 5) LaTeX
    out["latex"] = build_latex(out)

    # 6) JSON-proofing (no NaN/Inf)
    return _json_safe(out)
