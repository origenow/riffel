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
  <div class="nav-section">Autenticação</div>
  <a class="nav-item" href="#auth-login"><span class="badge badge-get">GET</span> /auth/login</a>
  <a class="nav-item" href="#auth-callback"><span class="badge badge-get">GET</span> /auth/callback</a>

  <div class="nav-section">Usuários</div>
  <a class="nav-item" href="#users-list"><span class="badge badge-get">GET</span> /users</a>
  <a class="nav-item" href="#user-detail"><span class="badge badge-get">GET</span> /users/{user_id}</a>
  <a class="nav-item" href="#user-delete"><span class="badge badge-del">DEL</span> /users/{user_id}/delete</a>

  <div class="nav-section">Dados (por Usuário)</div>
  <a class="nav-item active" href="#me"><span class="badge badge-get">GET</span> /users/{id}/me</a>
  <a class="nav-item" href="#myproducts"><span class="badge badge-get">GET</span> /users/{id}/myproducts</a>
  <a class="nav-item" href="#myorders"><span class="badge badge-get">GET</span> /users/{id}/myorders</a>
  <a class="nav-item" href="#productads"><span class="badge badge-get">GET</span> /users/{id}/productads</a>
  <a class="nav-item" href="#campaign-ads"><span class="badge badge-get">GET</span> /users/{id}/.../ads</a>

  <div class="nav-section">Util</div>
  <a class="nav-item" href="#token-status"><span class="badge badge-get">GET</span> /token/status</a>
  <a class="nav-item" href="#debug-env"><span class="badge badge-get">GET</span> /debug/env</a>
</aside>

<!-- MAIN CONTENT -->
<main class="main">

  <!-- PAGE HEADER -->
  <div class="page-header">
    <h1>Riffel API <span style="font-size: 1rem; color: var(--accent-light);">v2.0.0</span></h1>
    <p>API Django integrada ao Mercado Livre com suporte a <strong>múltiplas contas</strong> e autenticação OAuth2 automática.</p>
    <div class="base-url-box">
      <span class="label">Base URL</span>
      <code id="base-url">https://riffel.onrender.com</code>
      <button class="copy-btn" onclick="copyText('base-url', this)">Copiar</button>
    </div>
  </div>

  <!-- AUTH BOX -->
  <div class="auth-box">
    🔐 <strong>Arquitetura Multi-Usuário:</strong> A API armazena tokens de múltiplos usuários no Supabase. 
    Para endpoints de dados, o <code>user_id</code> do Mercado Livre é <strong>obrigatório</strong> na URL.
    Use o fluxo de <strong>Autenticação</strong> abaixo para conectar novas contas.
  </div>

  <!-- ═══════════════════════════ AUTENTICAÇÃO ═══════════════════════════ -->
  <div class="section-title" id="auth-login">Autenticação OAuth2</div>

  <div class="endpoint" id="ep-auth-login">
    <div class="endpoint-header" onclick="toggle('ep-auth-login')">
      <span class="method method-get">GET</span>
      <span class="endpoint-path">/auth/login</span>
      <span class="endpoint-summary">Inicia conexão com Mercado Livre</span>
      <span class="chevron">▼</span>
    </div>
    <div class="endpoint-body">
      <div class="endpoint-body-inner">
        <p class="desc">Redireciona o usuário para a página de autorização do Mercado Livre. Após autorizar, o ML redirecionará de volta para o callback da API.</p>
        <div class="res-header"><span class="status-badge s200">302 Redirect</span></div>
        <pre>Location: https://auth.mercadolivre.com.br/authorization?client_id=...</pre>
      </div>
    </div>
  </div>

  <div class="endpoint" id="ep-users-list" style="margin-top:12px">
    <div class="endpoint-header" onclick="toggle('ep-users-list')">
      <span class="method method-get">GET</span>
      <span class="endpoint-path">/users</span>
      <span class="endpoint-summary">Lista todas as contas conectadas</span>
      <span class="chevron">▼</span>
    </div>
    <div class="endpoint-body">
      <div class="endpoint-body-inner">
        <p class="desc">Retorna a lista de todos os usuários que já realizaram o login e possuem tokens ativos no sistema.</p>
        <div class="response-block">
          <div class="res-header"><span class="status-badge s200">200 OK</span></div>
          <pre>{
  "total": 1,
  "users": [
    {
      "user_id": 533863251,
      "nickname": "RIFFEL2024",
      "email": "joao@riffel.com.br",
      "updated_at": "2026-03-20T14:00:00Z"
    }
  ]
}</pre>
        </div>
      </div>
    </div>
  </div>

  <hr class="divider"/>

  <!-- ═══════════════════════════ DADOS ═══════════════════════════ -->
  <div class="section-title" id="me">Dados da Conta</div>

  <div class="endpoint" id="ep-me">
    <div class="endpoint-header" onclick="toggle('ep-me')">
      <span class="method method-get">GET</span>
      <span class="endpoint-path">/users/{user_id}/me</span>
      <span class="endpoint-summary">Perfil do usuário</span>
      <span class="chevron">▼</span>
    </div>
    <div class="endpoint-body">
      <div class="endpoint-body-inner">
        <p class="desc">Retorna os dados detalhados da conta ML do usuário: reputação, endereço e CNPJ formatado.</p>

        <div class="params-title">Path Parameters</div>
        <table>
          <tr><th>Nome</th><th>Tipo</th><th>Obrigatório</th><th>Descrição</th></tr>
          <tr><td><code>user_id</code></td><td>integer</td><td><span class="required">sim</span></td><td>ID numérico do usuário no Mercado Livre.</td></tr>
        </table>

        <div class="response-block">
          <div class="res-header"><span class="status-badge s200">200 OK</span></div>
          <pre>{ "nickname": "RIFFEL2024", "email": "joao@... " }</pre>
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
      <span class="endpoint-path">/users/{user_id}/myproducts</span>
      <span class="endpoint-summary">Produtos sincronizados</span>
      <span class="chevron">▼</span>
    </div>
    <div class="endpoint-body">
      <div class="endpoint-body-inner">
        <p class="desc">Retorna os produtos do <strong>cache Supabase</strong> (atualizado a cada 1h). Se o cache estiver vazio, executa um sync imediato automático.</p>

        <div class="params-title">Path Parameters</div>
        <table>
          <tr><th>Nome</th><th>Tipo</th><th>Obrigatório</th><th>Descrição</th></tr>
          <tr><td><code>user_id</code></td><td>integer</td><td><span class="required">sim</span></td><td>ID do usuário.</td></tr>
        </table>

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
      "status": "active",
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

          <div class="params-title" style="margin-top:16px">Valores possíveis de <code>status</code></div>
          <table class="params-table" style="margin-top:8px">
            <thead><tr><th>Valor</th><th>Descrição</th></tr></thead>
            <tbody>
              <tr><td><code>active</code></td><td>Ativo — anúncio visível e disponível para compra</td></tr>
              <tr><td><code>paused</code></td><td>Pausado — anúncio temporariamente suspenso pelo vendedor</td></tr>
              <tr><td><code>closed</code></td><td>Encerrado — anúncio finalizado e não disponível</td></tr>
              <tr><td><code>under_review</code></td><td>Sob revisão — anúncio em análise pelo Mercado Livre</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <div class="endpoint" id="ep-myproducts-sync" style="margin-top:12px">
    <div class="endpoint-header" onclick="toggle('ep-myproducts-sync')">
      <span class="method method-post">POST</span>
      <span class="endpoint-path">/users/{user_id}/myproducts/sync</span>
      <span class="endpoint-summary">Força atualização do cache</span>
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
      <span class="endpoint-path">/users/{user_id}/myorders</span>
      <span class="endpoint-summary">Histórico de vendas</span>
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
      "date_created": "2026-02-20T10:14:28.000-04:00",
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

          <div class="params-title" style="margin-top:16px">Campos de <code>vendas_detalhadas</code></div>
          <table class="params-table" style="margin-top:8px">
            <thead><tr><th>Campo</th><th>Tipo</th><th>Descrição</th></tr></thead>
            <tbody>
              <tr><td><code>order_id</code></td><td>string</td><td>Identificador único do pedido no Mercado Livre</td></tr>
              <tr>
                <td><code>date_created</code></td>
                <td>string (ISO 8601)</td>
                <td>
                  Data e hora de criação do pedido no formato <code>YYYY-MM-DDTHH:mm:ss.SSS±HH:mm</code><br/>
                  <span style="color:var(--text-muted);font-size:.82rem">Exemplo: <code>2026-02-20T10:14:28.000-04:00</code> — inclui offset de fuso horário retornado pelo ML</span>
                </td>
              </tr>
              <tr><td><code>unit_price</code></td><td>number</td><td>Preço unitário do item no pedido</td></tr>
              <tr><td><code>quantity</code></td><td>integer</td><td>Quantidade de unidades do item</td></tr>
              <tr><td><code>gross_item</code></td><td>number</td><td>Valor bruto do item (<code>unit_price × quantity</code>)</td></tr>
              <tr><td><code>gross_items_order</code></td><td>number</td><td>Valor bruto total do pedido (todos os itens)</td></tr>
              <tr><td><code>sale_fee_total_order</code></td><td>number</td><td>Taxa de venda cobrada pelo ML no pedido</td></tr>
              <tr><td><code>marketplace_fee_order</code></td><td>number</td><td>Comissão total do marketplace no pedido</td></tr>
              <tr><td><code>seller_shipping_cost</code></td><td>number</td><td>Custo de frete cobrado do vendedor</td></tr>
              <tr><td><code>net_order_simplified</code></td><td>number</td><td>Valor líquido do pedido (<code>bruto − taxas − frete</code>)</td></tr>
              <tr><td><code>discount_total_order</code></td><td>number</td><td>Total de descontos aplicados no pedido</td></tr>
            </tbody>
          </table>
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
  <div class="section-title" id="productads">Publicidade (Product Ads)</div>

  <div class="endpoint" id="ep-productads">
    <div class="endpoint-header" onclick="toggle('ep-productads')">
      <span class="method method-get">GET</span>
      <span class="endpoint-path">/users/{user_id}/productads</span>
      <span class="endpoint-summary">Métricas de campanhas (ROAS v2)</span>
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

  <div class="endpoint" id="ep-campaign-ads" style="margin-top:12px">
    <div class="endpoint-header" onclick="toggle('ep-campaign-ads')">
      <span class="method method-get">GET</span>
      <span class="endpoint-path">/users/{user_id}/productads/campaigns/{id}/ads</span>
      <span class="endpoint-summary">Anúncios de uma campanha (v2)</span>
      <span class="chevron">▼</span>
    </div>
    <div class="endpoint-body">
      <div class="endpoint-body-inner">
        <p class="desc">Retorna todos os anúncios (items) vinculados a uma campanha específica de Product Ads, incluindo a <strong style="color:var(--accent-light)">imagem do produto</strong> em alta resolução. Permite consultar dinamicamente passando o <strong style="color:var(--accent-light)">ID numérico</strong> ou o <strong style="color:var(--accent-light)">Nome Exato</strong> da campanha.</p>

        <div class="params-title">Path Parameters</div>
        <table>
          <tr><th>Nome</th><th>Tipo</th><th>Obrigatório</th><th>Descrição</th></tr>
          <tr><td><code>user_id</code></td><td>integer</td><td><span class="required">sim</span></td><td>ID do usuário.</td></tr>
          <tr>
            <td><code>campaign_identifier</code></td>
            <td>string/int</td>
            <td><span class="required">sim</span></td>
            <td>ID ou Nome da campanha.</td>
          </tr>
        </table>

        <div class="params-title">Exemplos de uso</div>
        <pre><button class="copy-pre" onclick="copyPre(this)">Copiar</button>GET /productads/campaigns/12345/ads    → Busca via ID (1 requisição ao ML)
GET /productads/campaigns/Black Friday/ads → Busca via Nome (resolve ID automático)</pre>

        <br/>
        <div class="response-block">
          <div class="params-title">Resposta</div>
          <div class="res-header"><span class="status-badge s200">200 OK</span></div>
          <pre><button class="copy-pre" onclick="copyPre(this)">Copiar</button>{
  "requested_campaign": "Black Friday",
  "resolved_campaign_id": 1234567,
  "total": 1,
  "results": [
    {
      "id": "MLB123456789",
      "item_id": "MLB123456789",
      "ad_group_id": 1105406861,
      "status": "active",
      "title": "Produto Exemplo",
      "price": 179.9,
      "image": "...",
      "metrics": { "clicks": 15, "roas": 5.2 }
    }
  ]
}</pre>
          <div class="res-header" style="margin-top:12px"><span class="status-badge s404">404</span></div>
          <pre>{ "error": "Campanha não encontrada com o nome: Campanha Errada. Verifique se é exatamente o mesmo nome." }</pre>
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
      <span class="endpoint-path">/users/{user_id}/token/status</span>
      <span class="endpoint-summary">Status do OAuth2</span>
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
  const sections = ['me','myproducts','myproducts-sync','myorders','myorders-sync','productads','campaign-ads','token-status','token-refresh','debug-env'];

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
