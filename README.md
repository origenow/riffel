# Riffel Backend (Integração Mercado Livre)

Esta é a aplicação backend desenvolvida em Django para gerenciar a integração com a API do Mercado Livre. O sistema possui suporte multi-usuário (multi-tenant) com autenticação OAuth2 completa, permitindo gerenciar produtos, pedidos e anúncios (Product Ads) de diferentes contas simultaneamente. O banco de dados primário utilizado é o Supabase.

## 🚀 Tecnologias Utilizadas

- **Framework Web:** Django & Django REST Framework
- **Banco de Dados:** Supabase (PostgreSQL)
- **Integração:** API Oficial do Mercado Livre
- **Autenticação:** Mercado Livre OAuth2
- **Linguagem:** Python 3

## 🎯 Principais Funcionalidades

- **Autenticação Mercado Livre (OAuth2):** 
  - Fluxo completo de login e autorização.
  - Renovação automática (refresh) dos tokens de acesso.
  - Suporte para múltiplas contas conectadas no mesmo backend.
- **Sincronização de Produtos:** Consulta e atualiza informações de produtos do Mercado Livre.
- **Gerenciamento de Pedidos:** Busca e atualização do status de pedidos via API e processes assíncronos.
- **Métricas e Product Ads:** 
  - Coleta de métricas e status das campanhas de Product Ads.
  - Consulta detalhada dos anúncios (Ads) por campanha (via Nome ou ID).

## 📁 Estrutura do Projeto

- `/core`: Configurações principais do Django (`settings.py`, `urls.py`, etc).
- `/mercadolivre`: App principal contendo as integrações, views de API, serviços de sincronização e gerenciamento de tokens.
  - `auth_views.py`: Views do fluxo de OAuth2.
  - `orders_sync.py` e `orders_service.py`: Lógica de pedidos.
  - `products_sync.py`: Lógica de produtos.
  - `ml_api.py` / `ml_api_async.py`: Clients para comunicação com a API do ML.
  - `supabase_client.py`: Integração com o banco Supabase.
- `/scripts` ou arquivos na raiz (`pedidos_async.py`, `metrics.py`, etc): Scripts de automação inter-relacionados (agora refatorados para o fluxo multi-usuário).

## ⚙️ Configuração do Ambiente

1. **Crie e ative um ambiente virtual:**
   ```bash
   python -m venv venv
   # No Windows:
   venv\Scripts\activate
   # No Linux/Mac:
   source venv/bin/activate
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure as Variáveis de Ambiente:**
   Crie um arquivo `.env` na raiz do projeto com base nas seguintes chaves:
   ```env
   # Configurações do Mercado Livre
   ML_APP_ID=seu_app_id
   ML_SECRET_KEY=sua_secret_key
   ML_REDIRECT_URI=https://seu-dominio.com/auth/callback

   # Configurações do Supabase
   SUPABASE_URL=sua_url_supabase
   SUPABASE_KEY=sua_chave_supabase
   
   # Configurações do Django
   SECRET_KEY=sua_secret_key_django
   DEBUG=True ou False
   ```

4. **Execute as Migrações do Supabase:**
   O banco local não utiliza migrações padrão do Django para tudo, rely no Supabase. Para adaptar a base aos novos requisitos de multi-usuário, rode no SQL Editor do Supabase o conteúdo dos arquivos `.sql` disponíveis, por exemplo: `supabase_multi_user_migration.sql`.

5. **Inicie o servidor de desenvolvimento:**
   ```bash
   python manage.py runserver
   ```

## 📚 Documentação Adicional

A aplicação possui outros documentos mais detalhados para componentes específicos:

- **[Guia de Migração Multi-Usuário](MIGRATION_GUIDE.md):** Contém os passos de deploy e configuração.
- **[Resumo de Implementação](IMPLEMENTATION_SUMMARY.md):** Explica os refactors e melhorias arquiteturais adicionados no fluxo de usuários.
- **[Comparação de Endpoints](ENDPOINTS_COMPARISON.md):** Mapa do de-para dos antigos endpoints para os novos contendo `user_id`.
- **Docs da API:** Ao rodar a aplicação, explore `/docs` no navegador para utilizar a documentação interativa dos endpoints.

## 👥 Gerenciando Contas

Para conectar uma nova conta do Mercado Livre ao sistema:
- Acesse `http://localhost:8000/auth/login` em seu navegador.
- Autorize o aplicativo. O sistema fará o callback e salvará as permissões na tabela do Supabase.
- Acesse `http://localhost:8000/users` para verificação das contas atreladas ao backend.
