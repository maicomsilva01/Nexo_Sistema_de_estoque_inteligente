import { ArrowRight, CircleAlert, PackageX } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { Alerta } from '../types';

interface Props { alertas: Alerta[]; limite?: number }
export default function AlertaEstoque({ alertas, limite = 5 }: Props) {
  const items = alertas.slice(0, limite);
  if (!items.length) return <div className="empty-state"><div className="empty-icon"><CircleAlert /></div>Nenhum item precisa de reposição agora.</div>;
  return <div className="alert-list">
    {items.map((a) => { const critical = a.severidade === 'ruptura'; const Icon = critical ? PackageX : CircleAlert; return <div className="alert-row" key={a.produto_id}>
      <span className={`alert-symbol ${critical ? 'critical' : ''}`}><Icon /></span>
      <span className="alert-main"><span className="alert-title">{a.nome}</span><span className="alert-description">{a.sku} · {critical ? 'sem saldo disponível' : `mínimo de ${a.estoque_minimo}`}</span></span>
      <span className="alert-count">{a.saldo} / {a.estoque_minimo}</span>
    </div>; })}
    {alertas.length > limite && <Link to="/alertas" className="panel-link" style={{ marginTop: 4 }}>Ver todos os {alertas.length} alertas <ArrowRight /></Link>}
  </div>;
}
