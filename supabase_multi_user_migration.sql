-- =====================================================
-- MIGRAÇÃO: Sistema Multi-Usuário
-- Adicionar user_id nas tabelas de dados
-- =====================================================

-- 1. Adicionar coluna user_id nas tabelas
ALTER TABLE mercadolivre_products 
ADD COLUMN IF NOT EXISTS user_id BIGINT;

ALTER TABLE mercadolivre_orders 
ADD COLUMN IF NOT EXISTS user_id BIGINT;

ALTER TABLE mercadolivre_orders_summary 
ADD COLUMN IF NOT EXISTS user_id BIGINT;

-- 2. Criar índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_products_user_id 
ON mercadolivre_products(user_id);

CREATE INDEX IF NOT EXISTS idx_orders_user_id 
ON mercadolivre_orders(user_id);

CREATE INDEX IF NOT EXISTS idx_orders_summary_user_id 
ON mercadolivre_orders_summary(user_id);

-- 3. Limpar dados existentes (fresh start)
DELETE FROM mercadolivre_products;
DELETE FROM mercadolivre_orders;
DELETE FROM mercadolivre_orders_summary;

-- 4. Verificar estrutura das tabelas
SELECT 'mercadolivre_products' as table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'mercadolivre_products'
ORDER BY ordinal_position;

SELECT 'mercadolivre_orders' as table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'mercadolivre_orders'
ORDER BY ordinal_position;

SELECT 'mercadolivre_orders_summary' as table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'mercadolivre_orders_summary'
ORDER BY ordinal_position;
