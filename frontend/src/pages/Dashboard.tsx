import { useEffect, useState } from 'react';
import { ArrowDownLeft, ArrowRight, ArrowUpRight, Boxes, CircleAlert, Package, RefreshCw, Wallet } from 'lucide-react';
import { Link } from 'react-router-dom';
import AlertaEstoque from '../components/AlertaEstoque';
import CardEstoque from '../components/CardEstoque';
import GraficoConsumo from '../components/GraficoConsumo';
import TabelaMovimentacoes from '../components/TabelaMovimentacoes';
import { api } from '../services/api';
import type { ResumoEstoque } from '../types';

const number = new Intl.NumberFormat('pt-BR');
const currency = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 });
const weekday = new Intl.DateTimeFormat('pt-BR', { weekday: 'long' }).format(new Date());
const greeting = new Date().getHours() < 12 ? 'Bom dia' : new Date().getHours() < 18 ? 'Boa tarde' : 'Boa noite';

export default function Dashboard() {
  const [data, setData] = useState<ResumoEstoque | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  async function load() { setLoading(true); try { setData(await api.resumo()); setError(''); } catch (e) { setError(e instanceof Error ? e.message : 'Falha ao carregar painel.'); } finally { setLoading(false); } }
  useEffect(() => { void load(); }, []);

  return <>
    <div className="page-heading"><div><div className="eyebrow">{weekday} · operação em foco</div><h2>{greeting}. Aqui está o seu estoque.</h2><p>Visão consolidada dos níveis, consumo e movimentações recentes.</p></div><div className="heading-actions"><button className="button button-ghost" onClick={() => void load()} disabled={loading}><RefreshCw size={14} /> Atualizar</button><Link className="button button-primary" to="/movimentacoes"><ArrowDownLeft size={15} /> Registrar entrada</Link></div></div>
    {error && <div className="toast error">{error}</div>}
    {data?.demonstracao && <div className="notice demo"><CircleAlert /> Painel iniciado com itens demonstrativos para você conhecer os recursos. Cadastre seus produtos ou edite os exemplos para refletir sua operação.</div>}
    {loading && !data ? <div className="metrics-grid">{[1,2,3,4].map((i) => <div className="metric-card" key={i}><div className="loading-line" style={{ width: '55%' }} /><div className="loading-line" style={{ width: '38%', height: 24, marginTop: 18 }} /></div>)}</div> : data && <>
      <div className="metrics-grid">
        <CardEstoque label="Produtos ativos" value={number.format(data.total_skus)} foot="SKUs no catálogo" icon={Package} />
        <CardEstoque label="Unidades disponíveis" value={number.format(data.unidades)} foot="Saldo total calculado" icon={Boxes} />
        <CardEstoque label="Atenção necessária" value={number.format(data.itens_criticos)} foot={data.itens_criticos ? 'itens no mínimo ou abaixo' : 'nenhum item crítico'} icon={CircleAlert} tone={data.itens_criticos ? 'warning' : 'normal'} />
        <CardEstoque label="Valor estimado" value={data.valor_estimado === null ? '—' : currency.format(data.valor_estimado)} foot="Com base nos custos cadastrados" icon={Wallet} />
      </div>
      <div className="content-grid">
        <section className="panel"><div className="panel-header"><div><h3 className="panel-title">Ritmo de consumo</h3><div className="panel-subtitle">Saídas registradas nos últimos 30 dias</div></div><span className="chart-legend"><i className="legend-dot" /> unidades/dia</span></div><GraficoConsumo serie={data.serie_consumo} /></section>
        <section className="panel"><div className="panel-header"><div><h3 className="panel-title">Pontos de atenção</h3><div className="panel-subtitle">Itens que podem interromper o fluxo</div></div><Link to="/alertas" className="panel-link">Abrir alertas <ArrowRight /></Link></div><AlertaEstoque alertas={data.alertas} /></section>
      </div>
      <section className="panel"><div className="panel-header"><div><h3 className="panel-title">Movimentações recentes</h3><div className="panel-subtitle">Entradas, saídas e ajustes no inventário</div></div><Link to="/movimentacoes" className="panel-link">Ver histórico <ArrowRight /></Link></div>{data.movimentacoes_recentes.length > 0 ? <TabelaMovimentacoes movimentacoes={data.movimentacoes_recentes} /> : <div className="empty-state"><ArrowUpRight size={18} style={{ verticalAlign: 'middle', marginRight: 6 }} />Ainda não há movimentações.</div>}</section>
      <div className="page-footer"><span>Saldo calculado a partir do livro de movimentações.</span><span>Atualizado agora · <button className="panel-link clickable" onClick={() => void load()}>sincronizar</button></span></div>
    </>}
  </>;
}
