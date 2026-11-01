import { useEffect, useState } from 'react';
import { Boxes, CircleAlert, Package, Search } from 'lucide-react';
import CardEstoque from '../components/CardEstoque';
import TabelaProdutos from '../components/TabelaProdutos';
import { api } from '../services/api';
import type { Produto } from '../types';

export default function Estoque() {
  const [items, setItems] = useState<Produto[]>([]); const [query, setQuery] = useState(''); const [filter, setFilter] = useState('todos'); const [error, setError] = useState(''); const [loading, setLoading] = useState(true);
  async function load() {
    setLoading(true);
    try { setItems(await api.estoque()); setError(''); }
    catch (e) { setError(e instanceof Error ? e.message : 'Falha ao carregar estoque.'); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, []);
  const units = items.reduce((sum, p) => sum + p.saldo, 0); const critical = items.filter((p) => p.saldo <= p.estoque_minimo).length;
  const filtered = items.filter((p) => `${p.nome} ${p.sku} ${p.categoria}`.toLowerCase().includes(query.toLowerCase()) && (filter === 'todos' || (filter === 'criticos' ? p.saldo <= p.estoque_minimo : p.saldo > p.estoque_minimo)));
  return <>
    <div className="page-heading"><div><div className="eyebrow">Posição de inventário</div><h2>Estoque</h2><p>O saldo é calculado pelo estoque inicial mais as movimentações registradas.</p></div></div>
    {error && <div className="toast error">{error}</div>}
    {loading ? <div className="metrics-grid" role="status">{[1,2,3].map((i) => <div className="metric-card" key={i}><div className="loading-line" style={{ width: '52%' }} /><div className="loading-line" style={{ width: '35%', height: 24, marginTop: 18 }} /></div>)}</div> : !(error && !items.length) && <div className="metrics-grid"><CardEstoque label="Produtos monitorados" value={String(items.length)} foot="itens ativos no catálogo" icon={Package} /><CardEstoque label="Unidades disponíveis" value={new Intl.NumberFormat('pt-BR').format(units)} foot="saldo consolidado" icon={Boxes} /><CardEstoque label="Abaixo do mínimo" value={String(critical)} foot="necessitam avaliação" icon={CircleAlert} tone={critical ? 'warning' : 'normal'} /></div>}
    <section className="panel"><div className="panel-header"><div><h3 className="panel-title">Níveis por produto</h3><div className="panel-subtitle">A barra compara o saldo com até duas vezes o mínimo configurado.</div></div><span className="tag">{loading ? '…' : `${filtered.length} itens`}</span></div>
      {!loading && !(error && !items.length) && <div className="filter-bar"><div className="search-field"><Search /><input className="input" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Filtrar por produto ou SKU" /></div><select className="select" value={filter} onChange={(e) => setFilter(e.target.value)}><option value="todos">Todos os níveis</option><option value="criticos">No mínimo ou abaixo</option><option value="saudaveis">Acima do mínimo</option></select></div>}
      {loading ? <div className="empty-state" role="status">Carregando saldos de estoque…</div> : error && !items.length ? <div className="empty-state">Não foi possível carregar os níveis.</div> : <TabelaProdutos produtos={filtered} />}
    </section>
  </>;
}
