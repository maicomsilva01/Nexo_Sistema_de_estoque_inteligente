import { useEffect, useState } from 'react';
import { AlertTriangle, ArrowRight, CircleAlert, PackageX } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import type { Alerta } from '../types';

export default function Alertas() {
  const [items, setItems] = useState<Alerta[]>([]); const [filter, setFilter] = useState('todos'); const [error, setError] = useState(''); const [loading, setLoading] = useState(true);
  async function load() {
    setLoading(true);
    try { setItems(await api.alertas()); setError(''); }
    catch (e) { setError(e instanceof Error ? e.message : 'Falha ao consultar alertas.'); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, []);
  const critical = items.filter((a) => a.severidade === 'ruptura').length;
  const filtered = items.filter((a) => filter === 'todos' || a.severidade === filter);
  return <>
    <div className="page-heading"><div><div className="eyebrow">Prevenção de ruptura</div><h2>Alertas de estoque</h2><p>Itens no mínimo, abaixo dele ou sem saldo disponível.</p></div><Link className="button button-primary" to="/movimentacoes"><ArrowRight /> Registrar reposição</Link></div>
    {error && <div className="toast error">{error}</div>}
    {loading ? <div className="metrics-grid" role="status">{[1,2,3,4].map((i) => <div className="metric-card" key={i}><div className="loading-line" style={{ width: '50%' }} /><div className="loading-line" style={{ width: '32%', height: 24, marginTop: 18 }} /></div>)}</div> : !(error && !items.length) && <div className="metrics-grid"><div className="metric-card"><div className="metric-top">Alertas ativos <span className="metric-icon"><AlertTriangle /></span></div><div className="metric-value">{items.length}</div><div className="metric-foot">itens que exigem atenção</div></div><div className="metric-card"><div className="metric-top">Ruptura <span className="metric-icon"><PackageX /></span></div><div className="metric-value">{critical}</div><div className="metric-foot">sem saldo disponível</div></div><div className="metric-card"><div className="metric-top">Abaixo do mínimo <span className="metric-icon"><CircleAlert /></span></div><div className="metric-value">{items.length - critical}</div><div className="metric-foot">saldo no limite ou abaixo</div></div><div className="metric-card"><div className="metric-top">Política de alerta <span className="metric-icon"><AlertTriangle /></span></div><div className="metric-value">Por SKU</div><div className="metric-foot">baseada no mínimo configurado</div></div></div>}
    <section className="panel section-gap"><div className="panel-header"><div><h3 className="panel-title">Fila de reposição</h3><div className="panel-subtitle">Quantidade indicada para recompor o nível mínimo e margem operacional.</div></div><select className="select" value={filter} onChange={(e) => setFilter(e.target.value)} disabled={loading}><option value="todos">Todos os alertas</option><option value="ruptura">Ruptura</option><option value="baixo">Abaixo do mínimo</option></select></div>
      {loading ? <div className="empty-state" role="status">Carregando alertas…</div> : error && !items.length ? <div className="empty-state">Não foi possível consultar os alertas.</div> : !filtered.length ? <div className="empty-state"><div className="empty-icon"><CircleAlert /></div>{items.length ? 'Nenhum alerta neste filtro.' : 'Tudo certo: nenhum produto precisa de reposição.'}</div> : <div className="table-wrap"><table className="data-table"><thead><tr><th>Prioridade</th><th>Produto</th><th>Saldo atual</th><th>Mínimo definido</th><th>Sugestão de reposição</th><th>Ação</th></tr></thead><tbody>{filtered.map((a) => <tr key={a.produto_id}><td><span className={`status-pill ${a.severidade === 'ruptura' ? 'status-danger' : 'status-warn'}`}>{a.severidade === 'ruptura' ? 'Ruptura' : 'Estoque baixo'}</span></td><td><div className="product-name">{a.nome}</div><div className="product-meta sku">{a.sku}</div></td><td className="mono">{a.saldo}</td><td className="mono">{a.estoque_minimo}</td><td><span className="quantity-positive">+{a.quantidade_repor} un.</span></td><td><Link className="button button-soft button-small" to="/movimentacoes">Repor <ArrowRight size={12} /></Link></td></tr>)}</tbody></table></div>}
    </section>
  </>;
}
