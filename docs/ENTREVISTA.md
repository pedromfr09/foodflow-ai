# Roteiro de demonstração e estudo para a entrevista

## Pitch de 35 segundos
"Tenho uma base forte em física, engenharia e modelagem aplicada. No meu projeto de pesquisa, já uso IA como ferramenta para acelerar simulações CFD com OpenFOAM. Resolvi demonstrar a aplicação dessa mentalidade a um problema de negócio e construí o FoodFlow AI: uma ferramenta que recebe dados de pedidos, calcula métricas de atraso e cancelamento, identifica operações prioritárias, gera relatórios e expõe uma API. A interface funciona com dados sintéticos sem depender de LLM. Opcionalmente, o Claude consulta funções reais em Python para responder perguntas com rastreabilidade."

## Demonstração de 60 a 90 segundos
1. Mostre a base sintética e informe que é simulação, não dados do iFood.
2. Explique taxa de atraso = entregas atrasadas / entregas totais.
3. Mostre loja problemática, a hipótese de ação e que nenhuma ação foi executada automaticamente.
4. Exporte relatório; abra `http://127.0.0.1:8000/docs`.
5. Se tiver chave configurada e testada, pergunte ao Claude quais lojas são prioritárias e abra o trace.

## Perguntas prováveis
**Como evita alucinações?** O modelo recebe regras para consultar ferramentas; os cálculos são feitos em Python, com base em dados, e a UI mostra chamadas. Não elimina totalmente erros de interpretação.

**O que o agente faz?** Escolhe consultas read-only via tool use e compõe resposta. Não cria pedidos nem aciona restaurante.

**Por que não utilizar um prompt único?** Porque o usuário precisa de métricas rastreáveis. Computar regras fora do LLM permite testes e repetir resultados.

**O que é o score?** Heurística 65% atrasos + 35% cancelamentos. Não é um modelo de machine learning; os pesos não foram otimizados com dados de produção.

**Como mensura impacto?** Ainda não houve implantação real. Em produção, faria experimento comparando horas de análise e qualidade do diagnóstico, descontando revisão e custo de API.

**O que é REST/API?** Um serviço HTTP com contratos de requisição/resposta JSON. Neste projeto, endpoints GET expõem resultados demo e POST recebe um lote de pedidos.

**O que faria se recebesse uma planilha quebrada?** Validaria colunas, tipos, duplicatas, status e limites, retornando erro 422 pela API quando necessário.

**O que é n8n?** Ferramenta de automação de workflows, com nós de gatilho, HTTP e transformação de dados. O repositório possui um modelo de fluxo; não afirmar que está em produção sem rodar.

**Como criou o código?** Com auxílio de IA e testes locais. Você definiu propósito/escopo e precisa conseguir explicar as interfaces e verificar resultados antes da entrevista. Não confundir código assistido por IA com desenvolvimento de modelos de IA do zero.

## Perguntas que você deve fazer ao recrutador
- Quais problemas de negócio AI Builders resolvem nos primeiros 90 dias?
- Como avaliam impacto: adoção, tempo poupado, conversão, produtividade?
- Que ferramentas e integrações são utilizadas pelo time?

## Estudo mínimo antes da entrevista
- Pandas: `groupby`, `mean`, `sum`, DataFrame, diferença entre contagem e taxa.
- Streamlit: `st.metric`, `st.plotly_chart`, `st.file_uploader`.
- FastAPI: rotas GET/POST, JSON, `/docs`, validação HTTP 422.
- LLM: prompt de sistema, ferramentas, tool use, loop e alucinação.
- n8n: gatilhos, requisições HTTP, input/output, credenciais.
