import { useState, type FormEvent } from 'react';
import { ArrowRight, Boxes, Radio, ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';

export default function PrimeiroAcesso() {
  const [bootstrapKey, setBootstrapKey] = useState('');
  const [name, setName] = useState('');
  const [username, setUsername] = useState('Turma2');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function createFirstAdmin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError('');
    try {
      await api.bootstrapAdmin({
        chave_bootstrap: bootstrapKey,
        nome: name,
        username,
        email: email.trim() || null,
        senha: password,
        origin: window.location.origin,
      });
      setBootstrapKey('');
      setPassword('');
      window.location.assign('/');
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Não foi possível configurar o administrador.');
      setBootstrapKey('');
      setPassword('');
      setLoading(false);
    }
  }

  return <div className="login-screen">
    <section className="login-showcase">
      <div className="login-brand"><div className="brand-mark">N</div><strong>nexo estoque</strong></div>
      <div className="login-copy">
        <div className="eyebrow">Configuração protegida</div>
        <h1>O primeiro acesso define quem administra.</h1>
        <p>Crie a conta responsável pelo painel. Este formulário só funciona com a chave privada de bootstrap e é fechado depois da criação do administrador.</p>
        <div className="login-graphic"><div className="login-graphic-title">PROVISIONAMENTO · USO ÚNICO</div><div className="signal-flow"><div className="signal-box"><Boxes /></div><span className="signal-line" /><div className="signal-box"><Radio /></div><span className="signal-line" /><div className="signal-box"><ShieldCheck /></div></div><div className="signal-label">username individual → permissão admin → cadastro fechado</div></div>
      </div>
      <div className="login-foot">© {new Date().getFullYear()} Nexo Estoque · Painel operacional</div>
    </section>
    <section className="login-panel">
      <div className="login-box">
        <div className="eyebrow">Primeiro administrador</div>
        <h2>Configurar acesso</h2>
        <p>Informe a chave recebida pelo canal seguro, escolha sua senha e confirme o nome de usuário.</p>
        {error && <div className="toast error login-error" role="alert">{error}</div>}
        <form onSubmit={createFirstAdmin} className="first-admin-form">
          <label className="field login-field"><span>Chave de primeiro acesso</span><input className="input" type="password" autoComplete="off" minLength={32} maxLength={256} value={bootstrapKey} onChange={(event) => setBootstrapKey(event.target.value)} required /></label>
          <label className="field login-field"><span>Nome</span><input className="input" type="text" autoComplete="name" minLength={2} maxLength={160} value={name} onChange={(event) => setName(event.target.value)} required /></label>
          <label className="field login-field"><span>Usuário</span><input className="input" type="text" autoComplete="username" minLength={3} maxLength={32} value={username} onChange={(event) => setUsername(event.target.value)} required /></label>
          <label className="field login-field"><span>E-mail <small>(opcional)</small></span><input className="input" type="email" autoComplete="email" maxLength={254} value={email} onChange={(event) => setEmail(event.target.value)} /></label>
          <label className="field login-field"><span>Senha individual <small>(mínimo de 12 caracteres)</small></span><input className="input" type="password" autoComplete="new-password" minLength={12} maxLength={128} value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
          <button className="button button-primary login-button" type="submit" disabled={loading}>{loading ? 'Configurando…' : 'Criar administrador'} {!loading && <ArrowRight size={15} />}</button>
        </form>
        <div className="login-security"><ShieldCheck size={13} style={{ verticalAlign: 'middle', marginRight: 5 }} />A chave é conferida somente pelo servidor e não fica salva na conta.</div>
        <div className="login-help"><Link to="/login">Voltar ao login</Link></div>
      </div>
    </section>
  </div>;
}
