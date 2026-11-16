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


def run_agent(question: str, df: pd.DataFrame, api_key: str, model: str = "claude-sonnet-5-5",
              *, max_requests: int = 5, max_tokens: int = 1000) -> dict[str, Any]:
    """Bounded requests, read-only tools; never retry or resume truncation automatically."""
    if not api_key or not api_key.strip():
        raise ValueError("Configure uma chave de API Anthropic para conversar com o agente.")
    if not question.strip() or len(question) > 2000:
        raise ValueError("Pergunta obrigatória, com no máximo 2.000 caracteres.")
    if not 2 <= max_requests <= 5 or not 128 <= max_tokens <= 4096:
        raise ValueError("Use 2 a 5 requisições e 128 a 4096 tokens por requisição.")
    try:
        import anthropic
    except ImportError as exc:
        raise RuntimeError("Instale a dependência 'anthropic' antes de ativar o agente.") from exc
    client = anthropic.Anthropic(api_key=api_key, timeout=30.0, max_retries=0)
    messages: list[dict[str, Any]] = [{"role": "user", "content": question}]
    trace: list[dict[str, Any]] = []
    requests: list[dict[str, Any]] = []
    # Sonnet 5.5 defaults to adaptive/high, which can consume the entire output
    # budget before producing text. This setting is model-specific, not disabled.
    options = ({"thinking": {"type": "between_tools"},
                "output_config": {"effort": "low"}}
               if model == "claude-sonnet-5-5" else {})
    settings = {"max_requests": max_requests, "max_tokens": max_tokens, **options}

    def finish(text: str, reason: str) -> dict[str, Any]:
        return {"answer": text, "trace": trace, "requests": requests,
                "complete": reason == "completed", "completion_reason": reason,
                "settings": settings, "provider": "Anthropic Claude"}

    for step in range(max_requests):
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            tool_choice={"type": "auto"},
            messages=messages,
            **options,
        )
        requests.append({
            "step": step + 1, "message_id": response.id, "model": response.model,
            "stop_reason": response.stop_reason,
            "usage": response.usage.model_dump(exclude_none=True),
            "content_block_types": [block.type for block in response.content],
        })
        tool_calls = [block for block in response.content if block.type == "tool_use"]
        if response.stop_reason != "tool_use" or not tool_calls:
            text = "\n".join(block.text for block in response.content if block.type == "text")
            if response.stop_reason != "end_turn":
                reason = ("missing_tool_use_blocks" if response.stop_reason == "tool_use"
                          else response.stop_reason or "unknown_stop_reason")
            elif tool_calls:
                reason = "unexpected_tool_use_blocks"
            elif not text.strip():
                reason = "empty_answer"
            elif not trace:
                reason = "no_tools_executed"
            elif not all(item["success"] for item in trace):
                reason = "tool_error"
            else:
                reason = "completed"
            return finish(text, reason)
        messages.append({"role": "assistant", "content": [block.model_dump(exclude_none=True) for block in response.content]})
        tool_results = []
        for block in tool_calls:
            try:
                result = call_tool(block.name, block.input or {}, df)
            except (TypeError, ValueError) as exc:
                result = {"error": str(exc)}
            failed = isinstance(result, dict) and "error" in result
            trace.append({"step": step + 1, "tool_use_id": block.id,
                          "tool": block.name, "input": block.input,
                          "success": not failed, "result": result})
            tool_results.append({"type": "tool_result", "tool_use_id": block.id,
                                 "is_error": failed, "content": json.dumps(result, ensure_ascii=False)})
        messages.append({"role": "user", "content": tool_results})
    return finish("Limite de etapas do agente alcançado. Reformule com uma pergunta mais específica.",
                  "request_limit")
