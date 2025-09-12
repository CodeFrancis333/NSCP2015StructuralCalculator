import type { Bar, StirrupRect } from "../types";

type Props = { b_mm: number; h_mm: number; stirrup: StirrupRect; bars: Bar[] };

export default function BeamSketch({ b_mm, h_mm, stirrup, bars }: Props) {
  // Fixed canvas with margins; scale both directions to fit whatever the inputs are.
  const W = 420, H = 320, M = 36;
  const scale = Math.min((W - 2*M) / b_mm, (H - 2*M) / h_mm);
  const sx = (x: number) => M + x * scale;
  const sy = (y: number) => H - M - y * scale;

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      preserveAspectRatio="xMidYMid meet"
      className="w-full max-w-[520px] mx-auto h-auto"
    >
      {/* concrete outline */}
      <rect x={sx(0)} y={sy(h_mm)} width={b_mm*scale} height={h_mm*scale} fill="#e5e7eb" stroke="#111827" />

      {/* stirrup rectangle (inside) */}
      <rect
        x={sx(stirrup.x_min)} y={sy(stirrup.y_max)}
        width={(stirrup.x_max - stirrup.x_min) * scale}
        height={(stirrup.y_max - stirrup.y_min) * scale}
        fill="none" stroke="#6b7280" strokeDasharray="6 4" strokeWidth={2}
      />

      {/* bars */}
      {bars.map((b, i) => (
        <circle
          key={i}
          cx={sx(b.x_mm)} cy={sy(b.y_mm)}
          r={Math.max(3, (b.dia_mm * scale) / 2.4)}
          fill={b.role === "tension" ? "#0ea5e9" : "#f59e0b"}
          stroke="#111827"
        />
      ))}

      {/* dimensions */}
      {/* width */}
      <line x1={sx(0)} y1={sy(-12)} x2={sx(b_mm)} y2={sy(-12)} stroke="#111827" markerStart="" />
      <text x={(sx(0)+sx(b_mm))/2} y={sy(-18)} textAnchor="middle" fontSize="12" fill="#111827">
        {Math.round(b_mm)} mm
      </text>

      {/* height */}
      <line x1={sx(-12)} y1={sy(0)} x2={sx(-12)} y2={sy(h_mm)} stroke="#111827" />
      <text x={sx(-18)} y={(sy(0)+sy(h_mm))/2} transform={`rotate(-90 ${sx(-18)} ${(sy(0)+sy(h_mm))/2})`} textAnchor="middle" fontSize="12" fill="#111827">
        {Math.round(h_mm)} mm
      </text>
    </svg>
  );
}
