import { FormEvent, useEffect, useMemo, useState } from 'react';
import { CirclePlus, Search, X } from 'lucide-react';
import TabelaProdutos from '../components/TabelaProdutos';
import { api } from '../services/api';
import type { Produto } from '../types';

type FormValue = { sku: string; nome: string; categoria: string; unidade: string; custo: string; estoque_minimo: string; estoque_inicial: string; rfid_uid: string };
const blank: FormValue = { sku: '', nome: '', categoria: '', unidade: 'un', custo: '', estoque_minimo: '5', estoque_inicial: '0', rfid_uid: '' };

export default function Produtos() {
  const [items, setItems] = useState<Produto[]>([]); const [query, setQuery] = useState(''); const [category, setCategory] = useState('Todas');
  const [modal, setModal] = useState(false); const [editing, setEditing] = useState<Produto | null>(null); const [form, setForm] = useState(blank);
  const [error, setError] = useState(''); const [success, setSuccess] = useState(''); const [saving, setSaving] = useState(false); const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try { setItems(await api.produtos()); setError(''); }
    catch (e) { setError(e instanceof Error ? e.message : 'Não foi possível carregar os produtos.'); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, []);
  const categories = useMemo(() => ['Todas', ...new Set(items.map((p) => p.categoria).filter(Boolean))], [items]);
  const filtered = useMemo(() => items.filter((p) => (category === 'Todas' || p.categoria === category) && `${p.nome} ${p.sku} ${p.categoria}`.toLowerCase().includes(query.toLowerCase())), [items, category, query]);
  function openCreate() { setEditing(null); setForm(blank); setError(''); setModal(true); }
  function openEdit(product: Produto) { setEditing(product); setForm({ sku: product.sku, nome: product.nome, categoria: product.categoria, unidade: product.unidade, custo: product.custo?.toString() ?? '', estoque_minimo: String(product.estoque_minimo), estoque_inicial: String(product.estoque_inicial), rfid_uid: product.rfid_uid ?? '' }); setError(''); setModal(true); }
  async function submit(event: FormEvent) {
    event.preventDefault(); setSaving(true); setError('');
    try {
      if (editing) await api.atualizarProduto(editing.id, { nome: form.nome, categoria: form.categoria, unidade: form.unidade, custo: form.custo ? Number(form.custo) : null, estoque_minimo: Number(form.estoque_minimo), rfid_uid: form.rfid_uid || null });
      else await api.criarProduto({ sku: form.sku, nome: form.nome, categoria: form.categoria, unidade: form.unidade, custo: form.custo ? Number(form.custo) : null, estoque_minimo: Number(form.estoque_minimo), estoque_inicial: Number(form.estoque_inicial), rfid_uid: form.rfid_uid || null });
      setModal(false); setSuccess(editing ? 'Produto atualizado.' : 'Produto cadastrado.'); await load(); window.setTimeout(() => setSuccess(''), 3000);
    } catch (e) { setError(e instanceof Error ? e.message : 'Não foi possível salvar o produto.'); } finally { setSaving(false); }
  }
  const change = (key: keyof FormValue) => (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setForm((f) => ({ ...f, [key]: event.target.value }));

  return <>
    <div className="page-heading"><div><div className="eyebrow">Cadastro e identificação</div><h2>Produtos</h2><p>Catálogo central dos itens que circulam na operação.</p></div><div className="heading-actions"><button className="button button-primary" onClick={openCreate}><CirclePlus /> Novo produto</button></div></div>
    {success && <div className="toast success">{success}</div>}{error && !modal && <div className="toast error">{error}</div>}
    <section className="panel"><div className="panel-header"><div><h3 className="panel-title">Catálogo <span className="tag">{loading ? '…' : `${items.length} SKUs`}</span></h3><div className="panel-subtitle">Gerencie identificação, custo e níveis mínimos.</div></div></div>
      <div className="filter-bar"><div className="search-field"><Search /><input className="input" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Buscar por nome, SKU ou categoria" /></div><select className="select" value={category} onChange={(e) => setCategory(e.target.value)} disabled={loading}>{categories.map((c) => <option key={c}>{c}</option>)}</select></div>
      {loading ? <div className="empty-state" role="status">Carregando produtos…</div> : !filtered.length && !items.length && error ? <div className="empty-state">Não foi possível carregar o catálogo.</div> : <TabelaProdutos produtos={filtered} onEdit={openEdit} />}
    </section>
    {modal && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setModal(false); }}><section className="modal" role="dialog" aria-modal="true" aria-labelledby="product-modal-title"><div className="modal-header"><div><h3 id="product-modal-title">{editing ? 'Editar produto' : 'Novo produto'}</h3><p>Preencha a identificação e os parâmetros de estoque.</p></div><button className="icon-button" aria-label="Fechar" onClick={() => setModal(false)}><X /></button></div>
      {error && <div className="toast error">{error}</div>}
      <form onSubmit={(e) => void submit(e)}><div className="form-grid">
        <div className="field"><label htmlFor="sku">SKU</label><input id="sku" className="input" value={form.sku} onChange={change('sku')} required disabled={!!editing} maxLength={64} /></div>
        <div className="field"><label htmlFor="nome">Nome do produto</label><input id="nome" className="input" value={form.nome} onChange={change('nome')} required maxLength={140} /></div>
        <div className="field"><label htmlFor="categoria">Categoria</label><input id="categoria" className="input" value={form.categoria} onChange={change('categoria')} maxLength={80} /></div>
        <div className="field"><label htmlFor="unidade">Unidade</label><select id="unidade" className="select" style={{ maxWidth: 'none' }} value={form.unidade} onChange={change('unidade')}><option value="un">unidade (un)</option><option value="kg">quilograma (kg)</option><option value="L">litro (L)</option><option value="cx">caixa (cx)</option><option value="m">metro (m)</option></select></div>
        <div className="field"><label htmlFor="custo">Custo unitário (R$)</label><input id="custo" className="input" type="number" min="0" step="0.01" value={form.custo} onChange={change('custo')} placeholder="Opcional" /></div>
        <div className="field"><label htmlFor="minimo">Estoque mínimo</label><input id="minimo" className="input" type="number" min="0" step="1" value={form.estoque_minimo} onChange={change('estoque_minimo')} required /></div>
        {!editing && <div className="field"><label htmlFor="inicial">Saldo inicial</label><input id="inicial" className="input" type="number" min="0" step="1" value={form.estoque_inicial} onChange={change('estoque_inicial')} required /></div>}
        <div className="field"><label htmlFor="rfid">UID RFID (opcional)</label><input id="rfid" className="input mono" value={form.rfid_uid} onChange={change('rfid_uid')} placeholder="Ex.: A1B2C3D4" /></div>
      </div><div className="modal-actions"><button type="button" className="button button-ghost" onClick={() => setModal(false)}>Cancelar</button><button className="button button-primary" disabled={saving}>{saving ? 'Salvando…' : editing ? 'Salvar alterações' : 'Cadastrar produto'}</button></div></form>
    </section></div>}
  </>;
}
