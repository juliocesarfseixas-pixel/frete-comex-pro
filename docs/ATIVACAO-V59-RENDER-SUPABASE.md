# V5.9 — Plano de homologação e ativação segura

**Branch:** desenvolvimento-raio-x-v5-9 · **PR:** #1 (rascunho).
**Projeto Supabase informado:** snnwpiqkcabhvhcoeugo.
**Site público atual:** https://frete-comex-pro-raio-x.onrender.com — preservar.
**ATENÇÃO:** executar os comandos abaixo somente no ambiente de homologação ou após autorização específica.

## 1. Prévia visual sem banco e sem e-mail

Criar serviço Render de homologação **separado** apontando para esta branch.
Reaproveitar o mesmo build/start do serviço Python atual:
- Build: `pip install -r requirements.txt`
- Start: `python server.py`
- `ENABLE_V59_PREVIEW=1`
- `ENABLE_V59_STORAGE=0`
- `ENABLE_V59_EMAIL=0`
- **Não definir DATABASE_URL neste estágio.** O servidor usará SQLite isolado.
- Acessar `/v59-preview/` e `/api/v59/capabilities`.
- Conferir nome da transportadora, e-mail, 35 perguntas, 'Não sei informar',
  cálculos, dashboard, impressão e PDF executivo de 35 respostas.

## 2. Supabase existente — somente depois de inspeção e backup

1. Verificar permissões e tabelas existentes. Não apagar nem sobrescrever.
2. Revisar `supabase/003_raiox_v59_isolado.sql`. Ele cria o schema
   `raiox_v59`, uma tabela e um índice; não altera a tabela `public.diagnostics`.
3. Executar em projeto autorizado (preferencialmente staging/branch do Supabase).
4. Criar papel PostgreSQL privado com permissões mínimas de esquema e tabela;
   nunca enviar senha/chave ao HTML, GitHub ou chat.
5. Configurar `DATABASE_URL` somente nas variáveis secretas do Render.
   Copiar URL da caixa **Connect** do projeto; não presumir hostname do pooler.
   Sessão (porta 5432) é geralmente indicada para backend persistente quando IPv4.
6. Habilitar `ENABLE_V59_STORAGE=1` apenas após teste com empresa fictícia.
7. Validar que `GET /api/v59/capabilities` retorna `storage:true`.
8. Confirmar que a gravação ocorre exclusivamente em `raiox_v59.diagnostics`.

O módulo `v59_storage.py` utiliza SQL parametrizado. A gravação ocorre somente
quando o usuário solicita o registro na interface.

## 3. Entrega transacional via Resend

1. Verificar domínio do remetente no Resend e configurar segredos
   `RESEND_API_KEY` e `EMAIL_FROM` no serviço de homologação.
2. Validar PDF com dados fictícios e endereço de teste controlado.
3. Somente após aprovação, definir `ENABLE_V59_EMAIL=1`.
4. O resultado `accepted` significa aceito pela API, **não** entregue ao destinatário.
   Uma chave de idempotência acompanha cada diagnóstico.

**LGPD:** antes de habilitar registro com dados reais, concluir revisão jurídica
do aviso de privacidade, definir prazo de retenção, rotina de exclusão, gestão
de solicitações de titulares e medidas de segurança. A exclusão automática dos
diagnósticos V5.9 **não** está implementada.

## 4. Critérios de bloqueio para publicação

- [x] Frontend original versionado e capa sem marca Frete COMEX PRO
- [x] Catálogo imutável com 35 enunciados e 175 alternativas
- [x] Motor e API versionados, sem substituir rotas anteriores
- [x] PDF executivo com todas as perguntas e ações, renderizado localmente
- [x] Registro no banco e envio por e-mail atrás de flags, sem execução real
- [x] Teste manual local em Chromium com as 35 respostas preenchidas
- [ ] Resultado verde da última execução de GitHub Actions
- [ ] Banco Supabase conectado e migração executada com autorização
- [ ] Entrega real Resend comprovada com domínio verificado
- [ ] Teste funcional no serviço Render separado
- [ ] Política de retenção aprovada e implementada
- [ ] Aprovação expressa para mesclar PR #1 e publicar a V5.9

## Fontes técnicas oficiais
- Supabase conexão PostgreSQL: https://supabase.com/docs/guides/database/connecting-to-postgres
- Resend envio por API: https://resend.com/docs/api-reference/emails/send-email
- Resend idempotência: https://resend.com/blog/engineering-idempotency-keys
