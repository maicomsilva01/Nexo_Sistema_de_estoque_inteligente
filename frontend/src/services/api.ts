import type {
  Alerta,
  AuthStatus,
  Movimentacao,
  PrevisaoProduto,
  Produto,
  ResumoEstoque,
  TipoMovimentacao,
  Usuario,
} from '../types';

const API = '/api';

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set('Accept', 'application/json');
  if ((init.method ?? 'GET').toUpperCase() !== 'GET') headers.set('X-Nexo-Request', 'fetch');
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  const response = await fetch(`${API}${path}`, { ...init, headers, credentials: 'include' });
  if (!response.ok) {
    let message = `Não foi possível concluir a operação (${response.status}).`;
    try {
      const body = (await response.json()) as { detail?: string; message?: string };
      message = body.detail || body.message || message;
    } catch {
      // Mantém a mensagem HTTP quando a resposta não é JSON.
    }
    throw new Error(message);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  authStatus: () => request<AuthStatus>('/auth/status'),
  login: (username: string, senha: string, origin: string) =>
    request<{ ok: boolean }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, senha, origin }),
    }),
  bootstrapAdmin: (data: { chave_bootstrap: string; nome: string; username: string; email?: string | null; senha: string; origin: string }) =>
    request<{ ok: boolean; usuario: Usuario }>('/auth/bootstrap', { method: 'POST', body: JSON.stringify(data) }),
  logout: () => request<{ ok: boolean }>('/auth/logout', { method: 'POST' }),
  usuarios: () => request<Usuario[]>('/usuarios'),
  criarUsuario: (data: { nome: string; username: string; email?: string | null; senha: string; perfil: 'admin' | 'operador' }) =>
    request<Usuario>('/usuarios', { method: 'POST', body: JSON.stringify(data) }),
  atualizarUsuario: (openId: string, data: { nome?: string; username?: string; email?: string | null; senha?: string; perfil?: 'admin' | 'operador'; ativo?: boolean }) =>
    request<Usuario>(`/usuarios/${encodeURIComponent(openId)}`, { method: 'PATCH', body: JSON.stringify(data) }),
  desativarUsuario: (openId: string) =>
    request<void>(`/usuarios/${encodeURIComponent(openId)}`, { method: 'DELETE' }),
  resumo: () => request<ResumoEstoque>('/estoque/resumo'),
  produtos: (q = '') => request<Produto[]>(`/produtos${q ? `?q=${encodeURIComponent(q)}` : ''}`),
  criarProduto: (data: {
    sku: string;
    nome: string;
    categoria: string;
    unidade: string;
    custo: number | null;
    estoque_minimo: number;
    estoque_inicial: number;
    rfid_uid: string | null;
  }) => request<Produto>('/produtos', { method: 'POST', body: JSON.stringify(data) }),
  atualizarProduto: (id: number, data: Partial<Produto>) =>
    request<Produto>(`/produtos/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  movimentacoes: (limit = 100) => request<Movimentacao[]>(`/movimentacoes?limit=${limit}`),
  criarMovimentacao: (data: {
    produto_id: number;
    tipo: TipoMovimentacao;
    quantidade: number;
    motivo: string;
  }) => request<Movimentacao>('/movimentacoes', { method: 'POST', body: JSON.stringify(data) }),
  lerRfid: (data: { uid: string; tipo: TipoMovimentacao; quantidade: number }) =>
    request<Movimentacao>('/movimentacoes/scan', { method: 'POST', body: JSON.stringify(data) }),
  estoque: () => request<Produto[]>('/estoque'),
  alertas: () => request<Alerta[]>('/estoque/alertas'),
  previsoes: (dias = 30) => request<PrevisaoProduto[]>(`/previsoes?dias=${dias}`),
  treinarPrevisoes: () => request<{ modelos: number; caminho: string }>('/previsoes/treinar', { method: 'POST' }),
};
