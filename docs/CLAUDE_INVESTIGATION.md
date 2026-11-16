# Investigação da validação parcial — 2026-11-16

Investigação exclusivamente offline. Nenhuma nova chamada Anthropic, publicação, push ou leitura de credencial foi realizada. A evidência original em `reports/claude_validation.md` foi preservada.

## Diagnóstico

O relatório registra três requisições bem-sucedidas ao modelo Sonnet 5.5. Na rodada 1, o Claude solicitou `rank_restaurants` com `{"limit": 5}` e `get_kpis` com `{}`. Na rodada 2, solicitou `get_restaurant_details` com `{"restaurant_id": "LOJA-03"}`. As três funções retornaram `success=true`; uma reprodução local de cada chamada confirmou igualdade integral dos resultados, inclusive a série diária da loja.

Na rodada 3, a API retornou `stop_reason=max_tokens`, `output_tokens=1000` e `thinking_tokens=1000`. A resposta textual final está vazia. O modelo consumiu o orçamento de saída em raciocínio antes de produzir uma conclusão. A classificação INCOMPLETO está correta. Não houve falha das ferramentas nem esgotamento do limite de cinco rodadas. O relatório não permite investigar o conteúdo interno do raciocínio, e ele não foi solicitado nem registrado.

Não existem números em uma conclusão textual do Claude para comparar. Os números das ferramentas conferem: 1.200 pedidos, 1.139 entregues, 61 cancelados; loja líder LOJA-03, 126 pedidos, 120 entregues, 6 cancelados, atraso de 96,67% (116/120), cancelamento de 4,76% (6/126) e escore 64,5. Recomendações e causalidade não foram validadas.

Somando todas as respostas, foram registrados 4.789 tokens de entrada e 1.139 de saída. Entrada repetida entre rodadas conta em cada requisição; saída inclui raciocínio. Esses totais não são uma auditoria da cobrança.

## Correções

- No Sonnet 5.5, o agente envia `thinking={"type":"between_tools"}` e `output_config={"effort":"low"}`. A configuração anterior deixava o padrão adaptativo/high consumir o orçamento. A [documentação oficial](https://platform.claude.com/docs/en/models/sonnet-5-5/whats-new-sonnet-5-5) descreve `between_tools` como o menor modo de raciocínio disponível nesse modelo. Outros identificadores de modelo não recebem parâmetros específicos do Sonnet 5.5.
- `max_requests` e `max_tokens` são configuráveis, com limites validados antes da criação do cliente. A interface existente mantém a mesma assinatura posicional e os mesmos limites de cinco requisições/1.000 tokens; o CLI de validação usa duas requisições/512 tokens por padrão.
- O agente registra motivo explícito de término e tipos dos blocos recebidos, sem salvar conteúdo de raciocínio. Não transforma thinking em resposta pública, nem tenta retomar truncamento com outra chamada paga.
- Chamadas de ferramentas em uma resposta truncada não são executadas. Apenas respostas com `stop_reason=tool_use` e blocos válidos entram no ciclo de ferramentas.
- O CLI registra configurações, motivo técnico e ausência explícita de texto. `--output` permite preservar a evidência anterior, e a criação exclusiva do arquivo evita sobrescrita concorrente. Um marcador local é criado antes da chamada para detectar problemas de escrita e impedir confusão com uma evidência antiga em caso de falha.
- Mensagens e blocos do assistente continuam sendo devolvidos integralmente durante o ciclo; não há mudança na arquitetura de ferramentas locais read-only.

## Validação local

`python -m pytest -q`: **24 passaram, 1 aviso, 2,33 s**, fora do sandbox do Windows para permitir o socket interno do TestClient. O aviso de depreciação httpx/TestClient permanece. Os testes do agente simulam o SDK e incluem exaustão por thinking, truncamento com tool_use parcial, limite econômico, configuração específica do modelo, geração de relatório e preservação da evidência existente.

## Tentativa econômica preparada após o diagnóstico (histórico)

Executar somente após aprovação de uma nova chamada paga, em PowerShell privado sem transcrição:

```powershell
.\.venv\Scripts\python.exe -m scripts.verify_claude_agent --prompt-key --output reports/claude_validation_simple.md
```

Pergunta padrão: “Use somente get_kpis uma vez. Informe apenas o total de pedidos, o número de entregues e o de cancelados, em uma frase. Não faça outras análises.”

Esperado: uma solicitação de ferramenta e uma resposta final, em duas requisições. O prompt orienta o uso de uma ferramenta; não é garantia de adesão do modelo. O teto é duas requisições de até 512 tokens de saída cada, sem retry. Tokens de entrada também são cobrados; não existe garantia de preço total nem de sucesso. Se o modelo pedir outra ferramenta na segunda rodada, o teste termina incompleto sem uma terceira requisição.

Esperado na resposta: 1.200 pedidos, 1.139 entregues e 61 cancelados. Na época deste diagnóstico, a correção ainda dependia de confirmação real. O comando acima documenta a preparação histórica; não é necessário repeti-lo para revisar a evidência.

## Desfecho auditado

Em 16/11/2026 às 21:24:19 UTC (18:24:19 em São Paulo), a execução feita pelo responsável passou: uma chamada `get_kpis({})`, duas requisições à API, resposta final com `end_turn`, 1.979 tokens de entrada e 76 de saída no total, sem tokens de raciocínio registrados. As três contagens do texto e todo o retorno da ferramenta coincidem com o Python. Isso confirma o smoke test simples após a correção; os fluxos complexos e a produção continuam fora do escopo comprovado. Veja a [evidência sanitizada](CLAUDE_VALIDATION.md).
