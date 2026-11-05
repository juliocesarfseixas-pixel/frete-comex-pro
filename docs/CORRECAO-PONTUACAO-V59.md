# Ajuste de consistência da pontuação — 04/11/2026

Detectada divergência: a interface V5.9 calculava a nota consolidada dos cinco departamentos se houvesse 80% de respostas válidas **no conjunto de 25**, enquanto o backend exige 80% **em cada departamento de cinco perguntas**.

## Correção aplicada ao pacote ZIP de homologação

Adicionar a função a seguir antes de `function fmt(n)`:

```javascript
function validDepartmentAggregate(){
  for(let start=10;start<35;start+=5){
    if(!eligible(start,start+5))return null;
  }
  return score(10,35);
}
```

Substituir as três ocorrências de `validScore(10,35)` por `validDepartmentAggregate()`. Assim, um departamento sem quatro respostas válidas bloqueia a nota consolidada, independentemente da quantidade total respondida nos demais departamentos.

**Estado:** pacote local corrigido, integridade ZIP e sintaxe dos dois blocos JavaScript verificadas com Node. A transferência dos 3 MB de HTML para o GitHub e o teste visual de navegador ainda são necessários.

**Atenção:** a nota geral do backend é a média de todas as respostas válidas nas seis dimensões; o dashboard visual mostra indicadores separados para governança e departamentos. Não rotular a nota departamental como índice geral do backend.
