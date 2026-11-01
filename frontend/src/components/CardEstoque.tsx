import type { LucideIcon } from 'lucide-react';

interface CardEstoqueProps {
  label: string;
  value: string;
  foot: string;
  icon: LucideIcon;
  tone?: 'normal' | 'warning' | 'danger';
}

export default function CardEstoque({ label, value, foot, icon: Icon, tone = 'normal' }: CardEstoqueProps) {
  return <article className={`metric-card ${tone}`}>
    <div className="metric-top"><span>{label}</span><span className="metric-icon"><Icon /></span></div>
    <div className="metric-value">{value}</div>
    <div className="metric-foot">{foot}</div>
  </article>;
}
