import { Bell, LogOut, Menu } from 'lucide-react';
import type { Usuario } from '../types';

interface HeaderProps {
  title: string;
  user: Usuario;
  onLogout: () => void;
  onMenu: () => void;
}

export default function Header({ title, user, onLogout, onMenu }: HeaderProps) {
  const initials = user.nome.trim().split(/\s+/).slice(0, 2).map((part) => part[0]).join('').toUpperCase();
  const roleLabel = user.perfil === 'admin' ? 'Administrador' : 'Operador';
  return (
    <header className="topbar">
      <div className="topbar-left">
        <button className="icon-button mobile-menu" onClick={onMenu} aria-label="Abrir navegação"><Menu /></button>
        <div><h1>{title}</h1><div className="crumb">Operação · Nexo Estoque</div></div>
      </div>
      <div className="topbar-actions">
        <button className="icon-button" aria-label="Ver alertas" onClick={() => { window.location.href = '/alertas'; }}><Bell /></button>
        <div className="user-chip">
          <span className="avatar">{initials || 'NE'}</span>
          <div><div className="user-name">{user.nome || 'Operador'}</div><div className="user-role">{roleLabel}</div></div>
        </div>
        <button className="icon-button" aria-label="Sair da conta" title="Sair" onClick={onLogout}><LogOut /></button>
      </div>
    </header>
  );
}
