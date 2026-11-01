import { Package } from 'lucide-react';
import type { Produto } from '../types';

interface Props { produtos: Produto[]; onEdit?: (produto: Produto) => void }

export default function TabelaProdutos({ produtos, onEdit }: Props) {
  if (!produtos.length) return <div className="empty-state"><div className="empty-icon"><Package /></div>Nenhum produto encontrado com esses filtros.</div>;
  return <div className="table-wrap"><table className="data-table">
    <thead><tr><th>Produto</th><th>SKU</th><th>Saldo atual</th><th>Mínimo</th><th>Situação</th><th /></tr></thead>
    <tbody>{produtos.map((produto) => {
      const ratio = produto.estoque_minimo > 0 ? Math.min(100, (produto.saldo / (produto.estoque_minimo * 2)) * 100) : 100;
      const state = produto.saldo <= 0 ? 'ruptura' : produto.saldo <= produto.estoque_minimo ? 'baixo' : 'ok';
      return <tr key={produto.id}>
        <td><div className="product-cell"><span className="product-glyph"><Package /></span><span><span className="product-name">{produto.nome}</span><span className="product-meta">{produto.categoria || 'Sem categoria'} · {produto.unidade}</span></span></div></td>
        <td><span className="sku">{produto.sku}</span></td>
        <td className="stock-cell"><div className="stock-number"><strong>{produto.saldo} {produto.unidade}</strong><span>mín. {produto.estoque_minimo}</span></div><div className="stock-rail"><div className={`stock-fill ${state === 'ruptura' ? 'out' : state === 'baixo' ? 'low' : ''}`} style={{ width: `${ratio}%` }} /></div></td>
        <td className="mono">{produto.estoque_minimo}</td>
        <td><span className={`status-pill ${state === 'ruptura' ? 'status-danger' : state === 'baixo' ? 'status-warn' : 'status-ok'}`}>{state === 'ruptura' ? 'Ruptura' : state === 'baixo' ? 'Abaixo do mínimo' : 'Saudável'}</span></td>
        <td>{onEdit && <button className="button button-ghost button-small" onClick={() => onEdit(produto)}>Editar</button>}</td>
      </tr>;
    })}</tbody>
  </table></div>;
}
