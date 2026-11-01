import type { SerieConsumo } from '../types';

interface Props { serie: SerieConsumo[] }
export default function GraficoConsumo({ serie }: Props) {
  if (!serie.length || serie.every((day) => day.quantidade === 0)) return <div className="empty-state">O gráfico aparece quando houver consumo registrado.</div>;
  const width = 620; const height = 190; const left = 28; const right = 12; const top = 12; const bottom = 27;
  const max = Math.max(1, ...serie.map((day) => day.quantidade));
  const usableWidth = width - left - right; const usableHeight = height - top - bottom;
  const points = serie.map((day, index) => {
    const x = left + (serie.length === 1 ? usableWidth / 2 : index * usableWidth / (serie.length - 1));
    const y = top + usableHeight - (day.quantidade / max) * usableHeight;
    return { x, y, value: day.quantidade, label: day.dia };
  });
  const line = points.map((p) => `${p.x},${p.y}`).join(' ');
  const area = `${left},${top + usableHeight} ${line} ${left + usableWidth},${top + usableHeight}`;
  const labels = [points[0], points[Math.floor((points.length - 1) / 2)], points[points.length - 1]].filter((p, i, all) => p && all.findIndex((q) => q.label === p.label) === i);
  return <div className="chart-wrap" role="img" aria-label="Gráfico do consumo diário dos últimos 30 dias">
    <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
      <defs><linearGradient id="chartFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#32c48d" stopOpacity=".2"/><stop offset="100%" stopColor="#32c48d" stopOpacity="0"/></linearGradient></defs>
      {[0, 1, 2, 3].map((i) => { const y = top + i * usableHeight / 3; return <line key={i} x1={left} x2={width - right} y1={y} y2={y} className="chart-grid" />; })}
      <polygon points={area} className="chart-area" />
      <polyline points={line} className="chart-line" />
      {points.filter((_, i) => i === 0 || i === points.length - 1 || i % 7 === 0).map((p) => <circle key={p.label} cx={p.x} cy={p.y} r="3.5" className="chart-dot"><title>{p.label}: {p.value} unidades</title></circle>)}
      {labels.map((p) => <text key={p.label} x={p.x} y={height - 4} textAnchor="middle" className="chart-label">{p.label.slice(5)}</text>)}
    </svg>
  </div>;
}
