-- V5.9: nova migração recomendada (substitui 002, NÃO execute 002).
-- Mantém intactas todas as tabelas existentes no esquema public.
-- Executar apenas após backup e aprovação de implantação.
BEGIN;
CREATE SCHEMA IF NOT EXISTS raiox_v59;
REVOKE ALL ON SCHEMA raiox_v59 FROM PUBLIC, anon, authenticated;
CREATE TABLE IF NOT EXISTS raiox_v59.diagnostics (
    id uuid PRIMARY KEY,
    created_at timestamptz NOT NULL DEFAULT now(),
    company_name text NOT NULL CHECK (char_length(company_name) BETWEEN 2 AND 120),
    email text NOT NULL CHECK (char_length(email) BETWEEN 3 AND 254),
    responsible text NOT NULL DEFAULT '' CHECK (char_length(responsible) <= 100),
    responses jsonb NOT NULL CHECK (
      jsonb_typeof(responses) = 'array'
      AND jsonb_array_length(responses) = 35
    ),
    result jsonb NOT NULL CHECK (jsonb_typeof(result) = 'object'),
    email_status text NOT NULL DEFAULT 'not_requested'
);
CREATE INDEX IF NOT EXISTS idx_v59_diagnostics_created_at
    ON raiox_v59.diagnostics(created_at DESC);
ALTER TABLE raiox_v59.diagnostics ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON raiox_v59.diagnostics FROM PUBLIC, anon, authenticated;
COMMIT;

-- Atenção: a conta PostgreSQL usada pelo backend precisa de USAGE no
-- esquema e INSERT/SELECT/UPDATE nas tabelas. Conceder permissões mínimas
-- apenas ao papel privado do servidor, nunca a anon/authenticated.
-- Não inserir URL de banco, senha ou service_role no repositório.
