# Homologação V5.9 — checklist de liberação

> Este checklist é para a branch de desenvolvimento. Não habilitar deploy automático no serviço Render atual.

## Evidência automatizada
- [x] Motor de pontuação de 35 respostas com 80% mínimo por dimensão.
- [x] Cadastro mínimo e PDF preliminar.
- [x] Rotas versionadas `POST /api/v59/preview` e `POST /api/v59/relatorio`.
- [x] Testes HTTP em servidor temporário (GitHub Actions, execução #4: https://github.com/juliocesarfseixas-pixel/frete-comex-pro/actions/runs/41947138722).

## Ainda bloqueia a publicação
- [ ] Integrar os 35 enunciados e as 175 alternativas **exatas** do pacote V5.9 aprovado, sem substituir por opções genéricas.
- [ ] Integrar capa com caminhão, dashboard, prioridades e relatório completo.
- [ ] Verificar o fluxo de cadastro sem checkbox e sem marketing.
- [ ] Testar acessibilidade, celular, impressão, notas com respostas insuficientes.
- [ ] Revisar privacidade, logs, retenção, envio de e-mail e controle de acesso.
- [ ] Validar banco PostgreSQL/Supabase e migração de dados sem sobrescrever v1.4.
- [ ] Subir uma prévia separada no Render e obter aprovação expressa antes de mesclar na `main`.

## Pacote visual de referência
O pacote V5.9 de publicação possui `public/index.html`, `public/privacidade.html` e `public/termos.html`. Ele é um site estático que gera PDF via impressão do navegador, **não** está integrado ao backend Python. Deve ser incorporado como artefato versionado, preservando seu catálogo e sua capa, antes de disponibilizar uma prévia no serviço web existente.

## Contrato provisório da API
`POST /api/v59/preview`:
```json
{"company":{"name":"Transportadora Exemplo","email":"teste@example.com","responsible":""},"responses":[0,1,2,3,4,null,0,1,2,3,4,0,1,2,3,4,0,1,2,3,4,0,1,2,3,4,0,1,2,3,4,0,1,2,3,4]}
```
Responde com pontuações, `stored:false` e `emailSent:false`.

`POST /api/v59/relatorio`: mesmo corpo; devolve PDF preliminar.

**Não coletar avaliações reais via API de prévia** até concluir segurança, armazenamento e entrega.
