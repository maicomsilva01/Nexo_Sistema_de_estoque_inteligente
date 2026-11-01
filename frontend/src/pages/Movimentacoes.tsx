import { FormEvent, useEffect, useState } from 'react';
import { ArrowDownLeft, ArrowUpRight, Radio, RefreshCw } from 'lucide-react';
import TabelaMovimentacoes from '../components/TabelaMovimentacoes';
import { api } from '../services/api';
import type { Movimentacao, Produto, TipoMovimentacao } from '../types';

export default function Movimentacoes() {
  const [items, setItems] = useState<Movimentacao[]>([]); const [products, setProducts] = useState<Produto[]>([]);
  const [type, setType] = useState<TipoMovimentacao>('entrada'); const [productId, setProductId] = useState(''); const [quantity, setQuantity] = useState('1'); const [reason, setReason] = useState('');
  const [uid, setUid] = useState(''); const [error, setError] = useState(''); const [success, setSuccess] = useState(''); const [saving, setSaving] = useState(false); const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const [moves, prods] = await Promise.all([api.movimentacoes(100), api.produtos()]);
      setItems(moves); setProducts(prods.filter((p) => p.ativo));
      if (!productId && prods.length) setProductId(String(prods[0].id));
      setError('');
    } catch (e) { setError(e instanceof Error ? e.message : 'Não foi possível carregar os dados.'); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, []);
  async function submit(event: FormEvent) {
    event.preventDefault(); setSaving(true); setError(''); setSuccess('');
    try { await api.criarMovimentacao({ produto_id: Number(productId), tipo: type, quantidade: Number(quantity), motivo: reason || (type === 'ajuste' ? 'Ajuste de inventário' : 'Movimentação manual') }); setSuccess('Movimentação registrada e saldo atualizado.'); setQuantity('1'); setReason(''); await load(); }
    catch (e) { setError(e instanceof Error ? e.message : 'Não foi possível registrar a movimentação.'); }
    finally { setSaving(false); }
  }
  async function scan(event: FormEvent) {
    event.preventDefault(); setSaving(true); setError(''); setSuccess('');
    try { const move = await api.lerRfid({ uid, tipo: type, quantidade: Number(quantity) }); setSuccess(`Leitura ${uid} associada a ${move.produto_nome}; movimentação registrada.`); setUid(''); await load(); }
    catch (e) { setError(e instanceof Error ? e.message : 'Falha na leitura RFID.'); }
    finally { setSaving(false); }
  }
  return <>
    <div className="page-heading"><div><div className="eyebrow">Livro de inventário</div><h2>Movimentações</h2><p>Cada entrada, saída ou ajuste atualiza o saldo e mantém o histórico.</p></div><button className="button button-ghost" onClick={() => void load()} disabled={loading}><RefreshCw /> Atualizar histórico</button></div>
    {error && <div className="toast error">{error}</div>}{success && <div className="toast success">{success}</div>}
    <div className="content-grid equal">
      <section className="panel"><div className="panel-header"><div><h3 className="panel-title">Registrar movimentação</h3><div className="panel-subtitle">Informe o item, o tipo e a quantidade.</div></div></div>
        {loading ? <div className="empty-state" role="status">Carregando produtos e movimentos…</div> : <form onSubmit={(e) => void submit(e)}><div className="form-grid">
          <div className="field"><label htmlFor="tipo">Tipo</label><select id="tipo" className="select" style={{ maxWidth: 'none' }} value={type} onChange={(e) => setType(e.target.value as TipoMovimentacao)}><option value="entrada">Entrada</option><option value="saida">Saída</option><option value="ajuste">Ajuste (+ adiciona, − reduz)</option></select></div>
          <div className="field"><label htmlFor="quantidade">Quantidade</label><input id="quantidade" className="input" type="number" step="1" min={type === 'ajuste' ? undefined : '1'} value={quantity} onChange={(e) => setQuantity(e.target.value)} required /></div>
          <div className="field full"><label htmlFor="produto">Produto</label><select id="produto" className="select" style={{ maxWidth: 'none' }} value={productId} onChange={(e) => setProductId(e.target.value)} required disabled={!products.length}><option value="">Selecione um produto</option>{products.map((p) => <option key={p.id} value={p.id}>{p.nome} · {p.sku} · saldo {p.saldo}</option>)}</select></div>
          <div className="field full"><label htmlFor="motivo">Motivo</label><input id="motivo" className="input" value={reason} onChange={(e) => setReason(e.target.value)} maxLength={240} placeholder="Ex.: compra, consumo, contagem cíclica" /></div>
        </div><div className="modal-actions"><button className="button button-primary" disabled={saving || !productId}>{type === 'entrada' ? <ArrowDownLeft /> : <ArrowUpRight />}{saving ? 'Registrando…' : 'Registrar movimento'}</button></div></form>}
      </section>
      <section className="panel"><div className="panel-header"><div><h3 className="panel-title">Leitura de tag RFID</h3><div className="panel-subtitle">Simule a leitura pela UID cadastrada no produto.</div></div><span className="tag green">Wokwi / RC522</span></div>
        <div className="rfid-card"><Radio /><div className="rfid-copy"><strong>Leitura simulada</strong><span>ESP32 + RC522 · UID associada ao catálogo</span></div></div>
        <form onSubmit={(e) => void scan(e)} className="section-gap"><div className="form-grid"><div className="field full"><label htmlFor="uid">UID da tag</label><input id="uid" className="input mono" value={uid} onChange={(e) => setUid(e.target.value)} placeholder="Ex.: A1B2C3D4" required /></div><div className="field full"><label htmlFor="rfid-qty">Quantidade nesta leitura</label><input id="rfid-qty" className="input" type="number" min="1" max="2000000000" step="1" value={quantity} onChange={(e) => setQuantity(e.target.value)} required /></div></div><div className="modal-actions"><button className="button button-soft" disabled={saving || loading}><Radio /> Associar e registrar</button></div></form>
      </section>
    </div>
    <section className="panel section-gap"><div className="panel-header"><div><h3 className="panel-title">Histórico recente</h3><div className="panel-subtitle">Movimentações mais recentes primeiro · {loading ? '…' : `${items.length} registros`}</div></div></div>{loading ? <div className="empty-state" role="status">Carregando histórico…</div> : <TabelaMovimentacoes movimentacoes={items} />}</section>
  </>;
}
