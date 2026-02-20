from django.http import HttpResponse


DOCS_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Riffel API — Documentação</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet"/>
  <style>
    :root {
      --bg: #0f1117;
      --bg2: #161b27;
      --bg3: #1e2535;
      --border: #2a3147;
      --text: #e2e8f0;
      --text-muted: #8892a4;
      --accent: #6366f1;
      --accent-light: #818cf8;
      --get: #10b981;
      --get-bg: rgba(16,185,129,0.12);
      --post: #f59e0b;
      --post-bg: rgba(245,158,11,0.12);
      --del: #ef4444;
      --del-bg: rgba(239,68,68,0.12);
      --tag: rgba(99,102,241,0.15);
      --radius: 10px;
      --shadow: 0 4px 24px rgba(0,0,0,0.4);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; display: flex; min-height: 100vh; }

    /* ── SIDEBAR ── */
    .sidebar {
      width: 260px; min-width: 260px; background: var(--bg2);
      border-right: 1px solid var(--border); padding: 28px 0;
      position: sticky; top: 0; height: 100vh; overflow-y: auto;
      display: flex; flex-direction: column;
    }
    .sidebar-logo { padding: 0 24px 24px; border-bottom: 1px solid var(--border); }
    .sidebar-logo .logo-text { font-size: 1.3rem; font-weight: 700; color: #fff; letter-spacing: -.5px; }
    .sidebar-logo .logo-text span { color: var(--accent-light); }
    .sidebar-logo .version { font-size: .72rem; color: var(--text-muted); margin-top: 4px; background: var(--tag); display: inline-block; padding: 2px 8px; border-radius: 20px; }
    .nav-section { padding: 20px 24px 8px; font-size: .68rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: var(--text-muted); }
    .nav-item {
      display: flex; align-items: center; gap: 10px;
      padding: 9px 24px; font-size: .85rem; color: var(--text-muted);
      cursor: pointer; transition: all .15s; text-decoration: none;
      border-left: 2px solid transparent;
    }
    .nav-item:hover { color: var(--text); background: rgba(99,102,241,.06); }
    .nav-item.active { color: var(--accent-light); background: rgba(99,102,241,.1); border-left-color: var(--accent); }
    .nav-item .badge {
      font-size: .6rem; font-weight: 700; padding: 2px 6px; border-radius: 4px;
      font-family: 'JetBrains Mono', monospace; letter-spacing: .3px;
    }
    .badge-get { background: var(--get-bg); color: var(--get); }
    .badge-post { background: var(--post-bg); color: var(--post); }

    /* ── MAIN ── */
    .main { flex: 1; padding: 40px 48px; max-width: 900px; margin: 0 auto; width: 100%; }

    /* ── HEADER ── */
    .page-header { margin-bottom: 48px; }
    .page-header h1 { font-size: 2rem; font-weight: 700; color: #fff; }
    .page-header p { color: var(--text-muted); margin-top: 10px; font-size: .95rem; line-height: 1.7; }
    .base-url-box {
      margin-top: 20px; background: var(--bg2); border: 1px solid var(--border);
      border-radius: var(--radius); padding: 14px 20px;
      display: flex; align-items: center; gap: 12px;
    }
    .base-url-box .label { font-size: .72rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: .8px; white-space: nowrap; }
    .base-url-box code { font-family: 'JetBrains Mono', monospace; font-size: .85rem; color: var(--accent-light); flex: 1; }
    .copy-btn {
      background: var(--bg3); border: 1px solid var(--border); color: var(--text-muted);
      padding: 5px 12px; border-radius: 6px; cursor: pointer; font-size: .75rem;
      transition: all .15s; white-space: nowrap;
    }
    .copy-btn:hover { color: #fff; border-color: var(--accent); }

    /* ── SECTION TITLE ── */
    .section-title { font-size: 1.1rem; font-weight: 600; color: #fff; margin: 40px 0 16px; display: flex; align-items: center; gap: 10px; }
    .section-title::before { content:''; width: 4px; height: 18px; background: var(--accent); border-radius: 4px; }
    hr.divider { border: none; border-top: 1px solid var(--border); margin: 32px 0; }

    /* ── ENDPOINT CARD ── */
    .endpoint {
      background: var(--bg2); border: 1px solid var(--border);
      border-radius: var(--radius); margin-bottom: 16px;
      overflow: hidden; transition: border-color .2s;
    }
    .endpoint:hover { border-color: var(--accent); }
    .endpoint-header {
      display: flex; align-items: center; gap: 14px;
      padding: 16px 22px; cursor: pointer; user-select: none;
    }
    .method {
      font-family: 'JetBrains Mono', monospace; font-size: .72rem;
      font-weight: 700; padding: 4px 10px; border-radius: 5px;
      min-width: 52px; text-align: center; letter-spacing: .5px;
    }
    .method-get { background: var(--get-bg); color: var(--get); }
    .method-post { background: var(--post-bg); color: var(--post); }
    .endpoint-path { font-family: 'JetBrains Mono', monospace; font-size: .88rem; color: #fff; flex: 1; }
    .endpoint-summary { font-size: .82rem; color: var(--text-muted); }
    .chevron { color: var(--text-muted); font-size: .7rem; transition: transform .2s; margin-left: auto; }
    .endpoint.open .chevron { transform: rotate(180deg); }

    /* ── ENDPOINT BODY ── */
    .endpoint-body { border-top: 1px solid var(--border); display: none; }
    .endpoint.open .endpoint-body { display: block; }
    .endpoint-body-inner { padding: 22px; }
    .desc { font-size: .87rem; color: var(--text-muted); line-height: 1.7; margin-bottom: 20px; }

    /* ── PARAMS TABLE ── */
    .params-title { font-size: .72rem; font-weight: 600; text-transform: uppercase; letter-spacing: .8px; color: var(--text-muted); margin-bottom: 10px; }
    table { width: 100%; border-collapse: collapse; font-size: .84rem; margin-bottom: 20px; }
    th { background: var(--bg3); color: var(--text-muted); font-weight: 500; font-size: .72rem; text-transform: uppercase; letter-spacing: .6px; padding: 9px 14px; text-align: left; }
    td { padding: 10px 14px; border-top: 1px solid var(--border); vertical-align: top; }
    td code { font-family: 'JetBrains Mono', monospace; font-size: .8rem; background: var(--bg3); padding: 2px 7px; border-radius: 4px; color: var(--accent-light); }
    .required { color: var(--del); font-size: .7rem; font-weight: 600; }
    .optional { color: var(--text-muted); font-size: .7rem; }

    /* ── RESPONSE BOX ── */
    .response-block { margin-top: 6px; }
    .res-header { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
    .status-badge { font-family: 'JetBrains Mono', monospace; font-size: .72rem; font-weight: 700; padding: 3px 9px; border-radius: 5px; }
    .s200 { background: var(--get-bg); color: var(--get); }
    .s400 { background: rgba(245,158,11,.15); color: var(--post); }
    .s401 { background: rgba(239,68,68,.12); color: var(--del); }
    .s500 { background: rgba(239,68,68,.12); color: var(--del); }
    pre {
      background: #0a0d14; border: 1px solid var(--border); border-radius: 8px;
      padding: 16px 18px; overflow-x: auto; font-family: 'JetBrains Mono', monospace;
      font-size: .78rem; line-height: 1.65; color: #a5b4fc; position: relative;
    }
    .copy-pre {
      position: absolute; top: 8px; right: 10px;
      background: var(--bg3); border: 1px solid var(--border);
      color: var(--text-muted); padding: 3px 10px; border-radius: 5px;
      cursor: pointer; font-size: .7rem; font-family: 'Inter', sans-serif;
    }
    .copy-pre:hover { color: #fff; border-color: var(--accent); }

    /* ── AUTH INFO ── */
    .auth-box {
      background: rgba(99,102,241,.08); border: 1px solid rgba(99,102,241,.25);
      border-radius: var(--radius); padding: 16px 20px; margin-bottom: 32px;
      font-size: .85rem; line-height: 1.6;
    }
    .auth-box strong { color: var(--accent-light); }

    /* ── SCROLLBAR ── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 10px; }

    @media (max-width: 768px) {
      .sidebar { display: none; }
      .main { padding: 24px 20px; }
    }
  </style>
</head>
<body>

<!-- SIDEBAR -->
<aside class="sidebar">
  <div class="sidebar-logo">
    <div class="logo-text">Riffel <span>API</span></div>
    <div class="version">v1.0.0</div>
  </div>

  <div class="nav-section">Conta</div>
  <a class="nav-item active" href="#me"><span class="badge badge-get">GET</span> /me</a>

  <div class="nav-section">Produtos</div>
  <a class="nav-item" href="#myproducts"><span class="badge badge-get">GET</span> /myproducts</a>
  <a class="nav-item" href="#myproducts-sync"><span class="badge badge-post">POST</span> /myproducts/sync</a>

  <div class="nav-section">Pedidos</div>
  <a class="nav-item" href="#myorders"><span class="badge badge-get">GET</span> /myorders</a>
  <a class="nav-item" href="#myorders-sync"><span class="badge badge-post">POST</span> /myorders/sync</a>

  <div class="nav-section">Anúncios</div>
  <a class="nav-item" href="#productads"><span class="badge badge-get">GET</span> /productads</a>

  <div class="nav-section">Token</div>
  <a class="nav-item" href="#token-status"><span class="badge badge-get">GET</span> /token/status</a>
  <a class="nav-item" href="#token-refresh"><span class="badge badge-post">POST</span> /token/refresh</a>

  <div class="nav-section">Utilitários</div>
  <a class="nav-item" href="#debug-env"><span class="badge badge-get">GET</span> /debug/env</a>
</aside>

<!-- MAIN CONTENT -->
<main class="main">

  <!-- PAGE HEADER -->
  <div class="page-header">
    <h1>Riffel API</h1>
    <p>API Django + DRF integrada ao Mercado Livre e Supabase.<br/>
    Autenticação via token armazenado no Supabase — refresh automático a cada requisição.</p>
    <div class="base-url-box">
      <span class="label">Base URL</span>
      <code id="base-url">https://riffel.onrender.com</code>
      <button class="copy-btn" onclick="copyText('base-url', this)">Copiar</button>
    </div>
  </div>

  <!-- AUTH -->
  <div class="auth-box">
    🔑 <strong>Autenticação:</strong> Todas as rotas usam o token Mercado Livre armazenado no <strong>Supabase</strong>.
    Não é necessário passar o token manualmente — a API busca e renova automaticamente.
    Use <code style="font-family:monospace;background:rgba(0,0,0,.3);padding:2px 6px;border-radius:4px">/token/refresh</code> para forçar um refresh manual.
  </div>

  <!-- ═══════════════════════════ CONTA ═══════════════════════════ -->
  <div class="section-title" id="me">Conta</div>

  <div class="endpoint" id="ep-me">
    <div class="endpoint-header" onclick="toggle('ep-me')">
      <span class="method method-get">GET</span>
      <span class="endpoint-path">/me</span>
      <span class="endpoint-summary">Dados da conta Mercado Livre</span>
      <span class="chevron">▼</span>
    </div>
    <div class="endpoint-body">
      <div class="endpoint-body-inner">
        <p class="desc">Retorna os dados da conta autenticada no Mercado Livre: nome, email, CNPJ formatado, endereço, reputação, nível Mercado Líder, entre outros.</p>

        <div class="params-title">Parâmetros</div>
        <p style="color:var(--text-muted);font-size:.84rem">Nenhum parâmetro necessário.</p>

        <br/>
        <div class="response-block">
          <div class="params-title">Resposta</div>
          <div class="res-header"><span class="status-badge s200">200 OK</span></div>
          <pre><button class="copy-pre" onclick="copyPre(this)">Copiar</button>{
  "id": 533863251,
  "nickname": "RIFFEL2024",
  "data_de_registro": "2020-03-15T10:22:00.000-03:00",
  "primeiro_nome": "João",
  "email": "joao@riffel.com.br",
  "cnpj": "12.345.678/0001-99",
  "endereco": "Rua das Flores, 100",
  "cidade": "São Paulo",
  "estado": "SP",
  "cep": "01310-100",
  "permalink_perfil": "https://perfil.mercadolivre.com.br/RIFFEL2024",
  "nivel_reputacao": "5_green",
  "nivel_mercado_lider": "gold",
  "mercadoenvios": "accepted",
  "nome_marca": "Riffel",
  "foto_perfil": "https://http2.mlstatic.com/D_NQ_NP_...",
  "numero_telefone": "+5511999999999"
}</pre>
        </div>
      </div>
    </div>
  </div>

  <hr class="divider"/>

  <!-- ═══════════════════════════ PRODUTOS ═══════════════════════════ -->
  <div class="section-title" id="myproducts">Produtos</div>

  <div class="endpoint" id="ep-myproducts">
    <div class="endpoint-header" onclick="toggle('ep-myproducts')">
      <span class="method method-get">GET</span>
      <span class="endpoint-path">/myproducts</span>
      <span class="endpoint-summary">Lista todos os produtos do seller</span>
      <span class="chevron">▼</span>
    </div>
    <div class="endpoint-body">
      <div class="endpoint-body-inner">
        <p class="desc">Retorna os produtos do <strong style="color:var(--accent-light)">cache Supabase</strong> (atualizado automaticamente a cada 1 hora em background). Zero chamadas ao ML API nesta rota = <strong style="color:var(--get)">uso mínimo de RAM</strong>. Se o cache estiver vazio, executa um sync imediato na primeira chamada.</p>

        <div class="params-title">Parâmetros</div>
        <p style="color:var(--text-muted);font-size:.84rem">Nenhum parâmetro necessário.</p>

        <br/>
        <div class="response-block">
          <div class="params-title">Resposta</div>
          <div class="res-header"><span class="status-badge s200">200 OK</span></div>
          <pre><button class="copy-pre" onclick="copyPre(this)">Copiar</button>{
  "total_produtos": 42,
  "ultimo_sync": "2026-02-20T14:30:00+00:00",
  "sync_status": "completed",
  "produtos": [
    {
      "ID": "MLB3456789012",
      "titulo": "Tenis Esportivo Running Pro",
      "preco": 199.90,
      "estoque_atual": 15,
      "quantidade_vendida": 230,
      "data_de_criacao": "2023-01-10T08:30:00.000Z",
      "permalink": "https://www.mercadolivre.com.br/...",
      "foto": "https://http2.mlstatic.com/D_NQ_NP_...",
      "modo_de_compra": "not_specified",
      "tipo_logistico": "fulfillment",
      "Marca": "Nike",
      "GTIN": "7891234567890",
      "SKU": "TEN-RUN-42",
      "TTS_horas": 3.21
    }
  ]
}</pre>
        </div>
      </div>
    </div>
  </div>

  <div class="endpoint" id="ep-myproducts-sync" style="margin-top:12px">
    <div class="endpoint-header" onclick="toggle('ep-myproducts-sync')">
      <span class="method method-post">POST</span>
      <span class="endpoint-path">/myproducts/sync</span>
      <span class="endpoint-summary">Força sync imediato dos produtos</span>
      <span class="chevron">&#9660;</span>
    </div>
    <div class="endpoint-body">
      <div class="endpoint-body-inner">
        <p class="desc">Força uma sincronização imediata dos produtos do Mercado Livre para o Supabase. Normalmente não é necessário — o sync automático roda a cada 1 hora em background.</p>

        <div class="params-title">Body</div>
        <p style="color:var(--text-muted);font-size:.84rem">Nenhum body necessário.</p>

        <br/>
        <div class="response-block">
          <div class="res-header"><span class="status-badge s200">200 OK</span></div>
          <pre><button class="copy-pre" onclick="copyPre(this)">Copiar</button>{
  "message": "Sincronizacao concluida!",
  "total_items": 42,
  "last_sync_at": "2026-02-20T14:30:00+00:00"
}</pre>
        </div>
      </div>
    </div>
  </div>

  <hr class="divider"/>

  <!-- ═══════════════════════════ PEDIDOS ═══════════════════════════ -->
  <div class="section-title" id="myorders">Pedidos</div>

  <div class="endpoint" id="ep-myorders">
    <div class="endpoint-header" onclick="toggle('ep-myorders')">
      <span class="method method-get">GET</span>
      <span class="endpoint-path">/myorders</span>
      <span class="endpoint-summary">Streaming de todos os pedidos</span>
      <span class="chevron">▼</span>
    </div>
    <div class="endpoint-body">
      <div class="endpoint-body-inner">
        <p class="desc">Retorna os pedidos do <strong style="color:var(--accent-light)">cache Supabase</strong> (atualizado automaticamente a cada 1 hora em background). Zero chamadas ao ML API = <strong style="color:var(--get)">uso mínimo de RAM</strong>. Inclui conciliação financeira completa: preço bruto, taxas ML, frete seller, descontos e valor líquido por pedido. Se o cache estiver vazio, executa sync imediato na primeira chamada.</p>

        <div class="params-title">Parâmetros</div>
        <p style="color:var(--text-muted);font-size:.84rem">Nenhum parâmetro necessário.</p>

        <br/>
        <div class="response-block">
          <div class="params-title">Resposta</div>
          <div class="res-header"><span class="status-badge s200">200 OK</span></div>
          <pre><button class="copy-pre" onclick="copyPre(this)">Copiar</button>{
  "vendas_detalhadas": [
    {
      "order_id": "2000123456789",
      "unit_price": 199.90,
      "quantity": 2,
      "gross_item": 399.80,
      "gross_items_order": 399.80,
      "sale_fee_total_order": 59.97,
      "marketplace_fee_order": 59.97,
      "seller_shipping_cost": 0.00,
      "net_order_simplified": 339.83,
      "discount_total_order": 0.00
    }
  ],
  "total_pedidos": 1580,
  "total_linhas": 1634,
  "resumo": {
    "bruto_total": 285430.50,
    "taxas_total": 42814.57,
    "frete_seller_total": 0.00,
    "descontos_total": 120.00,
    "liquido_total": 242495.93
  },
  "ultimo_sync": "2026-02-20T14:30:00+00:00",
  "sync_status": "completed"
}</pre>
        </div>
      </div>
    </div>
  </div>

  <div class="endpoint" id="ep-myorders-sync" style="margin-top:12px">
    <div class="endpoint-header" onclick="toggle('ep-myorders-sync')">
      <span class="method method-post">POST</span>
      <span class="endpoint-path">/myorders/sync</span>
      <span class="endpoint-summary">Força sync imediato dos pedidos</span>
      <span class="chevron">&#9660;</span>
    </div>
    <div class="endpoint-body">
      <div class="endpoint-body-inner">
        <p class="desc">Força uma sincronização imediata dos pedidos do Mercado Livre para o Supabase. Normalmente não é necessário — o sync automático roda a cada 1 hora em background.</p>

        <div class="params-title">Body</div>
        <p style="color:var(--text-muted);font-size:.84rem">Nenhum body necessário.</p>

        <br/>
        <div class="response-block">
          <div class="res-header"><span class="status-badge s200">200 OK</span></div>
          <pre><button class="copy-pre" onclick="copyPre(this)">Copiar</button>{
  "message": "Sincronizacao de pedidos concluida!",
  "total_items": 1634,
  "last_sync_at": "2026-02-20T14:30:00+00:00"
}</pre>
        </div>
      </div>
    </div>
  </div>

  <hr class="divider"/>

  <!-- ═══════════════════════════ PRODUCT ADS ═══════════════════════════ -->
  <div class="section-title" id="productads">Anúncios (Product Ads)</div>

  <div class="endpoint" id="ep-productads">
    <div class="endpoint-header" onclick="toggle('ep-productads')">
      <span class="method method-get">GET</span>
      <span class="endpoint-path">/productads</span>
      <span class="endpoint-summary">Métricas de Product Ads por período</span>
      <span class="chevron">▼</span>
    </div>
    <div class="endpoint-body">
      <div class="endpoint-body-inner">
        <p class="desc">Retorna métricas consolidadas das campanhas de Product Ads: investimento, receita, vendas, impressões, cliques e ROAS. Também retorna o detalhe por campanha.</p>

        <div class="params-title">Query Parameters</div>
        <table>
          <tr><th>Nome</th><th>Tipo</th><th>Padrão</th><th>Obrigatório</th><th>Descrição</th></tr>
          <tr>
            <td><code>period</code></td>
            <td>integer</td>
            <td><code>30</code></td>
            <td><span class="optional">opcional</span></td>
            <td>Período em dias. Valores válidos: <code>7</code>, <code>15</code>, <code>30</code>, <code>60</code>, <code>90</code>.</td>
          </tr>
        </table>

        <div class="params-title">Exemplos de uso</div>
        <pre><button class="copy-pre" onclick="copyPre(this)">Copiar</button>GET /productads           → últimos 30 dias (padrão)
GET /productads?period=7  → últimos 7 dias
GET /productads?period=90 → últimos 90 dias</pre>

        <br/>
        <div class="response-block">
          <div class="params-title">Resposta</div>
          <div class="res-header"><span class="status-badge s200">200 OK</span></div>
          <pre><button class="copy-pre" onclick="copyPre(this)">Copiar</button>{
  "period_days": 30,
  "dashboard": {
    "investment": 1250.80,
    "revenue": 8750.40,
    "sales": 87,
    "impressions": 45230,
    "clicks": 890,
    "roas": 6.99
  },
  "campaigns": [
    {
      "id": "123456",
      "name": "Campanha Tênis",
      "status": "active",
      "metrics": {
        "clicks": 320,
        "prints": 15000,
        "cost": 420.30,
        "units_quantity": 32,
        "total_amount": 2980.00,
        "roas": 7.09
      }
    }
  ]
}</pre>
          <div class="res-header" style="margin-top:12px"><span class="status-badge s400">400</span></div>
          <pre>{ "error": "Periodo invalido. Use: [7, 15, 30, 60, 90]" }</pre>
        </div>
      </div>
    </div>
  </div>

  <hr class="divider"/>

  <!-- ═══════════════════════════ TOKEN ═══════════════════════════ -->
  <div class="section-title" id="token-status">Token</div>

  <div class="endpoint" id="ep-token-status">
    <div class="endpoint-header" onclick="toggle('ep-token-status')">
      <span class="method method-get">GET</span>
      <span class="endpoint-path">/token/status</span>
      <span class="endpoint-summary">Status do token armazenado</span>
      <span class="chevron">▼</span>
    </div>
    <div class="endpoint-body">
      <div class="endpoint-body-inner">
        <p class="desc">Retorna o status do token Mercado Livre armazenado no Supabase. Não expõe o valor do token — apenas metadados como expiração, user_id e escopo.</p>

        <div class="response-block">
          <div class="res-header"><span class="status-badge s200">200 OK</span></div>
          <pre><button class="copy-pre" onclick="copyPre(this)">Copiar</button>{
  "user_id": 533863251,
  "token_type": "Bearer",
  "expires_at": "2025-02-19T08:00:00+00:00",
  "scope": "offline_access read write",
  "updated_at": "2025-02-19T02:00:00+00:00"
}</pre>
        </div>
      </div>
    </div>
  </div>

  <div class="endpoint" id="ep-token-refresh" style="margin-top:12px">
    <div class="endpoint-header" onclick="toggle('ep-token-refresh')">
      <span class="method method-post">POST</span>
      <span class="endpoint-path">/token/refresh</span>
      <span class="endpoint-summary">Força refresh manual do token</span>
      <span class="chevron">▼</span>
    </div>
    <div class="endpoint-body">
      <div class="endpoint-body-inner">
        <p class="desc">Força um refresh imediato do token Mercado Livre usando o <code style="font-family:monospace;background:rgba(0,0,0,.3);padding:2px 5px;border-radius:3px">refresh_token</code> armazenado. Normalmente não é necessário — a API faz refresh automático quando o token está prestes a expirar.</p>

        <div class="params-title">Body</div>
        <p style="color:var(--text-muted);font-size:.84rem">Nenhum body necessário.</p>

        <br/>
        <div class="response-block">
          <div class="res-header"><span class="status-badge s200">200 OK</span></div>
          <pre><button class="copy-pre" onclick="copyPre(this)">Copiar</button>{
  "message": "Token atualizado com sucesso!",
  "user_id": 533863251,
  "expires_at": "2025-02-19T14:00:00+00:00"
}</pre>
        </div>
      </div>
    </div>
  </div>

  <hr class="divider"/>

  <!-- ═══════════════════════════ DEBUG ═══════════════════════════ -->
  <div class="section-title" id="debug-env">Utilitários</div>

  <div class="endpoint" id="ep-debug-env">
    <div class="endpoint-header" onclick="toggle('ep-debug-env')">
      <span class="method method-get">GET</span>
      <span class="endpoint-path">/debug/env</span>
      <span class="endpoint-summary">Diagnóstico de variáveis de ambiente</span>
      <span class="chevron">▼</span>
    </div>
    <div class="endpoint-body">
      <div class="endpoint-body-inner">
        <p class="desc">Verifica quais variáveis de ambiente estão configuradas e testa a conexão com o Supabase. Útil para diagnosticar problemas no deploy. <strong style="color:var(--post)">Não expõe valores sensíveis.</strong></p>

        <div class="response-block">
          <div class="res-header"><span class="status-badge s200">200 OK</span></div>
          <pre><button class="copy-pre" onclick="copyPre(this)">Copiar</button>{
  "env_vars_configuradas": {
    "SUPABASE_URL": true,
    "SUPABASE_KEY": true,
    "ML_APP_ID": true,
    "ML_SECRET_KEY": true,
    "ML_REDIRECT_URI": true,
    "DEBUG": false
  },
  "supabase_conectado": true,
  "supabase_erro": null,
  "token_no_banco": true
}</pre>
        </div>
      </div>
    </div>
  </div>

  <div style="margin-top:60px;padding-top:24px;border-top:1px solid var(--border);color:var(--text-muted);font-size:.78rem;text-align:center">
    Riffel API · Django 6 + DRF · Supabase · Mercado Livre
  </div>

</main>

<script>
  function toggle(id) {
    const el = document.getElementById(id);
    el.classList.toggle('open');
  }

  function copyText(id, btn) {
    const text = document.getElementById(id).innerText;
    navigator.clipboard.writeText(text).then(() => {
      btn.textContent = 'Copiado!';
      setTimeout(() => btn.textContent = 'Copiar', 1500);
    });
  }

  function copyPre(btn) {
    const pre = btn.parentElement;
    const text = pre.innerText.replace('Copiar', '').trim();
    navigator.clipboard.writeText(text).then(() => {
      btn.textContent = 'Copiado!';
      setTimeout(() => btn.textContent = 'Copiar', 1500);
    });
  }

  // Highlight nav item on scroll
  const navItems = document.querySelectorAll('.nav-item');
  const sections = ['me','myproducts','myproducts-sync','myorders','myorders-sync','productads','token-status','token-refresh','debug-env'];

  window.addEventListener('scroll', () => {
    let current = '';
    sections.forEach(id => {
      const el = document.getElementById(id);
      if (el && el.getBoundingClientRect().top < 120) current = id;
    });
    navItems.forEach(item => {
      item.classList.toggle('active', item.getAttribute('href') === '#' + current);
    });
  });
</script>
</body>
</html>"""


def docs_view(request):
    return HttpResponse(DOCS_HTML, content_type="text/html; charset=utf-8")
