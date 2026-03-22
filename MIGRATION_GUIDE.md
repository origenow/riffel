# Guia de Migração - Sistema Multi-Usuário OAuth2

## 🎯 O que mudou?

O sistema foi atualizado para suportar **múltiplas contas do Mercado Livre** com autenticação OAuth2 dinâmica. Agora você pode conectar várias contas e fazer consultas específicas por usuário.

## 📋 Mudanças nos Endpoints

### ❌ Endpoints REMOVIDOS (antigos)
```
GET  /me
GET  /myproducts
POST /myproducts/sync
GET  /myorders
POST /myorders/sync
GET  /productads
GET  /token/status
POST /token/refresh
```

### ✅ Endpoints NOVOS

#### Autenticação OAuth2
```
GET  /auth/login          → Inicia fluxo de autenticação
GET  /auth/callback       → Callback do Mercado Livre (automático)
```

#### Gerenciamento de Usuários
```
GET    /users                    → Lista todos os usuários conectados
GET    /users/{user_id}          → Detalhes de um usuário
DELETE /users/{user_id}/delete   → Remove conexão de um usuário
```

#### Endpoints por Usuário (user_id obrigatório)
```
GET  /users/{user_id}/me
GET  /users/{user_id}/myproducts
POST /users/{user_id}/myproducts/sync
GET  /users/{user_id}/myorders
POST /users/{user_id}/myorders/sync
GET  /users/{user_id}/productads?period=30
GET  /users/{user_id}/token/status
POST /users/{user_id}/token/refresh
```

#### Utilitários (sem alteração)
```
GET  /debug/env
GET  /docs
```

## 🔄 Como Migrar

### 1. Atualizar Tabela Supabase

Execute no SQL Editor do Supabase:

```sql
-- Adicionar novas colunas à tabela mercadolivre_tokens
ALTER TABLE mercadolivre_tokens 
ADD COLUMN IF NOT EXISTS nickname TEXT,
ADD COLUMN IF NOT EXISTS email TEXT,
ADD COLUMN IF NOT EXISTS first_name TEXT,
ADD COLUMN IF NOT EXISTS last_updated_me TIMESTAMPTZ;

-- Criar índice para melhor performance
CREATE INDEX IF NOT EXISTS idx_mercadolivre_tokens_user_id 
ON mercadolivre_tokens(user_id);
```

### 2. Conectar Primeira Conta

1. Acesse: `https://seu-dominio.com/auth/login`
2. Autorize a aplicação no Mercado Livre
3. Você será redirecionado de volta com a conta conectada

### 3. Atualizar Chamadas à API

**ANTES:**
```bash
curl https://seu-dominio.com/myproducts
```

**DEPOIS:**
```bash
# Primeiro, liste os usuários disponíveis
curl https://seu-dominio.com/users

# Depois, use o user_id nas chamadas
curl https://seu-dominio.com/users/533863251/myproducts
```

### 4. Exemplo Completo de Uso

```bash
# 1. Conectar nova conta
curl https://seu-dominio.com/auth/login
# (Abre no navegador e autoriza)

# 2. Listar contas conectadas
curl https://seu-dominio.com/users

# Resposta:
# {
#   "total": 2,
#   "users": [
#     {
#       "user_id": 533863251,
#       "nickname": "RIFFEL2024",
#       "email": "joao@riffel.com.br",
#       "first_name": "João",
#       "expires_at": "2025-02-19T08:00:00+00:00"
#     },
#     {
#       "user_id": 987654321,
#       "nickname": "LOJA_ABC",
#       "email": "contato@lojaabc.com",
#       "first_name": "Maria",
#       "expires_at": "2025-02-19T09:00:00+00:00"
#     }
#   ]
# }

# 3. Consultar produtos de um usuário específico
curl https://seu-dominio.com/users/533863251/myproducts

# 4. Consultar pedidos de outro usuário
curl https://seu-dominio.com/users/987654321/myorders

# 5. Remover uma conta
curl -X DELETE https://seu-dominio.com/users/987654321/delete
```

## 🔒 Variáveis de Ambiente Necessárias

Certifique-se de que estas variáveis estão configuradas:

```env
# Supabase
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-chave-supabase

# Mercado Livre OAuth2
ML_APP_ID=seu-app-id
ML_SECRET_KEY=sua-secret-key
ML_REDIRECT_URI=https://seu-dominio.com/auth/callback
```

**IMPORTANTE:** O `ML_REDIRECT_URI` deve estar cadastrado nas configurações da sua aplicação no [Mercado Livre Developers](https://developers.mercadolivre.com.br/).

## ⚠️ Comportamento de Erros

### Se user_id não for informado:
```json
{
  "error": "user_id é obrigatório"
}
```
**Status:** 400 Bad Request

### Se user_id não existir:
```json
{
  "error": "Usuário 123456 não encontrado."
}
```
**Status:** 404 Not Found

### Se token estiver expirado:
O sistema faz **refresh automático**. Se o refresh falhar:
```json
{
  "error": "Token inválido"
}
```
**Status:** 401 Unauthorized

## 📝 Scripts Standalone

Os scripts `metrics.py`, `products.py`, `pedidos_async.py` e `product_ads.py` foram **integrados à API Django**.

Para usá-los standalone, você precisa configurar manualmente os tokens:

```python
# metrics.py
ACCESS_TOKEN = "seu-token-aqui"

# products.py
ACCESS_TOKEN = "seu-token-aqui"
USER_ID = "seu-user-id-aqui"

# pedidos_async.py
BEARER_TOKEN = "seu-token-aqui"

# product_ads.py
ACCESS_TOKEN = "seu-token-aqui"
```

**Recomendação:** Use a API Django ao invés dos scripts standalone.

## 🔄 Refresh Automático de Tokens

O sistema verifica automaticamente se o token está próximo de expirar (menos de 30 minutos) e faz o refresh automaticamente em cada requisição.

Você também pode forçar um refresh manual:
```bash
POST /users/{user_id}/token/refresh
```

## 📊 Estrutura da Tabela Supabase

```
mercadolivre_tokens
├── id (uuid, PK)
├── user_id (bigint, unique) ← ID do Mercado Livre
├── access_token (text)
├── refresh_token (text)
├── token_type (text)
├── expires_in (integer)
├── expires_at (timestamp)
├── scope (text)
├── created_at (timestamp)
├── updated_at (timestamp)
├── nickname (text) ← NOVO
├── email (text) ← NOVO
├── first_name (text) ← NOVO
└── last_updated_me (timestamp) ← NOVO
```

## 🎉 Benefícios da Nova Arquitetura

✅ **Multi-conta:** Gerencie várias contas do Mercado Livre  
✅ **OAuth2 completo:** Autenticação segura e dinâmica  
✅ **Sem tokens hardcoded:** Maior segurança  
✅ **Refresh automático:** Tokens sempre válidos  
✅ **Organização:** Endpoints claros por usuário  
✅ **Escalável:** Fácil adicionar novas contas

## 🆘 Troubleshooting

### Erro: "Nenhum token encontrado"
**Solução:** Conecte uma conta via `/auth/login`

### Erro: "Usuário não encontrado"
**Solução:** Verifique se o `user_id` está correto usando `GET /users`

### Erro: "Token inválido"
**Solução:** Reconecte a conta via `/auth/login` ou force refresh via `/users/{user_id}/token/refresh`

### Erro no callback OAuth2
**Solução:** Verifique se `ML_REDIRECT_URI` está corretamente configurado no Mercado Livre Developers

## 📞 Suporte

Para mais informações, consulte a documentação completa em `/docs`
