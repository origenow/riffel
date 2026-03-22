-- =====================================================
-- MIGRAÇÃO: Adicionar colunas de informações do usuário
-- Tabela: mercadolivre_tokens
-- =====================================================

-- 1. Adicionar novas colunas
ALTER TABLE mercadolivre_tokens 
ADD COLUMN IF NOT EXISTS nickname TEXT,
ADD COLUMN IF NOT EXISTS first_name TEXT,
ADD COLUMN IF NOT EXISTS last_updated_me TIMESTAMPTZ;

-- 2. Criar índice para melhor performance
CREATE INDEX IF NOT EXISTS idx_mercadolivre_tokens_user_id 
ON mercadolivre_tokens(user_id);

-- 3. Verificar estrutura da tabela
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'mercadolivre_tokens'
ORDER BY ordinal_position;
