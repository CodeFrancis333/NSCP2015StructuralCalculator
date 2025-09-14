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
    return () => {
      if (url) URL.revokeObjectURL(url);
    };
  }, [url]);

  async function generate() {
    setBusy(true);
    try {
      const doc = new jsPDF({ unit: "pt", format: "a4" });
      doc.setFont("courier", "normal"); // built-in; reliable but ASCII-only

      // Page geometry
      const PAGE_W = doc.internal.pageSize.getWidth();
      const PAGE_H = doc.internal.pageSize.getHeight();

      const M_LEFT = 54;
      const M_RIGHT = 54;
      const M_TOP = 64;
      const M_BOTTOM = 22;

      // Slightly conservative content width to avoid rounding spill
      const CONTENT_W = PAGE_W - M_LEFT - M_RIGHT - 8;

      let y = M_TOP;
      const LINE_BODY = 12;
      const LINE_HEAD = 22;

      function ensureSpace(needed: number) {
        if (y + needed > PAGE_H - M_BOTTOM) {
          doc.addPage();
          y = M_TOP;
        }
      }

      // Replace non-ASCII with safe ASCII so jsPDF measures/wraps correctly.
      function asciiSanitize(s: string): string {
        return s
          .replaceAll("→", "->")
          .replaceAll("’", "'")
          .replaceAll("“", '"')
          .replaceAll("”", '"')
          .replace(/[^\x20-\x7E]/g, "?");
      }

      function section(title: string) {
        doc.setFontSize(10);
        ensureSpace(14);
        doc.text(asciiSanitize(title), M_LEFT, y);
        y += 14;
      }

      function writeLine(text: string, size = 10) {
        doc.setFontSize(size);
        const sanitized = asciiSanitize(text);
        const out = doc.splitTextToSize(sanitized, CONTENT_W);
        const lines: string[] = Array.isArray(out) ? (out as string[]) : [String(out)];
        for (const ln of lines) {
          ensureSpace(LINE_BODY);
          doc.text(ln, M_LEFT, y);
          y += LINE_BODY;
        }
      }

      // Header
      doc.setFontSize(14);
      doc.text("NSCP 2015 Beam Check - Results", M_LEFT, y);
      y += LINE_HEAD;

      // Shorthands
      const g = data.geom;
      const fx = data.checks.flexure;
      const sh = data.checks.shear;
      const r: any = (data as any).reinforcement ?? null; // optional extra block

      // Geometry & Materials
      section("Geometry & Materials");
      writeLine(`b = ${g.b_mm} mm   h = ${g.h_mm} mm   cover = ${g.cover_mm} mm`);
      writeLine(`f'c = ${g.fc_MPa} MPa   fy(main) = ${g.fy_main_MPa} MPa   fy(st) = ${g.fy_stirrup_MPa} MPa`);
      y += 4;

      // Reinforcement (optional)
      if (r) {
        section("Reinforcement");
        if (typeof r.tension_As_mm2 === "number") {
          writeLine(`As(tension) = ${Math.round(r.tension_As_mm2)} mm^2   d = ${r.d_mm.toFixed(1)} mm`);
        }
        if (typeof r.rho === "number" && typeof r.rho_min === "number" && typeof r.rho_max === "number") {
          writeLine(
            `rho = ${r.rho.toFixed(5)}   rho_min = ${r.rho_min.toFixed(5)}   rho_max = ${r.rho_max.toFixed(5)}`
          );
        }
        if (typeof r.As_min_mm2 === "number") {
          writeLine(
            `As_min = ${Math.round(r.As_min_mm2)} mm^2   used_rho_min_for_capacity = ${
              r.used_rho_min_for_capacity ? "yes" : "no"
            }`
          );
        }
        y += 4;
      }

      // Flexure
      section("Flexure");
      writeLine(`beta1 = ${fx.beta1.toFixed(3)}   c = ${fx.c.toFixed(1)} mm   a = ${fx.a.toFixed(1)} mm`);
      writeLine(`epsilon_t = ${fx.eps_t.toFixed(5)}   phi = ${fx.phi.toFixed(3)}`);
      writeLine(
        `phiMn = ${(fx.phi * fx.Mn_Nmm / 1e6).toFixed(2)} kN-m   Mu = ${g.Mu_kNm} kN-m   ${
          data.checks.flexure_ok ? "OK" : "NG"
        }`
      );
      y += 4;

      // Shear
      section("Shear");
      writeLine(`Vc = ${sh.Vc_kN.toFixed(1)} kN   phi = ${sh.phi.toFixed(2)}`);
      writeLine(
        `s_req = ${sh.s_req_mm.toFixed(1)} mm   s_code_min = ${sh.s_min_req_mm.toFixed(1)} mm   s_max = ${sh.s_max_mm.toFixed(1)} mm`
      );
      writeLine(
        `Provide s = ${sh.s_use_mm.toFixed(1)} mm  ->  phiVn = ${sh.phiVn_kN.toFixed(1)} kN   Vu = ${g.Vu_kN} kN   ${
          sh.ok ? "OK" : "NG"
        }`
      );
      y += 6;

      // Beam Sketch (SVG -> PNG), scaled to fit width
      if (svgEl) {
        const targetImgW = Math.min(460, CONTENT_W); // keep within content
        const targetImgH = Math.round((targetImgW * 2) / 3);

        ensureSpace(targetImgH + 12);

        const serializer = new XMLSerializer();
        const svgStr = serializer.serializeToString(svgEl);

        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");
        if (ctx) {
          canvas.width = targetImgW;
          canvas.height = targetImgH;

          const v = await Canvg.from(ctx, svgStr);
          await v.render();

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
        <button
          onClick={generate}
          disabled={busy}
          className="px-4 py-2 rounded-xl bg-black text-white disabled:opacity-60"
        >
          {busy ? "Building PDF…" : "Generate PDF (Courier)"}
        </button>

        {url && (
          <a
            href={url}
            download="beam-results.pdf"
            className="px-3 py-2 rounded-lg bg-gray-900 text-white"
          >
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
