# Frete COMEX PRO — Raio-X v1.4

## O que foi implementado
- Diagnóstico gratuito com 24 perguntas e relatório PDF direto (8 páginas).
- Cadastro opcional de e-mail e opt-in comercial separado.
- Persistência de diagnósticos em PostgreSQL (ou SQLite somente para testes locais).
- Painel administrativo agregado em `/admin`, protegido por HTTP Basic Authentication.
- Envio do PDF via API Resend, quando configurado. Download direto funciona sem e-mail.
- Retenção: `RETENTION_DAYS`, padrão 180 dias; a rotina de limpeza deve ser agendada externamente para exclusão efetiva (não há agendador incluído).

## Executar localmente
`pip install -r requirements.txt` e `python server.py`; acesse `http://localhost:8000`.
Sem `DATABASE_URL`, o SQLite local é criado automaticamente.

## Render — atualização a partir da v1.3
1. Faça backup da v1.3 e envie os arquivos da v1.4 para o MESMO repositório GitHub.
2. Configure as variáveis secretas no Render: `DATABASE_URL` (PostgreSQL persistente externo), `ADMIN_PASSWORD` (senha longa e aleatória), `ADMIN_USER` (opcional).
3. Opcional: `RESEND_API_KEY` e `EMAIL_FROM` (remetente de domínio verificado no Resend). Sem esses valores, o cadastro funciona, mas o envio não ocorre; o PDF pode ser baixado.
4. Faça o deploy, teste `/health`, as 24 perguntas, o registro, o PDF e `/admin`.
5. No Render gratuito, o disco local é efêmero. **Não use SQLite para registros reais no Render.** O serviço requer banco PostgreSQL externo para persistência.

## Segurança e privacidade — antes de usar com terceiros
- Configure identificação e canal de contato do controlador no aviso de privacidade, e revise a base legal, fornecedores, direitos dos titulares, transferência internacional e política de retenção.
- O painel usa HTTP Basic e não tem autenticação corporativa, trilha de auditoria ou proteção avançada. Use apenas em piloto restrito; coloque autenticação de borda/SSO antes de produção.
- Não há confirmação de posse do e-mail, proteção antispam distribuída, filas de e-mail, nem rotina automática de limpeza; adicione antes de escalar.
- `RETENTION_DAYS` é configurável, mas a exclusão depende de chamar a função `cleanup()` em uma tarefa agendada externa. Não prometa exclusão automática antes de configurá-la.
- Para não enviar dados de terceiros a um endereço digitado indevidamente, use e-mails próprios/autorizados nos testes e implemente verificação de e-mail antes de abertura pública.
- As respostas são autoavaliação gerencial, não auditoria ou cálculo de lucro.

## Rotas
- `GET /` — formulário
- `GET /health` — saúde
- `POST /api/relatorio` — PDF sem cadastro
- `POST /api/diagnosticos` — registro e envio opcional
- `GET /admin` — painel protegido
- `GET /api/admin/stats` — indicadores agregados protegidos

## Custo
Render gratuito pode suspender por inatividade. Banco persistente externo e serviço de e-mail podem ter custos/limites próprios. Confira planos antes de configurar.
