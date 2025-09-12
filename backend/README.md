# NSCP 2015 Beam Calculator Backend (Django + DRF)

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\\Scripts\\activate on Windows
pip install -r requirements.txt

# Create project structure (if you pasted files manually, skip)
python manage.py runserver 0.0.0.0:8000
```

### Endpoint
- `POST /api/beam/calc`

### Example JSON body
```json
{
  "width": 300,
  "height": 500,
  "cover": 40,
  "fc": 27.6,
  "agg_size": 20,
  "stirrup_dia": 10,
  "tension_bar_dia": 20,
  "compression_bar_dia": 16,
  "n_tension": 4,
  "n_compression": 2,
  "fy_main": 414,
  "fy_stirrup": 275,
  "Mu": 120.0,
  "Vu": 180.0
}
```

### Response
- Valid JSON with:
  - `rebar_layout.bars` → centers (mm) and roles for front-end drawing
  - `rebar_layout.stirrup_inside` → draw tie rectangle
  - `checks.flexure` & `checks.shear` → detailed steps
  - `latex` → full LaTeX document (ready to compile)

## Engineering Notes (Simplified)
- Flexure: NSCP 2015 ~ ACI 318. We use rectangular stress block (0.85 f'c, β1 per fc). φ depends on ε_t (0.65→0.90).
- Shear: Vc = 0.17 √f'c b d; φ = 0.75. Two-legged vertical ties. s_max = min(d/2, 600 mm). Minimum Av/s enforced.
- Spacing: Clear spacing ≥ max(25 mm, d_b, 4/3 agg). If agg unknown, we ignore that term.
- Coordinate system: bottom-left origin. Bars placed symmetrically across clear stirrup width.

> Always cross-check against NSCP 2015 provisions for your project. This tool is an aid, not a substitute for engineering judgment.