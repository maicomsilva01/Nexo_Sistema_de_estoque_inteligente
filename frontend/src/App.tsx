import { useEffect, useState } from 'react';
import { BrowserRouter, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { api } from './services/api';
import type { Usuario } from './types';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Produtos from './pages/Produtos';
import Movimentacoes from './pages/Movimentacoes';
import Estoque from './pages/Estoque';
import Previsoes from './pages/Previsoes';
import Alertas from './pages/Alertas';
import PrimeiroAcesso from './pages/PrimeiroAcesso';
import Usuarios from './pages/Usuarios';

function AppRoutes() {
  const [user, setUser] = useState<Usuario | null>(null);
  const [checking, setChecking] = useState(true);
  const [menuOpen, setMenuOpen] = useState(false);
  const [error, setError] = useState('');
  const [bootstrapAvailable, setBootstrapAvailable] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    let alive = true;
    api.authStatus()
      .then((result) => { if (alive) { setUser(result.usuario); setBootstrapAvailable(result.bootstrap_disponivel); setError(''); } })
      .catch((reason: unknown) => {
        if (alive) { setBootstrapAvailable(false); setError(reason instanceof Error ? reason.message : 'Falha ao verificar a sessão.'); }
      })
      .finally(() => { if (alive) setChecking(false); });
    return () => { alive = false; };
  }, [location.key]);

  async function logout() {
    try { await api.logout(); } finally { setUser(null); navigate('/login'); }
  }

  if (checking) return <div className="boot-screen"><span className="brand-mark">N</span><span>Preparando seu estoque…</span></div>;
  if (location.pathname === '/primeiro-acesso') {
    if (user) return <Navigate to="/" replace />;
    if (bootstrapAvailable) return <PrimeiroAcesso />;
    return <Login initialError="O primeiro administrador já foi configurado. Entre com sua conta." />;
  }
  if (location.pathname === '/login') {
    if (user) return <Navigate to="/" replace />;
    return <Login initialError={error} bootstrapAvailable={bootstrapAvailable} />;
  }
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;

  const titleByPath: Record<string, string> = {
    '/': 'Visão geral', '/produtos': 'Produtos', '/movimentacoes': 'Movimentações',
    '/estoque': 'Estoque', '/previsoes': 'Previsões', '/alertas': 'Alertas', '/usuarios': 'Usuários',
  };
  return (
    <div className="app-shell">
      <Sidebar open={menuOpen} onNavigate={() => setMenuOpen(false)} user={user} />
      <div className="main-area">
        <Header title={titleByPath[location.pathname] ?? 'Estoque'} user={user} onLogout={logout} onMenu={() => setMenuOpen((open) => !open)} />
        <main className="page-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/produtos" element={<Produtos />} />
            <Route path="/movimentacoes" element={<Movimentacoes />} />
            <Route path="/estoque" element={<Estoque />} />
            <Route path="/previsoes" element={<Previsoes />} />
            <Route path="/alertas" element={<Alertas />} />
            <Route path="/usuarios" element={user.perfil === 'admin' ? <Usuarios /> : <Navigate to="/" replace />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return <BrowserRouter><AppRoutes /></BrowserRouter>;
}
