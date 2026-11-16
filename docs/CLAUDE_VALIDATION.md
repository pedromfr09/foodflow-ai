# FoodFlow AI — validação real do agente Claude

**Resultado: PASSOU no smoke test simples, executado localmente com dados 100% sintéticos.** Não houve implantação em produção ou medição de ganho operacional. Esta versão sanitizada foi preparada a partir do relatório privado e de uma auditoria determinística offline.

## Execução auditada

| Item | Evidência |
|---|---|
| Data | 16/11/2026, 21:24:19 UTC (18:24:19 em São Paulo) |
| Provedor / modelo retornado | Anthropic / `claude-sonnet-5-5` nas duas respostas |
| Base | `generate_demo_orders()`, seed 42, 1.200 pedidos sintéticos |
| Ferramenta executada | `get_kpis` |
| Argumentos | `{}` |
| Resultado da ferramenta | `success=true`; retorno integral idêntico à reprodução em Python |
| Requisições à API / execuções de ferramenta | 2 / 1 |
| Motivos de parada | `tool_use` na primeira; `end_turn` na segunda |
| Blocos recebidos | `tool_use` na primeira; `text` na segunda |
| Resultado técnico | `completed`; texto final presente, sem truncamento |
| Limites configurados | 2 requisições; 512 tokens de saída por requisição; sem retry |
| Modo de raciocínio | `between_tools`, esforço `low` |
| Tokens totais registrados | 1.979 de entrada; 76 de saída (28 + 48); zero tokens de raciocínio |

Tokens de entrada foram somados entre requisições, incluindo contexto repetido. Esses totais não são uma auditoria da cobrança.

Pergunta enviada:

> Use somente get_kpis uma vez. Informe apenas o total de pedidos, o número de entregues e o de cancelados, em uma frase. Não faça outras análises.

Resposta final do Claude:

> Na amostra consultada, foram 1.200 pedidos no total, dos quais 1.139 foram entregues e 61 cancelados.

## Conferência de todos os valores

A auditoria reproduziu `kpis(clean_orders(generate_demo_orders()))` e confirmou igualdade de todos os campos com o resultado registrado. As três contagens do texto final conferem e satisfazem `1.139 + 61 = 1.200`.

| Campo da ferramenta | Resultado registrado e reproduzido | Presente no texto final |
|---|---:|---|
| `total_orders` | 1.200 | Sim |
| `delivered_orders` | 1.139 | Sim |
| `cancelled_orders` | 61 | Sim |
| `cancellation_rate_pct` | 5,08% | Não |
| `late_rate_pct` | 46,53% | Não |
| `avg_positive_delay_minutes` | 4,73 min | Não |
| `delivered_gmv_brl` | R$ 88.342,18 | Não |
| `store_count` | 10 | Não |
| `start_date` | 2026-10-01 | Não |
| `end_date` | 2026-10-15 | Não |

Cancelamento usa todos os pedidos; atraso usa apenas entregues. GMV é a soma dos valores dos pedidos entregues, sem devoluções, descontos ou taxas. O período descreve o dataset sintético, não a data de execução.

Reprodução offline dos cálculos, sem chave ou chamada Anthropic:

```powershell
python -c "from foodflow.data import generate_demo_orders; from foodflow.analytics import clean_orders, kpis; print(kpis(clean_orders(generate_demo_orders())))"
python -m pytest -q
```

## Alcance da evidência

| Camada | Comprovado | Limites |
|---|---|---|
| Testes locais | 24 testes passaram; métricas, dados, endpoints locais e agente simulado | Não usam a API Anthropic |
| API real, teste simples | Autenticação/acesso funcionaram naquela execução; solicitação de ferramenta, execução Python, devolução ao modelo e resposta final correta | Uma pergunta, uma amostra e um modelo; não prova robustez geral |
| API real, execução anterior | `rank_restaurants(limit=5)`, `get_kpis({})` e `get_restaurant_details(restaurant_id=LOJA-03)` retornaram resultados iguais ao Python | O ciclo terminou sem resposta final, por tokens; consultas complexas não foram validadas de ponta a ponta |
| Outras funções | `get_recommended_actions` está implementada | Não houve chamada real registrada dessa ferramenta nos relatórios auditados |
| Produção e impacto | Nenhuma evidência de implantação ou operação real | Sem SLA, carga, dados operacionais reais, ROI ou economia de horas medidos |

A suíte foi repetida na versão consolidada sobre o clone do GitHub: **24 passaram, 1 aviso, 2,84 s**. O código importado veio do clone; as dependências foram reutilizadas do ambiente virtual local, sem copiá-lo para o repositório. O aviso é `StarletteDeprecationWarning` sobre o uso de httpx pelo TestClient; não houve falha de teste. A migração dessa dependência permanece pendente.

A execução completa do agente pela interface Streamlit, outros modelos, perguntas adversariais e integração n8n não foram comprovados por este smoke test. A demonstração GitHub Pages é estática e não executa o agente Python.

## Histórico de debugging

A execução anterior de 16/11/2026 às 21:15:28 UTC foi **INCOMPLETO**: três ferramentas corretas, mas a terceira requisição consumiu os 1.000 tokens de saída em raciocínio (`thinking_tokens=1000`, `stop_reason=max_tokens`), sem texto final. O limite de cinco rodadas não foi atingido.

O agente foi ajustado para o modo `between_tools` com esforço `low` especificamente no Sonnet 5.5, passou a diagnosticar o término e manteve a recusa de truncamentos. O teste simples posterior confirmou o ciclo completo com essa configuração. A [investigação técnica](CLAUDE_INVESTIGATION.md) preserva o diagnóstico e os testes de regressão.

## Privacidade e revisão

Os relatórios originais permanecem locais em `reports/`, ignorados pelo Git. Esta evidência omite credenciais, identificadores de requisição/ferramenta, dados de conta e payloads brutos de erro. Não contém dados de clientes ou do iFood. A documentação resume uma execução observada; não é uma certificação independente do provedor. Nenhuma nova chamada paga foi realizada para esta auditoria.
