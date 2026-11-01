import { useState, type FormEvent } from 'react';
import { ArrowRight, Boxes, Radio, ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';

interface Props { initialError?: string; bootstrapAvailable?: boolean }

export default function Login({ initialError = '', bootstrapAvailable = false }: Props) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(initialError);

  async function enter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError('');
    try {
      await api.login(username, password, window.location.origin);
      setPassword('');
      window.location.assign('/');
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Não foi possível validar suas credenciais.');
      setPassword('');
      setLoading(false);
    }
  }

  return <div className="login-screen">
    <section className="login-showcase">
      <div className="login-brand"><div className="brand-mark">N</div><strong>nexo estoque</strong></div>
      <div className="login-copy">
        <div className="eyebrow">Inteligência operacional</div>
        <h1>Estoque sob controle, antes da ruptura.</h1>
        <p>Uma leitura mais clara do que entra, do que sai e do que precisa de atenção — para a operação não ser pega de surpresa.</p>
        <div className="login-graphic"><div className="login-graphic-title">FLUXO DE INVENTÁRIO · AO VIVO</div><div className="signal-flow"><div className="signal-box"><Boxes /></div><span className="signal-line" /><div className="signal-box"><Radio /></div><span className="signal-line" /><div className="signal-box"><ArrowRight /></div></div><div className="signal-label">produto → leitura RFID → movimentação rastreável</div></div>
      </div>
      <div className="login-foot">© {new Date().getFullYear()} Nexo Estoque · Painel operacional</div>
    </section>
    <section className="login-panel">
      <div className="login-box">
        <div className="eyebrow">Acesso individual</div>
        <h2>Entre na operação</h2>
        <p>Use o nome de usuário e a senha definidos para sua conta individual.</p>
        {error && <div className="toast error login-error" role="alert">{error}</div>}
        <form onSubmit={enter}>
          <label className="field login-field">
            <span>Usuário</span>
            <input
              autoComplete="username"
              className="input"
              maxLength={32}
              minLength={3}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="Turma2"
              required
              type="text"
              value={username}
            />
          </label>
          <label className="field login-field">
            <span>Senha</span>
            <input
              autoComplete="current-password"
              className="input"
              maxLength={128}
              minLength={12}
              onChange={(event) => setPassword(event.target.value)}
              required
              type="password"
              value={password}
            />
          </label>
          <button className="button button-primary login-button" type="submit" disabled={loading}>
            {loading ? 'Validando…' : 'Entrar no estoque'} {!loading && <ArrowRight size={15} />}
          </button>
        </form>
        <div className="login-security"><ShieldCheck size={13} style={{ verticalAlign: 'middle', marginRight: 5 }} />Cada movimentação fica associada à pessoa autenticada.</div>
        {bootstrapAvailable && <div className="login-help"><Link to="/primeiro-acesso">Configurar o primeiro administrador</Link></div>}
      </div>
    </section>
  </div>;
}
