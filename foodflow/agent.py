"""Optional Anthropic Claude tool-using agent; requires a separate paid API key."""
from __future__ import annotations
import json
from typing import Any
import pandas as pd
from .analytics import kpis, restaurant_ranking, recommended_actions, get_store_details

SYSTEM_PROMPT = """Você é um analista de operações de delivery e usa ferramentas para verificar dados.
Os dados são demonstrativos ou fornecidos pelo usuário; nunca diga que são dados oficiais do iFood.
Antes de responder com números, use ferramentas. Compare métricas com seus denominadores.
Não invente causas, ROI, ganhos, eventos, ações executadas ou efeitos de recomendações.
Separe observações, hipóteses e próximos passos. Não execute ações externas; só consulte.
Se a pergunta pedir algo fora da base, diga que os dados não sustentam a conclusão.
Responda de forma objetiva em português do Brasil."""

TOOL_SCHEMAS = [
    {"name": "get_kpis", "description": "Consultar KPIs consolidados na amostra atual.", "input_schema": {"type": "object", "properties": {}}},
    {"name": "rank_restaurants", "description": "Ordenar lojas por risco operacional (heurística transparente).", "input_schema": {"type": "object", "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 20}}}},
    {"name": "get_restaurant_details", "description": "Consultar indicadores e série temporal de uma loja.", "input_schema": {"type": "object", "properties": {"restaurant_id": {"type": "string"}}, "required": ["restaurant_id"]}},
    {"name": "get_recommended_actions", "description": "Consultar alertas e propostas baseadas em regras explícitas.", "input_schema": {"type": "object", "properties": {}}},
]


def call_tool(name: str, args: dict[str, Any], df: pd.DataFrame) -> Any:
    if name == "get_kpis":
        return kpis(df)
    if name == "rank_restaurants":
        return restaurant_ranking(df, limit=max(1, min(int(args.get("limit", 10)), 20)))
    if name == "get_restaurant_details":
        return get_store_details(df, str(args.get("restaurant_id", "")))
    if name == "get_recommended_actions":
        return recommended_actions(df)
    return {"error": "Ferramenta não autorizada."}


def run_agent(question: str, df: pd.DataFrame, api_key: str, model: str = "claude-sonnet-5-5") -> dict[str, Any]:
    """Four-step bounded tool loop, read-only; no external side effects or persistent conversations."""
    if not api_key or not api_key.strip():
        raise ValueError("Configure uma chave de API Anthropic para conversar com o agente.")
    if not question.strip() or len(question) > 2000:
        raise ValueError("Pergunta obrigatória, com no máximo 2.000 caracteres.")
    try:
        import anthropic
    except ImportError as exc:
        raise RuntimeError("Instale a dependência 'anthropic' antes de ativar o agente.") from exc
    client = anthropic.Anthropic(api_key=api_key, timeout=30.0, max_retries=1)
    messages: list[dict[str, Any]] = [{"role": "user", "content": question}]
    trace: list[dict[str, Any]] = []
    for step in range(5):
        response = client.messages.create(
            model=model,
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            tool_choice={"type": "any"} if step == 0 else {"type": "auto"},
            messages=messages,
        )
        tool_calls = [block for block in response.content if block.type == "tool_use"]
        if not tool_calls:
            text = "\n".join(block.text for block in response.content if block.type == "text")
            return {"answer": text or "Nenhuma resposta textual foi retornada.", "trace": trace, "provider": "Anthropic Claude"}
        messages.append({"role": "assistant", "content": [block.model_dump(exclude_none=True) for block in response.content]})
        tool_results = []
        for block in tool_calls:
            try:
                result = call_tool(block.name, block.input or {}, df)
            except (TypeError, ValueError) as exc:
                result = {"error": str(exc)}
            trace.append({"step": step + 1, "tool": block.name, "input": block.input})
            tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(result, ensure_ascii=False)})
        messages.append({"role": "user", "content": tool_results})
    return {"answer": "Limite de etapas do agente alcançado. Reformule com uma pergunta mais específica.", "trace": trace, "provider": "Anthropic Claude"}
