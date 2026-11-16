"""Reproducible business metrics and transparent, rules-based operational insights."""
from __future__ import annotations
import json
import math
from typing import Any
import pandas as pd

REQUIRED_COLUMNS = [
    "order_id", "restaurant_id", "region", "created_at", "promised_minutes",
    "actual_minutes", "order_value_brl", "status",
]


def clean_orders(data: pd.DataFrame) -> pd.DataFrame:
    missing = set(REQUIRED_COLUMNS) - set(data.columns)
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(sorted(missing))}")
    df = data[REQUIRED_COLUMNS].copy()
    if df.empty:
        raise ValueError("O arquivo de pedidos está vazio.")
    if len(df) > 15000:
        raise ValueError("Demonstração limitada a 15.000 pedidos por análise.")
    df["order_id"] = df["order_id"].astype(str).str.strip()
    df["restaurant_id"] = df["restaurant_id"].astype(str).str.strip()
    df["region"] = df["region"].astype(str).str.strip()
    df["status"] = df["status"].astype(str).str.lower().str.strip()
    if df["order_id"].eq("").any() or df["order_id"].duplicated().any():
        raise ValueError("order_id deve ser único e não vazio.")
    if df["restaurant_id"].eq("").any():
        raise ValueError("restaurant_id não pode ser vazio.")
    if not df["status"].isin(["delivered", "cancelled"]).all():
        raise ValueError("status aceita apenas 'delivered' ou 'cancelled'.")
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    if df["created_at"].isna().any():
        raise ValueError("created_at contém datas inválidas.")
    # Convert to ordinary naive local datetimes; incoming timezone-aware values are not supported.
    if df["created_at"].dt.tz is not None:
        raise ValueError("Datas devem ser informadas sem fuso horário (horário local).")
    for col in ["promised_minutes", "actual_minutes", "order_value_brl"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if df["promised_minutes"].isna().any() or (df["promised_minutes"] <= 0).any():
        raise ValueError("promised_minutes precisa ser um número positivo.")
    if df["order_value_brl"].isna().any() or (df["order_value_brl"] < 0).any():
        raise ValueError("order_value_brl precisa ser não negativo.")
    delivered = df["status"].eq("delivered")
    if df.loc[delivered, "actual_minutes"].isna().any() or (df.loc[delivered, "actual_minutes"] <= 0).any():
        raise ValueError("Pedidos entregues exigem actual_minutes positivo.")
    df["late"] = delivered & (df["actual_minutes"] > df["promised_minutes"])
    df["delay_minutes"] = (df["actual_minutes"] - df["promised_minutes"]).clip(lower=0).where(delivered, 0).fillna(0)
    df["date"] = df["created_at"].dt.strftime("%Y-%m-%d")
    return df


def kpis(df: pd.DataFrame) -> dict[str, Any]:
    delivered = df[df["status"] == "delivered"]
    total = len(df)
    n_delivered = len(delivered)
    return {
        "total_orders": total,
        "delivered_orders": n_delivered,
        "cancelled_orders": total - n_delivered,
        "cancellation_rate_pct": round(100 * (total - n_delivered) / total, 2),
        "late_rate_pct": round(100 * int(delivered["late"].sum()) / n_delivered, 2) if n_delivered else 0.0,
        "avg_positive_delay_minutes": round(float(delivered["delay_minutes"].mean()), 2) if n_delivered else 0.0,
        "delivered_gmv_brl": round(float(delivered["order_value_brl"].sum()), 2),
        "store_count": int(df["restaurant_id"].nunique()),
        "start_date": str(df["date"].min()),
        "end_date": str(df["date"].max()),
    }


def restaurant_ranking(df: pd.DataFrame, limit: int = 10) -> list[dict[str, Any]]:
    out = []
    for store, subset in df.groupby("restaurant_id"):
        m = kpis(subset)
        # Risk is a simple transparent prioritization heuristic; not a predictive ML model.
        score = round(0.65 * m["late_rate_pct"] + 0.35 * m["cancellation_rate_pct"], 1)
        out.append({
            "restaurant_id": str(store), "orders": m["total_orders"],
            "late_rate_pct": m["late_rate_pct"],
            "cancellation_rate_pct": m["cancellation_rate_pct"],
            "avg_positive_delay_minutes": m["avg_positive_delay_minutes"],
            "risk_score": score,
        })
    return sorted(out, key=lambda v: (-v["risk_score"], -v["orders"]))[:max(1, min(limit, 50))]


def get_store_details(df: pd.DataFrame, restaurant_id: str) -> dict[str, Any]:
    if restaurant_id not in set(df["restaurant_id"]):
        return {"error": "Restaurante não encontrado na base.", "restaurant_id": restaurant_id}
    subset = df[df["restaurant_id"] == restaurant_id]
    daily = subset.groupby("date").agg(orders=("order_id", "count"), delayed=("late", "sum"))
    return {
        "restaurant_id": restaurant_id,
        "kpis": kpis(subset),
        "daily_orders": [{"date": str(idx), "orders": int(row["orders"]), "late_orders": int(row["delayed"])} for idx, row in daily.iterrows()],
    }


def recommended_actions(df: pd.DataFrame) -> list[dict[str, str]]:
    ranking = restaurant_ranking(df)
    results: list[dict[str, str]] = []
    for store in ranking[:5]:
        if store["orders"] < 20:
            continue
        if store["late_rate_pct"] >= 40:
            results.append({
                "priority": "Alta", "store": store["restaurant_id"], "issue": "Atrasos frequentes",
                "evidence": f"{store['late_rate_pct']:.1f}% dos pedidos entregues acima do prazo ({store['orders']} pedidos totais).",
                "action": "Investigar capacidade na hora de pico e revisar tempo de preparo/promessa; validar em piloto antes de alterar SLA.",
            })
        if store["cancellation_rate_pct"] >= 10:
            results.append({
                "priority": "Alta", "store": store["restaurant_id"], "issue": "Cancelamentos elevados",
                "evidence": f"{store['cancellation_rate_pct']:.1f}% dos pedidos cancelados ({store['orders']} pedidos totais).",
                "action": "Auditar motivos de cancelamento, estoque e confirmação de pedidos; criar alerta preventivo.",
            })
    if not results:
        results.append({
            "priority": "Monitoramento", "store": "Todas", "issue": "Sem alerta nos limiares definidos",
            "evidence": "Nenhuma loja com mais de 20 pedidos ultrapassou os limites de alerta.",
            "action": "Monitorar indicadores diariamente e revisar limiares com a operação.",
        })
    return results


def analyze_orders(data: pd.DataFrame) -> dict[str, Any]:
    df = clean_orders(data)
    daily = df.groupby("date").agg(total=("order_id", "count"), late=("late", "sum"))
    return {
        "metadata": {"dataset": "CSV fornecido ou demonstração sintética", "currency": "BRL", "method": "regras explícitas; não é previsão causal"},
        "kpis": kpis(df),
        "ranking": restaurant_ranking(df),
        "alerts": recommended_actions(df),
        "daily": [{"date": str(day), "orders": int(row["total"]), "late_deliveries": int(row["late"])} for day, row in daily.iterrows()],
    }


def report_md(report: dict[str, Any]) -> str:
    m = report["kpis"]
    lines = [
        "# FoodFlow AI | Relatório operacional", "",
        "**Demonstração com dados sintéticos ou CSV disponibilizado pelo usuário. Não é um sistema oficial do iFood.**", "",
        f"Período: {m['start_date']} a {m['end_date']}", "",
        "## Indicadores", "",
        f"- Pedidos: {m['total_orders']}",
        f"- Taxa de cancelamento: {m['cancellation_rate_pct']}%",
        f"- Taxa de atraso sobre entregas: {m['late_rate_pct']}%",
        f"- Atraso positivo médio entre entregas: {m['avg_positive_delay_minutes']} min",
        f"- Valor bruto de pedidos entregues: R$ {m['delivered_gmv_brl']:,.2f}", "",
        "## Ações propostas (não executadas)", "",
    ]
    for a in report["alerts"]:
        lines += [f"### {a['store']} — {a['issue']}", f"- Evidência: {a['evidence']}", f"- Proposta: {a['action']}", ""]
    lines += ["## Limitações", "", "- Dados de demonstração não refletem a operação real do iFood.", "- As regras de alerta são heurísticas e precisam ser calibradas e validadas.", "- Nenhuma recomendação é executada automaticamente."]
    return "\n".join(lines) + "\n"
