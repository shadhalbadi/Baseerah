interface Point {
  label: string
  value: number
}

// Lightweight dependency-free SVG line chart. Time always flows left→right
// (chronological), independent of page direction.
export function ConsumptionChart({
  points,
  forecast,
  unit,
}: {
  points: Point[]
  forecast?: number
  unit: string
}) {
  if (points.length < 2) return null

  const W = 480
  const H = 160
  const P = 28 // padding

  const values = [...points.map((p) => p.value), ...(forecast != null ? [forecast] : [])]
  const max = Math.max(...values)
  const min = Math.min(...values, 0)
  const span = max - min || 1

  const n = points.length + (forecast != null ? 1 : 0)
  const x = (i: number) => P + (i * (W - 2 * P)) / (n - 1)
  const y = (v: number) => H - P - ((v - min) / span) * (H - 2 * P)

  const line = points.map((p, i) => `${x(i)},${y(p.value)}`).join(' ')
  const lastX = x(points.length - 1)
  const lastY = y(points[points.length - 1].value)

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className="w-full"
      role="img"
      aria-label="Consumption trend"
    >
      {/* baseline axis */}
      <line x1={P} y1={H - P} x2={W - P} y2={H - P} stroke="#e2e8f0" />
      {/* historical line */}
      <polyline points={line} fill="none" stroke="#059669" strokeWidth={2} />
      {points.map((p, i) => (
        <circle key={i} cx={x(i)} cy={y(p.value)} r={3} fill="#059669" />
      ))}
      {/* forecast segment (dashed) */}
      {forecast != null && (
        <>
          <line
            x1={lastX}
            y1={lastY}
            x2={x(n - 1)}
            y2={y(forecast)}
            stroke="#f59e0b"
            strokeWidth={2}
            strokeDasharray="4 3"
          />
          <circle cx={x(n - 1)} cy={y(forecast)} r={3.5} fill="#f59e0b" />
          <text x={x(n - 1)} y={y(forecast) - 8} fontSize={10} fill="#b45309" textAnchor="end">
            {forecast} {unit}
          </text>
        </>
      )}
    </svg>
  )
}
