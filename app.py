"""Run: streamlit run app.py"""
from __future__ import annotations
import json
import os
import pandas as pd
import plotly.express as px
import streamlit as st
from foodflow.analytics import clean_orders, analyze_orders, report_md
from foodflow.agent import run_agent
from foodflow.data import generate_demo_orders

st.set_page_config(page_title="FoodFlow AI • Operations Copilot", page_icon="🍽️", layout="wide")
st.markdown("""<style>
.block-container {padding-top: 1.5rem; max-width: 1350px}
h1, h2, h3 {letter-spacing:-.03em}
div[data-testid="stMetric"] {padding:14px 18px; border:1px solid #5b2738; border-radius:12px; background:rgba(99,40,59,.08)}
</style>""", unsafe_allow_html=True)

st.title("🍽️ FoodFlow AI")
st.caption("Operations Copilot • dashboard + análise + agente com ferramentas + API de automação")
st.info("Projeto independente de portfólio. Dados demonstrativos sintéticos — NÃO é um produto oficial do iFood.")

with st.sidebar:
    st.header("Fonte de dados")
    uploaded = st.file_uploader("Carregue pedidos (.csv)", type="csv", help="Use o mesmo esquema do arquivo data/sample_orders.csv")
    st.markdown("**Assistente de IA (opcional)**")
    api_key = st.text_input("Anthropic API key", value=os.environ.get("ANTHROPIC_API_KEY", ""), type="password", help="Chave de API paga, independente da assinatura do Claude. Não armazenada pelo aplicativo.")
    model = st.text_input("Modelo", value=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5"))
    st.caption("Sem chave, as métricas, alertas e relatórios funcionam normalmente.")

try:
    raw = pd.read_csv(uploaded) if uploaded is not None else generate_demo_orders()
    df = clean_orders(raw)
except (ValueError, UnicodeDecodeError, pd.errors.ParserError) as exc:
    st.error(f"Dados inválidos: {exc}")
    st.stop()

regions = ["Todas"] + sorted(df["region"].unique().tolist())
selected_region = st.selectbox("Região", regions)
if selected_region != "Todas":
    df = df[df["region"] == selected_region].copy()
report = analyze_orders(df)
m = report["kpis"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Pedidos", f"{m['total_orders']:,}")
c2.metric("Cancelamentos", f"{m['cancellation_rate_pct']:.1f}%")
c3.metric("Entregas atrasadas", f"{m['late_rate_pct']:.1f}%")
c4.metric("Atraso médio positivo", f"{m['avg_positive_delay_minutes']:.1f} min")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Diagnóstico", "🚨 Plano de ação", "🤖 Agente IA", "📤 Exportação"])
with tab1:
    left, right = st.columns([1.3, 1])
    with left:
        st.subheader("Volume diário")
        trend = pd.DataFrame(report["daily"])
        fig = px.line(trend, x="date", y=["orders", "late_deliveries"], markers=True,
                      labels={"value": "Quantidade", "date": "Dia", "variable": "Indicador"})
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("Lojas por risco operacional")
        ranking = pd.DataFrame(report["ranking"])
        chart = px.bar(ranking.head(8), x="restaurant_id", y="risk_score",
                       labels={"restaurant_id": "Loja", "risk_score": "Score de risco (heurístico)"})
        st.plotly_chart(chart, use_container_width=True)
    st.dataframe(pd.DataFrame(report["ranking"]), hide_index=True, use_container_width=True)
    st.caption("Score = 65% × taxa de atrasos + 35% × taxa de cancelamentos. Não é um modelo preditivo.")
with tab2:
    st.subheader("Alertas com evidências")
    for alert in report["alerts"]:
        with st.container(border=True):
            st.markdown(f"**{alert['store']} · {alert['issue']}** — Prioridade: {alert['priority']}")
            st.write(alert["evidence"])
            st.markdown(f"**Hipótese de intervenção:** {alert['action']}")
    st.warning("As propostas não são executadas automaticamente; devem ser validadas pela operação.")
with tab3:
    st.subheader("Pergunte sobre os dados")
    st.caption("Agente Claude com quatro ferramentas locais, consultas somente leitura e rastreabilidade de chamadas.")
    question = st.text_area("Pergunta", "Quais lojas devo priorizar e por quê? Use números da base e proponha próximos passos.", height=110)
    if st.button("Analisar com Claude", type="primary"):
        if not api_key:
            st.warning("Insira uma Anthropic API key para habilitar o agente. Os demais recursos funcionam offline.")
        else:
            with st.spinner("Consultando ferramentas e gerando resposta..."):
                try:
                    result = run_agent(question, df, api_key, model)
                    st.markdown(result["answer"])
                    with st.expander("Ver chamadas de ferramentas"):
                        st.json(result["trace"])
                except Exception as exc:
                    st.error(f"Não foi possível executar a chamada à API: {type(exc).__name__}: {exc}")
    st.code("GET /demo-analysis\nPOST /analyze\nGET /health", language="http")
with tab4:
    st.subheader("Exportar resultados e conectar automações")
    st.download_button("⬇️ Relatório (.md)", report_md(report), "relatorio_foodflow.md", mime="text/markdown")
    st.download_button("⬇️ Análise (.json)", json.dumps(report, ensure_ascii=False, indent=2), "analise_foodflow.json", mime="application/json")
    st.download_button("⬇️ Pedidos demonstrativos (.csv)", df.drop(columns=["late", "delay_minutes", "date"]).to_csv(index=False), "pedidos_foodflow.csv", mime="text/csv")
    st.markdown("Automação local via `python -m foodflow.automation` e integração n8n/Make via FastAPI.")
    st.code("uvicorn foodflow.api:app --reload\n# Acesse http://127.0.0.1:8000/docs", language="bash")
