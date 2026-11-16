# Case Study — FoodFlow AI

## Contexto e problema
Cenário simulado: uma equipe de operações de delivery recebe planilhas de pedidos e precisa identificar atrasos, cancelamentos e restaurantes que merecem investigação. O desafio é transformar dados brutos em indicadores e hipóteses de ação de maneira rastreável.

**Escopo:** demonstração independente, com dados 100% sintéticos. Não é produto oficial do iFood e não foi implantado em operações reais.

## Solução proposta
- Validar e analisar CSVs de pedidos com Python e Pandas.
- Calcular KPIs operacionais e priorizar restaurantes com uma heurística explícita.
- Explorar indicadores em um dashboard Streamlit.
- Expor análises em JSON por FastAPI.
- Gerar relatórios Markdown/JSON por rotina executável.
- Permitir consultas em linguagem natural com Claude e quatro ferramentas Python somente de leitura, quando houver chave de API válida.
- Disponibilizar um template de fluxo n8n para orquestração com a API.

## Decisões de arquitetura
| Escolha | Motivo |
|---|---|
| Dados sintéticos | Demonstração reproduzível sem dados de clientes |
| KPIs calculados em Python | Métricas verificáveis, independentes de respostas de LLM |
| Streamlit | Iteração rápida de interface |
| FastAPI | Contrato HTTP/JSON documentado |
| Claude com tool use (opcional) | Consultas guiadas por funções em vez de números gerados livremente |
| Ferramentas read-only | Nenhuma intervenção automática em pedidos ou restaurantes |

## Evidências e limites de validação
- Testes automatizados para métricas, validação de dados e endpoints estão disponíveis em `tests/`. Execute `python -m pytest -q` para reproduzir os resultados no seu ambiente.
- A versão `index.html` é uma demonstração interativa estática, com processamento no navegador; não executa o backend Python.
- A integração com a API externa do Claude **não estava validada com credenciais reais** na preparação inicial do MVP.
- O workflow n8n é um **template**, não uma automação comprovadamente implantada.
- Nenhum ganho de produtividade, ROI ou economia de horas em produção foi medido.

## Riscos e próximos passos
1. Usar dados operacionais somente com autorização e governança apropriadas.
2. Adicionar autenticação e limites de requisições antes de expor a API na internet.
3. Validar qualidade dos alertas com usuários e dados reais autorizados.
4. Executar testes end-to-end do agente e do fluxo n8n.
5. Medir tempo de análise, custo por execução e taxa de acerto dos alertas em um piloto controlado.
