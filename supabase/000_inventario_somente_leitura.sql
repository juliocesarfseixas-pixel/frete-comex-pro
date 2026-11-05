-- Inventário somente leitura para homologação da V5.9
-- Executar no SQL Editor do Supabase e compartilhar apenas os resultados,
-- sem linhas de dados, credenciais ou informações pessoais.
SELECT table_schema, table_name,
       COALESCE(obj_description((quote_ident(table_schema)||'.'||quote_ident(table_name))::regclass),'') AS descricao
FROM information_schema.tables
WHERE table_schema NOT IN ('pg_catalog','information_schema','auth','storage','realtime','supabase_functions','extensions','vault','graphql','graphql_public','pgsodium','net')
  AND table_type='BASE TABLE'
ORDER BY table_schema, table_name;

SELECT table_schema, table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema NOT IN ('pg_catalog','information_schema','auth','storage','realtime','supabase_functions','extensions','vault','graphql','graphql_public','pgsodium','net')
ORDER BY table_schema, table_name, ordinal_position;

SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog','information_schema','auth','storage','realtime','supabase_functions','extensions','vault','graphql','graphql_public','pgsodium','net')
ORDER BY schemaname, tablename;
