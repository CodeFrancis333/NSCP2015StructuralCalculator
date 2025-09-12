import type { BeamResponse } from "../types";

export default function BeamResults({ data }: { data: BeamResponse | null }) {
  if (!data) return <div className="text-sm text-gray-500">No results yet.</div>;
  const { checks, latex } = data;
  const chip = (ok:boolean) => (
    <span className={`px-2 py-1 rounded-full text-xs ${ok?'bg-green-100 text-green-700':'bg-red-100 text-red-700'}`}>
      {ok?'OK':'NG'}
    </span>
  );
  const downloadTex = () => {
    const blob = new Blob([latex], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "beam_report.tex"; a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4">
      <div className="rounded-2xl bg-white p-4 shadow">
        <div className="font-semibold mb-2">Summary</div>
        <div className="text-sm space-y-1">
          <div>φMₙ = <b>{checks.flexure_capacity_kNm.toFixed(2)}</b> kN·m {chip(checks.flexure_ok)}</div>
          <div>φVₙ = <b>{checks.shear.phiVn_kN.toFixed(2)}</b> kN {chip(checks.shear.ok)} – provide s = <b>{checks.shear.s_use_mm.toFixed(0)}</b> mm</div>
        </div>
        <button onClick={downloadTex} className="mt-3 px-3 py-2 rounded-xl bg-gray-900 text-white">Export LaTeX</button>
      </div>
      <div className="rounded-2xl bg-white p-4 shadow">
        <details>
          <summary className="cursor-pointer font-semibold">Raw JSON</summary>
          <pre className="mt-2 text-xs overflow-auto">{JSON.stringify(data, null, 2)}</pre>
        </details>
      </div>
    </div>
  );
}
