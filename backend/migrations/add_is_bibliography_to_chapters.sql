-- Migration: Adicionar campo is_bibliography na tabela chapters
-- Execute este script no banco PostgreSQL para aplicar a migration

ALTER TABLE chapters ADD COLUMN IF NOT EXISTS is_bibliography BOOLEAN NOT NULL DEFAULT FALSE;

-- Verificar resultado
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'chapters' AND column_name = 'is_bibliography';
