import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { Plus, RefreshCw, ShieldCheck, UserRoundCog } from 'lucide-react';
import { api } from '../services/api';
import type { Usuario } from '../types';

type FormState = { nome: string; username: string; email: string; senha: string; perfil: 'admin' | 'operador'; ativo: boolean };
const emptyForm: FormState = { nome: '', username: '', email: '', senha: '', perfil: 'operador', ativo: true };

export default function Usuarios() {
  const [users, setUsers] = useState<Usuario[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Usuario | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);

  const loadUsers = useCallback(async () => {
    setLoading(true);
    setError('');
    try { setUsers(await api.usuarios()); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Não foi possível carregar as contas.'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { void loadUsers(); }, [loadUsers]);

  function openCreate() {
    setEditing(null);
    setForm(emptyForm);
    setError('');
    setNotice('');
    setDialogOpen(true);
  }

  function openEdit(user: Usuario) {
    setEditing(user);
    setForm({ nome: user.nome, username: user.username, email: user.email ?? '', senha: '', perfil: user.perfil, ativo: user.ativo });
    setError('');
    setNotice('');
    setDialogOpen(true);
  }

  async function saveUser(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError('');
    const email = form.email.trim() || null;
    try {
      if (editing) {
        await api.atualizarUsuario(editing.open_id, {
          nome: form.nome,
          username: form.username,
          email,
          perfil: form.perfil,
          ativo: form.ativo,
          ...(form.senha ? { senha: form.senha } : {}),
        });
      } else {
        await api.criarUsuario({ nome: form.nome, username: form.username, email, senha: form.senha, perfil: form.perfil });
      }
      setDialogOpen(false);
      setNotice(editing ? 'Conta atualizada.' : 'Conta criada. A pessoa já pode entrar com o nome de usuário e a senha definidos.');
      await loadUsers();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Não foi possível salvar a conta.');
    } finally { setSaving(false); }
  }

  async function toggleActive(user: Usuario) {
    setError('');
    setNotice('');
    if (user.ativo && !window.confirm(`Desativar a conta de ${user.nome}? O histórico de movimentações será preservado.`)) return;
    try {
      if (user.ativo) await api.desativarUsuario(user.open_id);
      else await api.atualizarUsuario(user.open_id, { ativo: true });
      setNotice(user.ativo ? 'Conta desativada; o histórico foi preservado.' : 'Conta reativada.');
      await loadUsers();
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Não foi possível alterar o estado da conta.'); }
  }

  return <>
    <div className="page-heading">
      <div><div className="eyebrow">Administração</div><h2>Usuários</h2><p>Contas individuais e permissões da operação.</p></div>
      <div className="heading-actions"><button className="button button-ghost" onClick={() => void loadUsers()} disabled={loading}><RefreshCw />Atualizar</button><button className="button button-primary" onClick={openCreate}><Plus />Novo usuário</button></div>
    </div>
    <div className="notice"><ShieldCheck />Somente administradores podem criar contas. Desativar uma conta preserva as movimentações já registradas.</div>
    {error && <div className="toast error" role="alert">{error}</div>}
    {notice && <div className="toast success" role="status">{notice}</div>}
    <section className="panel">
      <div className="panel-header"><div><h3 className="panel-title">Contas cadastradas</h3><div className="panel-subtitle">A senha nunca é exibida depois de salva.</div></div><span className="status-pill status-neutral">{users.length} contas</span></div>
      {loading ? <div className="loading-line" /> : users.length === 0 ? <div className="empty-state"><div className="empty-icon"><UserRoundCog /></div>Nenhuma conta cadastrada.</div> : <div className="table-wrap"><table className="data-table"><thead><tr><th>Nome</th><th>Usuário</th><th>E-mail</th><th>Perfil</th><th>Estado</th><th>Ações</th></tr></thead><tbody>
        {users.map((user) => <tr key={user.open_id}><td><strong>{user.nome}</strong></td><td>{user.username}</td><td>{user.email || '—'}</td><td>{user.perfil === 'admin' ? 'Administrador' : 'Operador'}</td><td><span className={`status-pill ${user.ativo ? 'status-ok' : 'status-neutral'}`}>{user.ativo ? 'Ativo' : 'Inativo'}</span></td><td><div className="user-actions"><button className="button button-ghost button-small" onClick={() => openEdit(user)}>Editar</button><button className={`button button-small ${user.ativo ? 'button-danger' : 'button-soft'}`} onClick={() => void toggleActive(user)}>{user.ativo ? 'Desativar' : 'Ativar'}</button></div></td></tr>)}
      </tbody></table></div>}
    </section>

    {dialogOpen && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setDialogOpen(false); }}>
      <section className="modal" role="dialog" aria-modal="true" aria-labelledby="user-dialog-title">
        <div className="modal-header"><div><h3 id="user-dialog-title">{editing ? 'Editar usuário' : 'Novo usuário'}</h3><p>{editing ? 'Altere os dados e permissões da conta.' : 'A conta será criada pelo administrador, sem cadastro público.'}</p></div><button className="icon-button" onClick={() => setDialogOpen(false)} aria-label="Fechar">×</button></div>
        {error && <div className="toast error" role="alert">{error}</div>}
        <form onSubmit={saveUser}>
          <div className="form-grid">
            <div className="field full"><label htmlFor="user-name">Nome</label><input id="user-name" className="input" value={form.nome} onChange={(event) => setForm({ ...form, nome: event.target.value })} minLength={2} maxLength={160} required /></div>
            <div className="field full"><label htmlFor="user-username">Usuário</label><input id="user-username" className="input" value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} minLength={3} maxLength={32} required /><span className="field-hint">Único; letras, números, ponto, hífen ou sublinhado.</span></div>
            <div className="field full"><label htmlFor="user-email">E-mail (opcional)</label><input id="user-email" className="input" type="email" autoComplete="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} maxLength={254} /></div>
            <div className="field full"><label htmlFor="user-password">{editing ? 'Nova senha (opcional)' : 'Senha inicial'}</label><input id="user-password" className="input" type="password" autoComplete="new-password" value={form.senha} onChange={(event) => setForm({ ...form, senha: event.target.value })} minLength={form.senha ? 12 : undefined} maxLength={128} required={!editing} /><span className="field-hint">Mínimo de 12 caracteres. A redefinição substitui a senha anterior.</span></div>
            <div className="field"><label htmlFor="user-role">Perfil</label><select id="user-role" className="select" value={form.perfil} onChange={(event) => setForm({ ...form, perfil: event.target.value as FormState['perfil'] })}><option value="operador">Operador</option><option value="admin">Administrador</option></select></div>
            {editing && <div className="field"><label htmlFor="user-active">Estado</label><select id="user-active" className="select" value={form.ativo ? 'true' : 'false'} onChange={(event) => setForm({ ...form, ativo: event.target.value === 'true' })}><option value="true">Ativo</option><option value="false">Inativo</option></select></div>}
          </div>
          <div className="modal-actions"><button type="button" className="button button-ghost" onClick={() => setDialogOpen(false)}>Cancelar</button><button type="submit" className="button button-primary" disabled={saving}>{saving ? 'Salvando…' : editing ? 'Salvar alterações' : 'Criar usuário'}</button></div>
        </form>
      </section>
    </div>}
  </>;
}
