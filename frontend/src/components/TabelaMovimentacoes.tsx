import { ArrowDownLeft, ArrowUpRight, Settings2 } from 'lucide-react';
import type { Movimentacao } from '../types';

interface Props { movimentacoes: Movimentacao[] }
const dateFormat = new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });

export default function TabelaMovimentacoes({ movimentacoes }: Props) {
  if (!movimentacoes.length) return <div className="empty-state">Ainda não há movimentações registradas.</div>;
  return <div className="table-wrap"><table className="data-table">
    <thead><tr><th>Tipo</th><th>Produto</th><th>Quantidade</th><th>Motivo</th><th>Responsável</th><th>Data</th></tr></thead>
    <tbody>{movimentacoes.map((m) => {
      const Icon = m.tipo === 'entrada' ? ArrowDownLeft : m.tipo === 'saida' ? ArrowUpRight : Settings2;
      const sign = m.quantidade_assinada > 0 ? '+' : '';
      return <tr key={m.id}>
        <td><span className={`movement-type ${m.tipo}`} title={m.tipo}><Icon /></span></td>
        <td><div className="product-name">{m.produto_nome}</div><div className="product-meta sku">{m.sku}</div></td>
        <td><span className={m.quantidade_assinada >= 0 ? 'quantity-positive' : 'quantity-negative'}>{sign}{m.quantidade_assinada}</span></td>
        <td><span className="product-meta">{m.motivo || (m.origem === 'rfid' ? 'Leitura RFID' : '—')}</span></td>
        <td><span className="product-meta">{m.usuario_nome || 'Sistema'}</span></td>
        <td><span className="product-meta">{dateFormat.format(new Date(m.criado_em))}</span></td>
      </tr>;
    })}</tbody>
  </table></div>;
}
