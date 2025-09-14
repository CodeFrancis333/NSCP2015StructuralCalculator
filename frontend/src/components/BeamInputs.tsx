import { useState } from "react";
import type { BeamRequest } from "../types";

type Form = {
  width:string;height:string;cover:string;fc:string;agg_size:string;
  stirrup_dia:string;tension_bar_dia:string;compression_bar_dia:string;
  n_tension:string;n_compression:string;fy_main:string;fy_stirrup:string;Mu:string;Vu:string;
};

const init: Form = {
  width:"300", height:"500", cover:"40",
  fc:"27.6", agg_size:"20",
  stirrup_dia:"10", tension_bar_dia:"20", compression_bar_dia:"16",
  n_tension:"4", n_compression:"2",
  fy_main:"414", fy_stirrup:"275",
  Mu:"120", Vu:"180",
};

type Props = { onRun:(p:BeamRequest)=>Promise<void>; loading:boolean };

export default function BeamInputs({ onRun, loading }: Props) {
  const [f,setF] = useState<Form>(init);
  const [err,setErr] = useState<string|null>(null);

  const clsInput =
    "w-full px-3 py-2 rounded-lg border bg-white text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-lime-400";

  // keep everything as strings here; parse on submit only
  const set = (k: keyof Form) => (v: string) => setF(s => ({ ...s, [k]: v }));

  const toNum = (s: string) => s.trim() === "" ? NaN : Number(s.replace(",", "."));

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    const payload: BeamRequest = {
      width: toNum(f.width),
      height: toNum(f.height),
      cover: toNum(f.cover),
      fc: toNum(f.fc),
      agg_size: f.agg_size.trim()==="" ? null : toNum(f.agg_size),
      stirrup_dia: toNum(f.stirrup_dia),
      tension_bar_dia: toNum(f.tension_bar_dia),
      compression_bar_dia: f.compression_bar_dia.trim()==="" ? null : toNum(f.compression_bar_dia),
      n_tension: toNum(f.n_tension),
      n_compression: toNum(f.n_compression),
      fy_main: toNum(f.fy_main),
      fy_stirrup: toNum(f.fy_stirrup),
      Mu: toNum(f.Mu),
      Vu: toNum(f.Vu),
    };

    // quick client-side check for required fields
    const required = [
      payload.width, payload.height, payload.cover, payload.fc,
      payload.stirrup_dia, payload.tension_bar_dia, payload.n_tension,
      payload.fy_main, payload.fy_stirrup, payload.Mu, payload.Vu,
    ];
    if (required.some(x => !Number.isFinite(x))) {
      setErr("Please complete required numeric fields.");
      return;
    }

    await onRun(payload);
  }

  return (
    <form onSubmit={submit} className="space-y-3">
      <Panel title="Beam Geometry">
        <Field label="b (mm)" v={f.width} set={set("width")} cls={clsInput}/>
        <Field label="h (mm)" v={f.height} set={set("height")} cls={clsInput}/>
        <Field label="cover (mm)" v={f.cover} set={set("cover")} cls={clsInput}/>
      </Panel>

      <Panel title="Concrete Properties">
        <Field label="f'c (MPa)" v={f.fc} set={set("fc")} cls={clsInput}/>
        <Field label="agg. size (mm)" v={f.agg_size} set={set("agg_size")} cls={clsInput}/>
      </Panel>

      <Panel title="Steel Properties">
        <Field label="stirrup φ (mm)" v={f.stirrup_dia} set={set("stirrup_dia")} cls={clsInput}/>
        <Field label="tension bar φ (mm)" v={f.tension_bar_dia} set={set("tension_bar_dia")} cls={clsInput}/>
        <Field label="comp. bar φ (mm)" v={f.compression_bar_dia} set={set("compression_bar_dia")} cls={clsInput}/>
        <Field label="# tension bars" v={f.n_tension} set={set("n_tension")} cls={clsInput}/>
        <Field label="# comp. bars" v={f.n_compression} set={set("n_compression")} cls={clsInput}/>
        <Field label="fyt (MPa)" v={f.fy_main} set={set("fy_main")} cls={clsInput}/>
        <Field label="fys (MPa)" v={f.fy_stirrup} set={set("fy_stirrup")} cls={clsInput}/>
      </Panel>

      <Panel title="Beam Loads">
        <Field label="Mu (kN·m)" v={f.Mu} set={set("Mu")} cls={clsInput}/>
        <Field label="Vu (kN)" v={f.Vu} set={set("Vu")} cls={clsInput}/>
      </Panel>

      {err && <div className="text-sm text-red-700 bg-red-50 border border-red-200 p-2 rounded">{err}</div>}

      <button disabled={loading} className="px-4 py-2 rounded-xl bg-black text-white disabled:opacity-60">
        {loading ? "Running…" : "Run"}
      </button>
    </form>
  );
}

function Panel({title, children}:{title:string; children:React.ReactNode}) {
  // matches your dark panel while keeping inputs readable
  return (
    <div className="rounded-2xl p-4 bg-gradient-to-b from-gray-800 to-gray-900 text-gray-100 shadow">
      <div className="font-semibold mb-3">{title}</div>
      <div className="grid gap-3 sm:grid-cols-2">{children}</div>
    </div>
  );
}
function Field({label, v, set, cls}:{label:string; v:string; set:(s:string)=>void; cls:string}) {
  return (
    <label className="text-sm grid gap-1">
      <span className="text-gray-100">{label}</span>
      {/* IMPORTANT: text input with string value so focus is never lost */}
      <input
        type="text"
        inputMode="decimal"
        pattern="[0-9]*[.,]?[0-9]*"
        autoComplete="off"
        className={cls}
        value={v}
        onChange={(e)=>set(e.target.value)}
      />
    </label>
  );
}

