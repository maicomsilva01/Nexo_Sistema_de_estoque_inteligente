export interface Usuario {
  open_id: string;
  nome: string;
  username: string;
  email: string | null;
  perfil: 'admin' | 'operador';
  ativo: boolean;
}

export interface AuthStatus {
  autenticado: boolean;
  usuario: Usuario | null;
  bootstrap_disponivel: boolean;
}

export interface Produto {
  id: number;
  sku: string;
  nome: string;
  categoria: string;
  unidade: string;
  custo: number | null;
  estoque_minimo: number;
  estoque_inicial: number;
  saldo: number;
  rfid_uid: string | null;
  ativo: boolean;
  demonstracao: boolean;
  atualizado_em: string;
}

export type TipoMovimentacao = 'entrada' | 'saida' | 'ajuste';

export interface Movimentacao {
  id: number;
  produto_id: number;
  produto_nome: string;
  sku: string;
  tipo: TipoMovimentacao;
  quantidade: number;
  quantidade_assinada: number;
  motivo: string;
  usuario_nome: string | null;
  criado_em: string;
  origem: 'manual' | 'rfid' | 'demonstracao';
}

export interface Alerta {
  produto_id: number;
  sku: string;
  nome: string;
  saldo: number;
  estoque_minimo: number;
  quantidade_repor: number;
  severidade: 'ruptura' | 'baixo';
}

export interface SerieConsumo {
  dia: string;
  quantidade: number;
}

export interface PrevisaoProduto {
  produto_id: number;
  sku: string;
  nome: string;
  saldo_atual: number;
  consumo_30_dias: number;
  consumo_diario_estimado: number;
  previsao_horizonte: number;
  horizonte_dias: number;
  dias_ate_ruptura: number | null;
  metodo: string;
  confianca: 'adequada' | 'limitada' | 'sem_historico';
  serie: SerieConsumo[];
  recomendacao: string;
}

export interface ResumoEstoque {
  total_skus: number;
  unidades: number;
  itens_criticos: number;
  valor_estimado: number | null;
  entradas_mes: number;
  saidas_mes: number;
  serie_consumo: SerieConsumo[];
  alertas: Alerta[];
  movimentacoes_recentes: Movimentacao[];
  demonstracao: boolean;
}
