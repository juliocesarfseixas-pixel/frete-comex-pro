# Frete COMEX PRO — Raio-X da Precificação v1.3

Aplicação web de diagnóstico (24 perguntas, 6 pilares) com geração direta de relatório PDF de 8 páginas. **Piloto sem cadastro e sem armazenamento de respostas no servidor.**

## Executar localmente

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python server.py
```

Abra http://localhost:8000. Endpoint de saúde: http://localhost:8000/health.

## Publicar no Render (plano gratuito, sujeito às condições vigentes)

1. Crie um repositório **privado** no GitHub e envie os arquivos desta pasta para a raiz do repositório (incluindo `render.yaml`). **Não envie dados de participantes ou PDFs reais.**
2. Entre em https://dashboard.render.com e escolha **New > Blueprint**.
3. Conecte sua conta GitHub e selecione o repositório. Confirme o serviço e o plano `free` antes de implantar.
4. Aguarde o deploy e abra a URL `https://<nome-do-servico>.onrender.com` exibida pelo Render.
5. Teste `/health`, preencha as 24 perguntas e faça o download do PDF.

Se o Blueprint não oferecer plano gratuito na conta/região, não confirme serviço pago sem verificar o preço. Alternativamente, crie **New > Web Service**, com Build `pip install -r requirements.txt` e Start `python server.py`.

## Segurança e limitações

- Servidor recalcula a pontuação, valida as 24 respostas e não aceita acesso a arquivos internos via GET.
- PDF é gerado em memória e retornado ao navegador. Nenhum banco de dados, cadastro ou envio por e-mail foi implementado.
- Cabeçalhos de proteção básicos, limite de tamanho de payload e limitação simples por IP (15 PDFs/hora/instância). **Limitação em memória não é proteção completa contra abuso** e reinicia com a instância.
- O tráfego público utiliza HTTPS disponibilizado pela plataforma de hospedagem.
- **Não usar com dados pessoais de clientes reais antes de publicar política de privacidade, revisar bases legais, retenção e fornecedores**, e concluir testes de segurança.
- Instâncias gratuitas podem hibernar, reiniciar e ter limitações de desempenho. O serviço não está configurado para produção com SLA.
- Não existe autenticação; o link é acessível a qualquer pessoa que o receba.
- A metodologia de maturidade é gerencial, não validada estatisticamente, e não substitui auditoria ou análise de conformidade.

Referências: https://render.com/docs/blueprint-spec e https://render.com/docs/free ; LGPD: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm
