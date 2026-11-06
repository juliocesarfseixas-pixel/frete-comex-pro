# Raio-X do Transportador — restauração da essência visual

**Estudo de reconstrução, não publicado.** Esta versão é uma proposta de base visual para homologação, não substitui V5.9 no GitHub/Render.

## Como abrir

1. Descompacte a pasta completa.
2. Abra `index.html` em Chrome, Edge ou Firefox.
3. Selecione **Explorar demonstração** para ver o relatório com dados fictícios ou **Iniciar diagnóstico** para responder às 35 perguntas originais.
4. No relatório, clique em **Salvar relatório em PDF**. Na janela de impressão escolha PDF, A4 e **gráficos de plano de fundo** para preservar a identidade azul-marinho.

## Base preservada

- A marca Raio-X do Transportador e o conceito Governo Empresarial 360°.
- Fotografia original do caminhão da versão V5.9, extraída do próprio pacote histórico.
- Catálogo V5.9 **idêntico** (35 perguntas, 175 alternativas e recomendações), disponível no arquivo `perguntas-v59-originais.json` e embutido no HTML para uso offline.
- Seis dimensões: governança corporativa (10); Tesouro e Pessoas; Estratégia e Governança; Frota e Patrimônio; Transportes e Operações; Comércio e Expansão (5 cada).
- Dois índices independentes: governança e departamentos; não há novo índice agregado usado como indicador principal.

## Regras de pontuação

- Respostas inteiras de 0 a 4. A opção “Não sei informar” exclui a questão da média.
- Governança exige ao menos 8 de 10 válidas; cada departamento exige 4 de 5 válidas.
- O índice consolidado departamental só aparece quando **todos** os cinco departamentos atingem 4/5 válidas.
- A classificação segue os cortes existentes da V5.9: crítico `<25`, inicial `<50`, em desenvolvimento `<70`, estruturado `<85`, avançado `>=85`.
- Recomendações extraídas das perguntas originais com menor pontuação (em caso de empate, ordem do catálogo).
- Dados fictícios são explicitamente identificados.

## Decisões de reformulação

1. Uma única identidade visual do início ao PDF: azul-marinho, dourado, azul-claro e a fotografia original.
2. Remoção de blocos redundantes de versões antigas: um dashboard, uma leitura executiva, um relatório.
3. Separação nítida entre visual de homologação e integração backend: o protótipo **não** armazena nem envia dados.
4. Sem CNPJ, WhatsApp, marketing ou consentimentos desnecessários; nome e e-mail obrigatórios apenas no formulário de avaliação (sem transmissão na prévia).
5. Sem promessas de auditoria/certificação, automação de retenção ou envio de e-mail inexistentes.
6. Sem renomear o produto para Frete COMEX PRO ou adicionar marca de outra empresa.

## Publicação

**Não publicar esta prévia diretamente.** Etapas futuras: revisão das regras de negócio, automação dos testes visuais, segurança, conexão com Supabase e Resend com credenciais privadas, QA no Render em serviço separado, aceitação expressa do design e publicação controlada.

## Fontes internas

`referencias/dashboard-original-azul-marinho.png` — dashboard V5.4 original;
`referencias/conceito-visual-original.png` — estudo visual anterior do Raio-X;
`assets/caminhao-original.webp` — imagem extraída do V5.9;
`perguntas-v59-originais.json` — perguntas fornecidas pelo histórico do projeto.