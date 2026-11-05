# Integração V5.9 — Raio-X do Transportador

## Estado do projeto
Esta branch é de desenvolvimento. **Não realizar merge/deploy automático** antes dos testes.

### Requisitos aprovados
- Identidade independente: Raio-X do Transportador, sem marca Conexão Global.
- 35 perguntas com cinco alternativas específicas (notas 0–4) e "Não sei informar".
- 10 questões de governança e 25 questões distribuídas entre Tesouro e Pessoas, Estratégia e Governança, Frota e Patrimônio, Transportes e Operações, Comércio e Expansão.
- Exibir uma pergunta por vez; dashboard calculado apenas com respostas válidas.
- Exigir pelo menos 80% de respostas válidas em cada dimensão para exibir nota daquela dimensão.
- PDF com identificação da transportadora e relatório das respostas.
- Cadastro: nome da transportadora e e-mail obrigatórios; responsável opcional. Sem CNPJ, WhatsApp ou opt-in comercial.
- Aviso de privacidade acessível sem checkbox obrigatório. Responsável: Júlio Seixas; contato: juliocesarfseixas@gmail.com.

## Incompatibilidades identificadas na v1.4
1. `server.py:validate` exige 6 pilares x 4 respostas (24); a V5.9 usa 35 perguntas.
2. `make_pdf` monta relatório específico da precificação em 8 páginas, não corresponde ao dashboard de governança.
3. `POST /api/diagnosticos` exige `privacyAccepted === true`, contrariando o cadastro simplificado aprovado.
4. O modelo `diagnostics` e o painel `/admin` foram feitos para a metodologia antiga; migrar sem perder registros existentes.
5. O aviso atual promete retenção de até 180 dias, mas `cleanup()` não é agendado automaticamente.
6. A configuração atual permite SQLite local quando `DATABASE_URL` não existe; no Render gratuito isso não assegura persistência.
7. A aplicação V5.9 estática usa impressão do navegador para PDF; não afirmar envio por e-mail ou persistência antes da implementação.

## Ordem segura de implementação
1. Versionar os ativos V5.9 na branch sem substituir `index.html` da produção.
2. Implementar contrato versionado `/api/v59/*` e persistência separada/migração para preservar dados v1.4.
3. Testar validação, pontuação, casos "Não sei informar", limite de 80%, sanitização e relatório.
4. Configurar PostgreSQL/Supabase com credenciais somente no Render; aplicar RLS se houver acesso direto pelo cliente.
5. Verificar envio transacional com remetente validado, sem marketing, e confirmação de posse do endereço antes de compartilhar dados.
6. Testar política de privacidade, retenção efetiva, controles de acesso e proteção contra abuso.
7. Criar ambiente de prévia e validar ponta a ponta; só depois aprovar merge em `main` e deploy no Render.

Referências oficiais:
- LGPD: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm
- Render: https://render.com/docs/web-services
- Supabase RLS: https://supabase.com/docs/guides/database/postgres/row-level-security
