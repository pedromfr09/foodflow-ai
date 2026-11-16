# Checklist de portfólio para AI Builder — iFood

## Ordem recomendada no GitHub

1. **FoodFlow AI** — projeto principal AI Builder: análise operacional, dashboard, API, automação, agente opcional.
2. **Automação do Ciclo de Rankine** — problema físico de engenharia resolvido por software; destacar inputs, outputs, gráficos e reprodutibilidade.
3. **CFD + IA aplicada à pesquisa** — um case de processo de trabalho com Claude/OpenFOAM, somente com imagens e dados que o laboratório autorizar divulgar.

## O que fazer hoje, sem inventar validação

- Fazer fork/copy deste projeto para um repositório novo `foodflow-ai` de sua conta.
- Abrir `index.html` e testar filtro por região e exportação JSON.
- Iniciar a aplicação Streamlit local e capturar tela do dashboard se conseguir instalar dependências.
- Rodar `python -m pytest -q` e anexar screenshot dos testes.
- Se tiver chave API Anthropic, rodar uma pergunta do agente e registrar trace. Se não tiver, explicitar no README que o agente é opcional e ainda não foi validado contra serviço externo.
- Publicar `index.html` pelo GitHub Pages (Settings → Pages → Deploy from a branch → main → root). Após publicação, inserir URL de demo no topo do README.
- Gravar demonstração de até 90 segundos; pode ser vídeo não listado, com link no README.

## Texto a colocar na descrição do repositório

"Operational intelligence copilot for delivery: interactive KPI dashboard, Python analytics, FastAPI endpoints, report automation and optional Claude tool-use agent. Synthetic data; independent portfolio project."

## Melhorias rápidas no README do projeto Rankine (sem acessar seu repositório)

- Uma imagem do gráfico de saída e uma frase do objetivo do modelo.
- Exemplo real e reproduzível de `input` e `output` do código.
- Explicação breve das hipóteses termodinâmicas adotadas e limitações.
- Instruções para executar em no máximo três comandos.
- Lista das variáveis ajustáveis e resultados calculados.
- Nota indicando quais etapas foram assistidas por IA, se aplicável.

## Case CFD + IA (não divulgar código/dados proprietários)

**Problema:** acelerar a preparação e execução de simulações CFD de um protótipo de microssensor de fluidos.

**Workflow declarado pelo pesquisador:** definição de geometria e contorno → Claude auxilia a escrever/adaptar arquivos de OpenFOAM → usuário executa e depura casos → usuário interpreta resultados (comparação com resultados ANSYS quando aplicável).

**Provas visuais sugeridas:** geometria CAD, malha, imagem de campo de velocidade, árvore de arquivos OpenFOAM, instrução/prompt utilizado sem contexto sensível.

**Métricas futuras:** tempo para configuração sem/ com assistente, taxa de casos estáveis e desvio entre grandezas previstas/medidas. Não publicar percentuais sem aferição.

## Redação segura para o currículo

"Uso de Claude integrado ao ambiente local para apoiar elaboração de scripts e configuração de casos CFD em OpenFOAM; execução e análise de simulações para desenvolvimento tecnológico de microssensores."

Evite "engenharia de agentes em produção", "desenvolvedor backend experiente", "sistema implantado no iFood", "economizou 80% do tempo" ou "validação industrial" sem evidências.
