-- Raio-X do Transportador V5.9 — migração isolada
-- Executar no SQL Editor do projeto Supabase após revisão.
-- Não altera a tabela diagnostics da aplicação v1.4.
-- Backend utiliza conexão PostgreSQL DATABASE_URL, não chave anon/service_role.
CREATE TABLE IF NOT EXISTS public.diagnostics_v59 (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at timestamptz NOT NULL DEFAULT now(),
    company_name text NOT NULL CHECK (char_length(company_name) BETWEEN 2 AND 120),
    email text NOT NULL CHECK (char_length(email) BETWEEN 3 AND 254),
    responsible text NOT NULL DEFAULT '',
    responses jsonb NOT NULL CHECK (jsonb_typeof(responses) = 'array' AND jsonb_array_length(responses) = 35),
    result jsonb NOT NULL CHECK (jsonb_typeof(result) = 'object'),
    email_status text NOT NULL DEFAULT 'not_requested'
      CHECK (email_status IN ('not_requested','pending','sent','failed','not_configured')),
    CHECK (char_length(responsible) <= 100)
);
CREATE INDEX IF NOT EXISTS idx_diagnostics_v59_created_at
    ON public.diagnostics_v59 (created_at DESC);

-- Acesso exclusivamente pelo backend, usando papel com permissão específica.
-- A API pública do Supabase não deve expor registros pessoais.
ALTER TABLE public.diagnostics_v59 ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.diagnostics_v59 FROM anon, authenticated;
-- Não criar policies públicas de SELECT/INSERT/UPDATE/DELETE.
-- Conexão do backend via papel PostgreSQL privilegiado deve ser controlada
-- por segredo no Render e protegida por TLS.
