import { Activity, ArrowLeftRight, BellRing, Boxes, LayoutDashboard, Package, TrendingUp, Users } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import brandMark from '../assets/nexo-mark.svg';
import type { Usuario } from '../types';

const links = [
  { to: '/', label: 'Visão geral', icon: LayoutDashboard, end: true },
  { to: '/produtos', label: 'Produtos', icon: Package },
  { to: '/movimentacoes', label: 'Movimentações', icon: ArrowLeftRight },
  { to: '/estoque', label: 'Estoque', icon: Boxes },
  { to: '/previsoes', label: 'Previsões', icon: TrendingUp },
  { to: '/alertas', label: 'Alertas', icon: BellRing },
];

interface SidebarProps { open: boolean; onNavigate: () => void; user: Usuario }

export default function Sidebar({ open, onNavigate, user }: SidebarProps) {
  const visibleLinks = user.perfil === 'admin' ? [...links, { to: '/usuarios', label: 'Usuários', icon: Users }] : links;
  return <>
    <div className={`mobile-backdrop ${open ? 'visible' : ''}`} onClick={onNavigate} />
    <aside className={`sidebar ${open ? 'open' : ''}`}>
      <div className="brand"><img className="brand-mark" src={brandMark} alt="" aria-hidden="true" /><div><div className="brand-name">nexo estoque</div><div className="brand-sub">inteligência operacional</div></div></div>
      <div className="nav-label">Operação</div>
      <nav className="nav-list" aria-label="Navegação principal">
        {visibleLinks.map(({ to, label, icon: Icon, end }) => <NavLink key={to} to={to} end={end} onClick={onNavigate} className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}><Icon /><span>{label}</span></NavLink>)}
      </nav>
      <div className="sidebar-spacer" />
      <div className="sidebar-note"><div className="note-line"><span className="live-dot" /> Visão em tempo real</div><p>Saldo calculado a partir das movimentações registradas.</p></div>
      <div className="sidebar-foot"><Activity size={12} style={{ verticalAlign: 'middle', marginRight: 5 }} /> Sistema de estoque · v0.1</div>
    </aside>
  </>;
}
