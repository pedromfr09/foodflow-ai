# Case Study — FoodFlow AI

## Situação (simulada)
Uma área de operações de delivery recebe planilhas com pedidos, mas carece de um resumo que priorize problemas de atrasos e cancelamentos. O objetivo é encurtar o caminho entre dados brutos e hipóteses de intervenção.

## Meta do MVP
- Analisar um CSV em interface sem treinamento prévio.
- Exibir quatro KPIs e um ranking operacional.
- Apresentar recomendações rastreáveis baseadas em indicadores.
- Permitir consultas por linguagem natural usando ferramentas read-only (API opcional).
- Disponibilizar JSON por API para conectar automações.

## Escolhas de produto
- **CSV + dados sintéticos:** permite demo reproduzível sem dados sensíveis.
- **Streamlit:** entrega de interface rápida por Python.
- **Pandas:** cálculo transparente de métricas.
- **FastAPI:** contrato JSON testável e documentação em `/docs`.
- **Claude Tool Use:** modelo escolhe funções para verificar métricas, reduzindo risco de números inventados.
- **Rules first:** indicadores e alertas verificáveis existem mesmo sem LLM.

## Validação e demonstração
- Dez testes automatizados cobrindo métricas/erros/API.
- CSV sintético com problemas operacionais introduzidos de propósito.
- Relatório exportável Markdown/JSON com limitações declaradas.
- A integração real ao Claude demanda chave Anthropic, não disponível para teste na criação inicial.
- n8n é disponibilizado como exemplo de fluxo, ainda sem prova de execução em ambiente externo.

## Riscos e mitigação
| Risco | Mitigação |
|---|---|
| LLM inventa fatos | Funções com dados e instruções de citar evidências |
| Confundir score com ML preditivo | Score definido explicitamente como heurística |
| Vazamento de dados | Synthetic-first, agente read-only, chave em campo password |
| Recomendações ruins | Não execução automática, exige validação humana |
| Falsa prova de impacto | Sem ROI ou horas economizadas fictícias |

## Critérios para afirmar impacto real no futuro
1. Implantar com dados aprovados pela organização.
2. Medir tempo manual de análise e tempo com ferramenta, no mesmo volume.
3. Contabilizar custo de API e revisão humana.
4. Testar se alertas antecipam problemas relevantes sem falsos positivos excessivos.

## Uma frase para o currículo
**FoodFlow AI (projeto autoral demonstrativo):** desenvolvimento de dashboard de indicadores operacionais, API FastAPI, rotina automatizada de relatórios e agente Claude com consulta a ferramentas Python; análise com dados sintéticos e testes automatizados.
