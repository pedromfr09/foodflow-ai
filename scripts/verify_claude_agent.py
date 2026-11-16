"""Execute one real Claude tool-use validation and save a local Markdown report.

Usage from repository root:
    python -m scripts.verify_claude_agent

The API key is read from ANTHROPIC_API_KEY or requested without echo.
No key is written to the report or GitHub.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import getpass
import json
import os
from pathlib import Path
import sys

from foodflow.agent import run_agent
from foodflow.analytics import clean_orders
from foodflow.data import generate_demo_orders

DEFAULT_QUESTION = (
    "Qual restaurante tem o maior risco operacional? Consulte os dados usando "
    "as ferramentas e justifique com números. Separe evidências e hipóteses."
)
DEFAULT_MODEL = "claude-sonnet-5-5"


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida um uso real das ferramentas do agente Claude.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Identificador de modelo disponível na sua conta.")
    parser.add_argument("--question", default=DEFAULT_QUESTION)
    args = parser.parse_args()
    api_key = os.environ.get("ANTHROPIC_API_KEY") or getpass.getpass("Cole sua Anthropic API key (oculta): ")
    if not api_key.strip():
        print("Chave ausente. Nenhuma chamada foi enviada.", file=sys.stderr)
        return 2

    df = clean_orders(generate_demo_orders())
    print("Executando consulta real ao Claude sobre dados sintéticos...")
    try:
        result = run_agent(args.question, df, api_key.strip(), model=args.model)
    except Exception as exc:
        # Avoid writing credentials or raw API error payloads in output/log files.
        print(
            f"Execução falhou ({type(exc).__name__}). "
            "Confira a chave, o saldo da API, o modelo e a conexão.",
            file=sys.stderr,
        )
        return 1

    trace = result.get("trace", [])
    answer = result.get("answer", "")
    complete = bool(trace) and bool(answer.strip()) and not answer.startswith("Limite de etapas")
    status = "PASSOU" if complete else "INCOMPLETO"
    report_path = Path("reports") / "claude_validation.md"
    report_path.parent.mkdir(exist_ok=True)
    def fenced(s: str) -> str:
        return s.replace("```", "`` `")

    lines = [
        "# FoodFlow AI — evidência de execução real do agente",
        "",
        f"- Data e hora (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"- Provedor: {result.get('provider', 'Anthropic Claude')}",
        f"- Modelo solicitado: `{args.model}`",
        f"- Base: {len(df)} pedidos **sintéticos**, não oficiais do iFood",
        f"- Chamadas de ferramentas registradas: {len(trace)}",
        f"- Resultado do smoke test: **{status}**",
        "- Observação: não houve implantação em produção ou medição de ganho operacional",
        "",
        "## Pergunta enviada",
        "",
        args.question,
        "",
        "## Resposta retornada",
        "",
        answer,
        "",
        "## Rastreabilidade das chamadas locais",
        "",
        "```json",
        fenced(json.dumps(trace, ensure_ascii=False, indent=2)),
        "```",
        "",
        "## Critério do smoke test",
        "",
        "A execução é considerada concluída se a API respondeu, houve ao menos uma "
        "chamada de ferramenta e o agente retornou uma resposta textual não truncada "
        "pelo limite de etapas. Isso não valida a precisão factual nem o comportamento "
        "em produção; confira os valores com os dados do projeto.",
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"{status}: {len(trace)} chamada(s) de ferramenta. Relatório salvo em {report_path}")
    if not complete:
        print("Revise a resposta e o trace: o teste não atingiu todos os critérios.")
        return 1
    print("Confira o relatório antes de compartilhar ou publicá-lo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
