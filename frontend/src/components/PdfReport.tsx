// src/components/PdfReport.tsx
import { useEffect, useState } from "react";
import jsPDF from "jspdf";
import { Canvg } from "canvg";
import type { BeamResponse } from "../types";

type Props = {
  data: BeamResponse;
  svgEl: SVGSVGElement | null;
};

export default function PdfReport({ data, svgEl }: Props) {
  const [url, setUrl] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    return () => { if (url) URL.revokeObjectURL(url); };
  }, [url]);

  async function generate() {
    setBusy(true);
    try {
      const doc = new jsPDF({ unit: "pt", format: "a4" });
      doc.setFont("courier", "normal"); // built-in & predictable

      // Page geometry
      const PAGE_W = doc.internal.pageSize.getWidth();
      const PAGE_H = doc.internal.pageSize.getHeight();
      const M_LEFT = 54, M_RIGHT = 54, M_TOP = 64, M_BOTTOM = 34;
      const CONTENT_W = PAGE_W - M_LEFT - M_RIGHT - 8; // extra pad to avoid spill
      let y = M_TOP;
      const LINE_BODY = 12, LINE_HEAD = 22;

      function ensureSpace(needed: number) {
        if (y + needed > PAGE_H - M_BOTTOM) { doc.addPage(); y = M_TOP; }
      }

      // ASCII-only (Courier has limited glyphs)
      function ascii(s: string) {
        return s
          .replaceAll("→", "->").replaceAll("’", "'")
          .replaceAll("•", "-").replaceAll("–", "-").replaceAll("—", "-")
          .replaceAll("“", '"').replaceAll("”", '"')
          .replace(/[^\x20-\x7E]/g, "?");
      }

      function heading(title: string) {
        ensureSpace(18);
        doc.setFontSize(11);
        doc.setTextColor(22, 80, 184);
        doc.text(ascii(title), M_LEFT, y);
        y += 6;
        doc.setDrawColor(22, 80, 184);
        doc.line(M_LEFT, y, PAGE_W - M_RIGHT, y);
        y += 10;
        doc.setTextColor(0, 0, 0);
      }

      function subheading(title: string) {
        ensureSpace(14);
        doc.setFontSize(10);
        doc.setTextColor(22, 80, 184);
        doc.text(ascii(title), M_LEFT, y);
        doc.setTextColor(0, 0, 0);
        y += 12;
      }

      function writeLine(text: string, size = 10) {
        doc.setFontSize(size);
        const lines = doc.splitTextToSize(ascii(text), CONTENT_W) as string[];
        for (const ln of lines) { ensureSpace(LINE_BODY); doc.text(ln, M_LEFT, y); y += LINE_BODY; }
      }

      // monospace "table" (pads columns with spaces)
      function writeTable(headers: string[], rows: string[][]) {
        const cols = headers.length;
        const colWidths: number[] = Array.from({ length: cols }, (_, i) =>
          Math.max(headers[i].length, ...rows.map(r => (r[i] ?? "").length))
        );
        const pad = (s: string, n: number) => (s ?? "").padEnd(n, " ");
        const sep = "  |  ";

        const headerLine = headers.map((h, i) => pad(h, colWidths[i])).join(sep);
        const dash = headers.map((_, i) => "-".repeat(colWidths[i])).join(sep);

        writeLine(headerLine);
        writeLine(dash);
        rows.forEach(r => writeLine(r.map((c, i) => pad(c, colWidths[i])).join(sep)));
      }

      // Header
      doc.setFontSize(14);
      doc.text("NSCP 2015 Beam Check - Results", M_LEFT, y);
      y += LINE_HEAD;

      // Shorthands
      const g = data.geom;
      const fx = data.checks.flexure;
      const sh = data.checks.shear;
      const r  = data.reinforcement;
      const hadVu = typeof g.Vu_kN === "number" && isFinite(g.Vu_kN as number);
      const VuText = hadVu ? `${g.Vu_kN} kN` : "—";

      // Geometry & Materials
      heading("Geometry & Materials");
      writeLine(`b = ${g.b_mm} mm   h = ${g.h_mm} mm   cover = ${g.cover_mm} mm`);
      writeLine(`f'c = ${g.fc_MPa} MPa   fy(main) = ${g.fy_main_MPa} MPa   fy(st) = ${g.fy_stirrup_MPa} MPa`);
      writeLine(`Mu = ${g.Mu_kNm} kN-m   Vu = ${VuText}`);
      if (g.agg_mm != null) writeLine(`agg. size = ${g.agg_mm} mm`);
      if (g.stirrup_dia_mm) writeLine(`stirrup bar = phi ${g.stirrup_dia_mm} mm`);
      if (g.lightweight != null) writeLine(`concrete type: ${g.lightweight ? "lightweight" : "normal weight"}`);
      y += 4;

      // Reinforcement summary
      heading("Reinforcement");
      writeLine(`As(tension) = ${Math.round(r.tension_As_mm2)} mm^2   d = ${r.d_mm.toFixed(1)} mm`);
      writeLine(`rho = ${r.rho.toFixed(5)}   rho_min = ${r.rho_min.toFixed(5)}   rho_max = ${r.rho_max.toFixed(5)}`);
      writeLine(`As_min = ${Math.round(r.As_min_mm2)} mm^2   used_rho_min_for_capacity = ${r.used_rho_min_for_capacity ? "yes" : "no"}`);
      y += 4;

      // Flexure — detailed
      heading("Flexure");
      writeLine(`Assumptions per NSCP 2015 Sec. 422.2.2 (rectangular stress block):`);
      writeLine(`- a = beta1 * c,  with beta1 = ${fx.beta1.toFixed(3)}`);
      writeLine(`- Cc = 0.85 * f'c * b * a`);
      writeLine(`- Equilibrium (if compression steel inside block):  Cc + A's*(f's - 0.85*f'c) = As*fs`);
      writeLine(`- Strains: epsilon_t = 0.003 * (d - c) / c`);
      writeLine(`- Phi from epsilon_t (tension-controlled ramp 0.65 @0.002 -> 0.90 @0.005)`);

      y += 4;
      subheading("Section results");
      writeLine(`d = ${fx.d.toFixed(1)} mm   c = ${fx.c.toFixed(1)} mm   a = ${fx.a.toFixed(1)} mm`);
      writeLine(`epsilon_t = ${fx.eps_t.toFixed(5)}   phi = ${fx.phi.toFixed(3)}   (assumption used: ${ascii(fx.assumption_used)})`);
      writeLine(`phiMn = ${(fx.phi * fx.Mn_Nmm / 1e6).toFixed(2)} kN-m   Mu = ${g.Mu_kNm} kN-m   ${data.checks.flexure_ok ? "OK" : "NG"}`);
      y += 4;

      // Show all assumption cases tried
      const tried = (fx.derivation as any)?.assumptions_tried as any[] || [];
      if (tried.length) {
        subheading("Assumption cases tried");
        const headers = ["case", "c (mm)", "a (mm)", "fs (MPa)", "fs'(MPa)", "in block?", "consistent?"];
        const rows = tried.slice(0, 12).map((t: any) => [
          String(t.case ?? ""),
          (t.c_mm != null ? Number(t.c_mm).toFixed(1) : "-"),
          (t.a_mm != null ? Number(t.a_mm).toFixed(1) : "-"),
          (t.fs_MPa != null ? Number(t.fs_MPa).toFixed(1) : "-"),
          (t.fsp_MPa != null ? Number(t.fsp_MPa).toFixed(1) : "-"),
          (t.inside_block ? "yes" : "no"),
          (t.consistent ? "yes" : "no"),
        ]);
        writeTable(headers, rows);
        y += 4;
      }

      // Flexure references (summary)
      heading("NSCP 2015 references (summary) — Flexure");
      writeLine("- Sec. 422.2.2: 0.003 max strain at extreme compression; tensile strength of concrete neglected.");
      writeLine("- Rectangular block: Cc = 0.85*f'c*b*a, with a = beta1*c; beta1 per Table 422.2.2.4.3.");
      writeLine("- Strength reduction: phi per Table 421.2.1(a)/(b); linear ramp for tension-controlled 0.65->0.90.");
      writeLine("- Min. flexural steel (Sec. 409.6.1): As_min >= max( (0.25*sqrt(f'c)/fy)*bw*d , (1.4/fy)*bw*d ).");
      writeLine("- Max. flexural steel (proxy): rho_max = (3/8)*(0.85*beta1*f'c/fy).");
      writeLine("- Spacing & layering (Sec. 425.2): layer clear spacing >= max(25, db, 4/3*d_agg); layer gap >= 25 mm.");
      writeLine("- Concrete cover (Sec. 420.6.1.3, Table 420.6.1.3.1): typical CC >= 40-50 mm depending on bar/exposure.");
      y += 6;

      // Shear results (compact)
      heading("Shear (NSCP 2015)");
      writeLine(`lambda = ${sh.lambda_concrete.toFixed(2)}   Vc = ${sh.Vc_kN.toFixed(1)} kN   phi = ${sh.phi.toFixed(2)}`);
      writeLine(`Vs_req = ${sh.Vs_req_kN.toFixed(1)} kN   Vs_threshold = ${sh.Vs_threshold_kN.toFixed(1)} kN   table_case = ${ascii(sh.table_case)}`);
      writeLine(`s_req = ${isFinite(sh.s_req_mm) ? sh.s_req_mm.toFixed(1) : "—"} mm   s_min = ${sh.s_min_req_mm.toFixed(1)} mm   s_table = ${sh.s_table_max_mm.toFixed(1)} mm`);
      if (hadVu) {
        writeLine(`Provide s = ${sh.s_use_mm.toFixed(1)} mm  ->  phiVn = ${sh.phiVn_kN.toFixed(1)} kN   Vu = ${g.Vu_kN} kN   ${sh.ok ? "OK" : "NG"}`);
      } else {
        writeLine(`Provide s = ${sh.s_use_mm.toFixed(1)} mm  ->  phiVn = ${sh.phiVn_kN.toFixed(1)} kN   (Vu not provided; capacity only)`);
      }
      writeLine(`Dimensional limit phi*V (Sec. 422.5.1.2): ${sh.dim_limit_phiV_kN.toFixed(1)} kN   ${sh.ok_dim ? "OK" : "NG"}`);
      writeLine(`Note (Sec. 409.4.3): ${ascii(sh.support_shear_note)}`);
      y += 6;

      // Shear references (summary)
      heading("NSCP 2015 references (summary) — Shear");
      writeLine("- Vn = Vc + Vs (Sec. 422.5.1.1).");
      writeLine("- Vc = (1/6)*lambda*sqrt(f'c)*bw*d (Sec. 422.5.5); lambda = 1.00 normal, 0.75 lightweight.");
      writeLine("- Vs = Av*fyt*d/s (Sec. 422.5.10); Av for two-legged vertical stirrups.");
      writeLine("- phi_shear = 0.75 (Table 421.2.1.b).");
      writeLine("- Spacing (Table 409.7.6.2.2): if Vs_req <= 0.33*sqrt(f'c)*b*d -> s_max = min(d/2, 600); else min(d/4, 300).");
      writeLine("- Minimum transverse steel (Sec. 409.6.3, Table 409.6.3.3): Av/s >= max(0.062*sqrt(f'c)*bw/fyt, 0.35*bw/fyt).");
      writeLine("- Shear near supports (Sec. 409.4.3): Vu may be taken at face of support; section at d from face may be used if (a)-(c).");
      y += 6;

      // Sketch (optional)
      if (svgEl) {
        const targetImgW = Math.min(460, CONTENT_W);
        const targetImgH = Math.round((targetImgW * 2) / 3);
        ensureSpace(targetImgH + 12);
        const serializer = new XMLSerializer();
        const svgStr = serializer.serializeToString(svgEl);
        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");
        if (ctx) {
          canvas.width = targetImgW; canvas.height = targetImgH;
          const v = await Canvg.from(ctx, svgStr); await v.render();
          const png = canvas.toDataURL("image/png");
          doc.addImage(png, "PNG", M_LEFT, y, targetImgW, targetImgH);
          y += targetImgH + 12;
        }
      }

      // Footer
      doc.setFontSize(8);
      doc.text("Generated by NSCP Beam Calculator (frontend PDF)", M_LEFT, PAGE_H - M_BOTTOM);

      const blob = doc.output("blob");
      const nextUrl = URL.createObjectURL(blob);
      if (url) URL.revokeObjectURL(url);
      setUrl(nextUrl);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <button onClick={generate} disabled={busy} className="px-4 py-2 rounded-xl bg-black text-white disabled:opacity-60">
          {busy ? "Building PDF…" : "Generate PDF (Courier)"}
        </button>
        {url && (
          <a href={url} download="beam-results.pdf" className="px-3 py-2 rounded-lg bg-gray-900 text-white">
            Download PDF
          </a>
        )}
      </div>
      {url && (
        <div className="rounded-2xl overflow-hidden border">
          <iframe title="Beam PDF" src={url} className="w-full h-[720px]" />
        </div>
      )}
    </div>
  );
}
