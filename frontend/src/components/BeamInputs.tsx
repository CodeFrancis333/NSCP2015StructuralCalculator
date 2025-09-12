import { useState } from "react";
import type { BeamRequest } from "../types";

const defaults: BeamRequest = {
  width: 300, height: 500, cover: 40,
  fc: 27.6, agg_size: 20,
  stirrup_dia: 10, tension_bar_dia: 20, compression_bar_dia: 16,
  n_tension: 4, n_compression: 2,
  fy_main: 414, fy_stirrup: 275,
  Mu: 120, Vu: 180,
};

type Props = { onRun: (p: BeamRequest) => Promise<void>; loading: boolean };

export default function BeamInputs({ onRun, loading }: Props) {
  const [f, setF] = useState<BeamRequest>(defaults);
  const input = "w-full px-3 py-2 rounded-lg border bg-white";

  function set<K extends keyof BeamRequest>(k: K, v: string) {
    const n = v === "" ? (undefined as any) : Number(v);
    setF((p) => ({ ...p, [k]: n }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    await onRun(f);
  }

  return (
    <form onSubmit={submit} className="space-y-3 text-sm">
      <Section title="Beam Geometry">
        <Row><Label>b (mm)</Label><Input val={f.width} onChange={(v)=>set("width", v)} /></Row>
        <Row><Label>h (mm)</Label><Input val={f.height} onChange={(v)=>set("height", v)} /></Row>
        <Row><Label>cover (mm)</Label><Input val={f.cover} onChange={(v)=>set("cover", v)} /></Row>
      </Section>

      <Section title="Concrete Properties">
        <Row><Label>f'c (MPa)</Label><Input val={f.fc} onChange={(v)=>set("fc", v)} /></Row>
        <Row><Label>Aggregate (mm)</Label><Input val={f.agg_size ?? 0} onChange={(v)=>set("agg_size", v)} /></Row>
      </Section>

      <Section title="Steel Properties">
        <Row><Label>stirrup φ (mm)</Label><Input val={f.stirrup_dia} onChange={(v)=>set("stirrup_dia", v)} /></Row>
        <Row><Label>ten. bar φ (mm)</Label><Input val={f.tension_bar_dia} onChange={(v)=>set("tension_bar_dia", v)} /></Row>
        <Row><Label>comp. bar φ (mm)</Label><Input val={f.compression_bar_dia ?? 0} onChange={(v)=>set("compression_bar_dia", v)} /></Row>
        <Row><Label># tension bars</Label><Input val={f.n_tension} onChange={(v)=>set("n_tension", v)} /></Row>
        <Row><Label># comp. bars</Label><Input val={f.n_compression ?? 0} onChange={(v)=>set("n_compression", v)} /></Row>
        <Row><Label>fyt (MPa)</Label><Input val={f.fy_main} onChange={(v)=>set("fy_main", v)} /></Row>
        <Row><Label>fys (MPa)</Label><Input val={f.fy_stirrup} onChange={(v)=>set("fy_stirrup", v)} /></Row>
      </Section>

      <Section title="Beam Loads">
        <Row><Label>Mu (kN·m)</Label><Input val={f.Mu} onChange={(v)=>set("Mu", v)} /></Row>
        <Row><Label>Vu (kN)</Label><Input val={f.Vu} onChange={(v)=>set("Vu", v)} /></Row>
      </Section>

      <button disabled={loading} className="px-4 py-2 rounded-xl bg-black text-white disabled:opacity-60">
        {loading ? "Running…" : "Run"}
      </button>
    </form>
  );

  function Section({ title, children }: { title: string; children: React.ReactNode }) {
    return (
      <div className="rounded-2xl bg-white text-gray-900 p-4 shadow">
        <div className="font-semibold mb-3">{title}</div>
        <div className="grid grid-cols-2 gap-3 max-[520px]:grid-cols-1">{children}</div>
      </div>
    );
  }
  function Row({ children }: { children: React.ReactNode }) { return <div className="contents">{children}</div> }
  function Label({ children }: { children: React.ReactNode }) { return <div className="self-center opacity-90">{children}</div> }
  function Input({ val, onChange }: { val: number; onChange: (v: string)=>void }) {
    return <input className={input} type="number" value={val} onChange={(e)=>onChange(e.target.value)} />;
  }
}
