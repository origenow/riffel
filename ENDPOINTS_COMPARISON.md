# Comparação de Endpoints - Antes e Depois

## 📊 Resumo das Mudanças

- **Endpoints Removidos:** 8
- **Endpoints Novos:** 12
- **Endpoints Mantidos:** 2 (utilitários)
- **Total Atual:** 14 endpoints

---

## ❌ ANTES - Endpoints Antigos (Removidos)

### Conta
```
GET /me
```
Retorna dados da conta ML (sem especificar qual usuário)

### Produtos
```
GET  /myproducts
POST /myproducts/sync
```
Produtos do cache Supabase (usuário indefinido)

### Pedidos
```
GET  /myorders
POST /myorders/sync
```
Pedidos do cache Supabase (usuário indefinido)

### Anúncios
```
GET /productads?period=30
```
Métricas de Product Ads (usuário indefinido)

### Token
```
GET  /token/status
POST /token/refresh
```
Status e refresh do token (usuário indefinido)

### Utilitários
```
GET /debug/env
GET /docs
```
Diagnóstico e documentação

---

## ✅ DEPOIS - Endpoints Novos

### 🔐 Autenticação OAuth2 (NOVO)

#### `GET /auth/login`
**Descrição:** Inicia o fluxo de autenticação OAuth2 do Mercado Livre  
**Resposta:** Redireciona para página de autorização do ML  
**Exemplo:**
```bash
curl https://riffel.onrender.com/auth/login
# Redireciona para: https://auth.mercadolivre.com.br/authorization?...
```

#### `GET /auth/callback?code=TG-xxxxx`
**Descrição:** Recebe código de autorização e salva token no Supabase  
**Parâmetros:**
- `code` (query, obrigatório) - Código de autorização do ML
- `error` (query, opcional) - Erro caso autorização seja negada

**Resposta Sucesso (200):**
```json
{
  "message": "Autenticação realizada com sucesso!",
  "user_id": 533863251,
  "nickname": "RIFFEL2024",
  "email": "joao@riffel.com.br",
  "first_name": "João"
}
```

**Resposta Erro (400):**
```json
{
  "error": "Código de autorização não fornecido."
}
```

---

### 👥 Gerenciamento de Usuários (NOVO)

#### `GET /users`
**Descrição:** Lista todos os usuários conectados  
**Resposta (200):**
```json
{
  "total": 2,
  "users": [
    {
      "user_id": 533863251,
      "nickname": "RIFFEL2024",
      "email": "joao@riffel.com.br",
      "first_name": "João",
      "expires_at": "2025-02-19T08:00:00+00:00",
      "updated_at": "2025-02-19T02:00:00+00:00",
      "last_updated_me": "2025-02-19T02:00:00+00:00"
    },
    {
      "user_id": 987654321,
      "nickname": "LOJA_ABC",
      "email": "contato@lojaabc.com",
      "first_name": "Maria",
      "expires_at": "2025-02-19T09:00:00+00:00",
      "updated_at": "2025-02-19T03:00:00+00:00",
      "last_updated_me": "2025-02-19T03:00:00+00:00"
    }
  ]
}
```

#### `GET /users/{user_id}`
**Descrição:** Retorna detalhes de um usuário específico  
**Parâmetros:**
- `user_id` (path, obrigatório) - ID do usuário no Mercado Livre

**Resposta (200):**
```json
{
  "user_id": 533863251,
  "nickname": "RIFFEL2024",
  "email": "joao@riffel.com.br",
  "first_name": "João",
  "token_type": "Bearer",
  "expires_at": "2025-02-19T08:00:00+00:00",
  "scope": "offline_access read write",
  "updated_at": "2025-02-19T02:00:00+00:00",
  "last_updated_me": "2025-02-19T02:00:00+00:00"
}
```

**Resposta Erro (404):**
```json
{
  "error": "Usuário 533863251 não encontrado."
}
```

#### `DELETE /users/{user_id}/delete`
**Descrição:** Remove a conexão de um usuário  
**Parâmetros:**
- `user_id` (path, obrigatório) - ID do usuário a ser removido

**Resposta (200):**
```json
{
  "message": "Usuário 533863251 removido com sucesso.",
  "user_id": 533863251
}
```

---

### 📦 Endpoints por Usuário (MODIFICADOS - user_id obrigatório)

#### `GET /users/{user_id}/me`
**Antes:** `GET /me`  
**Descrição:** Dados da conta do Mercado Livre  
**Parâmetros:**
- `user_id` (path, obrigatório) - ID do usuário

**Resposta (200):**
```json
{
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
}
```

#### `GET /users/{user_id}/myproducts`
**Antes:** `GET /myproducts`  
**Descrição:** Lista produtos do cache Supabase  
**Parâmetros:**
- `user_id` (path, obrigatório) - ID do usuário

**Resposta (200):**
```json
{
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
}
```

#### `POST /users/{user_id}/myproducts/sync`
**Antes:** `POST /myproducts/sync`  
**Descrição:** Força sincronização imediata dos produtos  
**Parâmetros:**
- `user_id` (path, obrigatório) - ID do usuário

**Resposta (200):**
```json
{
  "message": "Sincronizacao concluida!",
  "total_items": 42,
  "last_sync_at": "2026-02-20T14:30:00+00:00"
}
```

#### `GET /users/{user_id}/myorders`
**Antes:** `GET /myorders`  
**Descrição:** Lista pedidos do cache Supabase com conciliação financeira  
**Parâmetros:**
- `user_id` (path, obrigatório) - ID do usuário

**Resposta (200):**
```json
{
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
}
```

#### `POST /users/{user_id}/myorders/sync`
**Antes:** `POST /myorders/sync`  
**Descrição:** Força sincronização imediata dos pedidos  
**Parâmetros:**
- `user_id` (path, obrigatório) - ID do usuário

**Resposta (200):**
```json
{
  "message": "Sincronizacao de pedidos concluida!",
  "total_items": 1634,
  "last_sync_at": "2026-02-20T14:30:00+00:00"
}
```

#### `GET /users/{user_id}/productads?period=30`
**Antes:** `GET /productads?period=30`  
**Descrição:** Métricas de Product Ads por período (Atualizado para v2 e métricas ROAS)  
**Parâmetros:**
- `user_id` (path, obrigatório) - ID do usuário
- `period` (query, opcional) - Período em dias: 7, 15, 30, 60, 90 (padrão: 30)

**Resposta (200):**
```json
{
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
      "id": 355189450,
      "name": "Campanha Tênis",
      "status": "active",
      "roas_target": 2.0,
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
}
```

#### `GET /users/{user_id}/productads/campaigns/{campaign_id}/ads` (NOVO)
**Descrição:** Lista todos os anúncios (produtos) de uma campanha específica  
**Parâmetros:**
- `user_id` (path, obrigatório) - ID do usuário
- `campaign_id` (path, obrigatório) - ID ou Nome da campanha

**Resposta (200):**
```json
{
  "requested_campaign": "Campanha Tênis",
  "resolved_campaign_id": 355189450,
  "total": 42,
  "results": [
    {
      "item_id": "MLB3456789012",
      "ad_group_id": 1105406861,
      "title": "Tenis Esportivo Running Pro",
      "price": 199.90,
      "status": "active",
      "image": "https://http2.mlstatic.com/D_NQ_NP_...",
      "metrics": {
          "clicks": 15,
          "total_amount": 399.80,
          "roas": 5.2
      }
    }
  ]
}
```

#### `GET /users/{user_id}/token/status`
**Antes:** `GET /token/status`  
**Descrição:** Status do token armazenado  
**Parâmetros:**
- `user_id` (path, obrigatório) - ID do usuário

**Resposta (200):**
```json
{
  "user_id": 533863251,
  "token_type": "Bearer",
  "expires_at": "2025-02-19T08:00:00+00:00",
  "scope": "offline_access read write",
  "updated_at": "2025-02-19T02:00:00+00:00"
}
```

#### `POST /users/{user_id}/token/refresh`
**Antes:** `POST /token/refresh`  
**Descrição:** Força refresh manual do token  
**Parâmetros:**
- `user_id` (path, obrigatório) - ID do usuário

**Resposta (200):**
```json
{
  "message": "Token atualizado com sucesso!",
  "user_id": 533863251,
  "expires_at": "2025-02-19T14:00:00+00:00"
}
```

---

### 🛠️ Utilitários (SEM ALTERAÇÃO)

#### `GET /debug/env`
**Descrição:** Diagnóstico de variáveis de ambiente  
**Resposta (200):**
```json
{
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
}
```

#### `GET /docs`
**Descrição:** Documentação interativa da API  
**Resposta:** HTML com documentação completa

---

## 🔄 Exemplo de Migração

### Antes (Antigo)
```bash
# Buscar produtos (não especifica qual usuário)
curl https://riffel.onrender.com/myproducts

# Buscar pedidos (não especifica qual usuário)
curl https://riffel.onrender.com/myorders
```

### Depois (Novo)
```bash
# 1. Listar usuários disponíveis
curl https://riffel.onrender.com/users

# 2. Buscar produtos de um usuário específico
curl https://riffel.onrender.com/users/533863251/myproducts

# 3. Buscar pedidos de outro usuário
curl https://riffel.onrender.com/users/987654321/myorders
```

---

## 📝 Notas Importantes

1. **user_id é obrigatório** em todos os endpoints de dados (exceto auth e users)
2. **Refresh automático** de tokens acontece em cada requisição se necessário
3. **Múltiplas contas** podem ser conectadas simultaneamente
4. **Sem tokens hardcoded** - tudo gerenciado via OAuth2
5. **Compatibilidade:** Endpoints antigos foram removidos - atualize suas integrações

---

## 🎯 Benefícios

✅ **Segurança:** OAuth2 completo sem tokens expostos  
✅ **Multi-tenant:** Suporte a múltiplas contas  
✅ **Organização:** Endpoints claros e estruturados  
✅ **Escalabilidade:** Fácil adicionar novas contas  
✅ **Manutenção:** Refresh automático de tokens
