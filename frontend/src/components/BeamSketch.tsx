import { forwardRef } from "react";
import type { Bar, StirrupRect } from "../types";

type Props = { b_mm: number; h_mm: number; stirrup: StirrupRect; bars: Bar[] };

const BeamSketch = forwardRef<SVGSVGElement, Props>(function BeamSketch(
  { b_mm, h_mm, stirrup, bars }, ref
) {
  const W = 480, H = 360, M = 40;
  const scale = Math.min((W - 2*M) / b_mm, (H - 2*M) / h_mm);
  const sx = (x:number) => M + x * scale;
  const sy = (y:number) => H - M - y * scale;

  return (
    <div className="w-full flex items-center justify-center">
      <svg ref={ref} viewBox={`0 0 ${W} ${H}`} className="block w-full max-w-[560px] h-auto">
        <rect x={sx(0)} y={sy(h_mm)} width={b_mm*scale} height={h_mm*scale} fill="#d1d5db" stroke="#111827" />
        <rect
          x={sx(stirrup.x_min)} y={sy(stirrup.y_max)}
          width={(stirrup.x_max - stirrup.x_min)*scale}
          height={(stirrup.y_max - stirrup.y_min)*scale}
          fill="none" stroke="#6b7280" strokeDasharray="6 4" strokeWidth={2}
        />
        {bars.map((b,i)=>(
          <circle key={i} cx={sx(b.x_mm)} cy={sy(b.y_mm)}
                  r={Math.max(3,(b.dia_mm*scale)/2.2)}
                  fill={b.role==='tension' ? '#0ea5e9' : '#f59e0b'}
                  stroke="#111827"/>
        ))}
        <line x1={sx(0)} y1={sy(-14)} x2={sx(b_mm)} y2={sy(-14)} stroke="#111827" />
        <text x={(sx(0)+sx(b_mm))/2} y={sy(-22)} textAnchor="middle" fontSize="12" fill="#111827">
          {Math.round(b_mm)} mm
        </text>
        <line x1={sx(-14)} y1={sy(0)} x2={sx(-14)} y2={sy(h_mm)} stroke="#111827" />
        <text x={sx(-22)} y={(sy(0)+sy(h_mm))/2}
              transform={`rotate(-90 ${sx(-22)} ${(sy(0)+sy(h_mm))/2})`}
              textAnchor="middle" fontSize="12" fill="#111827">
          {Math.round(h_mm)} mm
        </text>
      </svg>
    </div>
  );
});

export default BeamSketch;
