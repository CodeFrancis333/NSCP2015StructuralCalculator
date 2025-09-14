// src/pages/BeamPage.tsx
import { useRef, useState } from "react";
import BeamInputs from "../components/BeamInputs";
import BeamResults from "../components/BeamResults";
import BeamSketch from "../components/BeamSketch";
import PdfReport from "../components/PdfReport"; // <-- add if you created it
import { calcBeam } from "../api";
import type { BeamRequest, BeamResponse } from "../types";

export default function BeamPage() {
  const [data, setData] = useState<BeamResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);

  async function run(payload: BeamRequest) {
    setLoading(true); setError(null);
    try { setData(await calcBeam(payload)); }
    catch (e: any) { setError(e.message ?? String(e)); }
    finally { setLoading(false); }
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-semibold">Reinforced Concrete Beam Calculator</h1>
        <p className="text-sm opacity-70">Real-time visualization • NSCP 2015 flexure & shear • Detailed export</p>
      </div>

      <div className="grid lg:grid-cols-[minmax(0,1fr)_380px] gap-6">
        {/* left: drawing */}
        <div className="rounded-2xl bg-gray-200 p-4 overflow-hidden">
          {data ? (
            <BeamSketch
              ref={svgRef}  // <-- attach the ref here
              b_mm={data.geom.b_mm}
              h_mm={data.geom.h_mm}
              stirrup={data.rebar_layout.stirrup_inside}
              bars={data.rebar_layout.bars}
            />
          ) : (
            <div className="text-sm text-gray-600">Run the calculator to see the cross section.</div>
          )}
        </div>

        {/* right: inputs */}
        <div>
          <div className="rounded-2xl overflow-hidden min-w-0">
            <BeamInputs onRun={run} loading={loading} />
          </div>
        </div>
      </div>

      {error && (
        <div className="text-sm text-red-600 whitespace-pre-wrap border border-red-200 bg-red-50 p-3 rounded">
          {error}
        </div>
      )}

      <div className="grid lg:grid-cols-2 gap-6">
        <BeamResults data={data} />
      </div>

      {/* PDF preview/export */}
      {data && (
        <div className="rounded-2xl bg-white p-4 shadow">
          <div className="font-semibold mb-2">PDF Report</div>
          <PdfReport data={data} svgEl={svgRef.current} />
        </div>
      )}
    </div>
  );
}
