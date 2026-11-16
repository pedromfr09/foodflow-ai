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
import warnings

from foodflow.agent import run_agent
from foodflow.analytics import clean_orders
from foodflow.data import generate_demo_orders

DEFAULT_QUESTION = (
    "Use somente get_kpis uma vez. Informe apenas o total de pedidos, o número "
    "de entregues e o de cancelados, em uma frase. Não faça outras análises."
)
DEFAULT_MODEL = "claude-sonnet-5-5"


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida um uso real das ferramentas do agente Claude.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Identificador de modelo disponível na sua conta.")
    parser.add_argument("--question", default=DEFAULT_QUESTION)
    parser.add_argument("--max-requests", type=int, choices=range(2, 6), default=2)
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--output", type=Path, default=Path("reports/claude_validation.md"),
                        help="Novo relatório local; nunca sobrescreve evidências existentes.")
    parser.add_argument("--prompt-key", action="store_true",
                        help="Ignora a variável de ambiente e exige entrada oculta no terminal privado.")
    args = parser.parse_args()
    if not args.question.strip() or len(args.question) > 2000:
        parser.error("Pergunta obrigatória, com no máximo 2.000 caracteres.")
    if not 128 <= args.max_tokens <= 4096:
        parser.error("--max-tokens deve estar entre 128 e 4096.")
    report_path = args.output
    if report_path.exists():
        print("Relatório já existe. Revise e arquive-o antes de autorizar outra execução paga.", file=sys.stderr)
        return 2
    api_key = None if args.prompt_key else os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        if not sys.stdin.isatty():
            print("É necessário um terminal privado interativo para entrada oculta. Nenhuma chamada enviada.", file=sys.stderr)
            return 2
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", getpass.GetPassWarning)
                api_key = getpass.getpass("Cole sua Anthropic API key (oculta): ")
        except (getpass.GetPassWarning, EOFError, KeyboardInterrupt):
            print("Entrada oculta indisponível ou cancelada. Nenhuma chamada enviada.", file=sys.stderr)
            return 2
    if not api_key.strip():
        print("Chave ausente. Nenhuma chamada foi enviada.", file=sys.stderr)
        return 2

    df = clean_orders(generate_demo_orders())
    report_path.parent.mkdir(parents=True, exist_ok=True)
    # Reserve the output before spending money; exclusive creation prevents races.
    # On failure this marker remains, so a previous PASS cannot be mistaken for this run.
    with report_path.open("x", encoding="utf-8") as pending:
        pending.write("# Validação iniciada; sem resultado concluído.\n")
    print(f"Executando consulta real: até {args.max_requests} requisições pagas, "
          f"{args.max_tokens} tokens por requisição, sem retries, sobre dados sintéticos...")
    try:
        result = run_agent(args.question, df, api_key.strip(), model=args.model,
                           max_requests=args.max_requests, max_tokens=args.max_tokens)
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
    complete = (result.get("complete") is True and bool(trace)
                and all(item.get("success") is True for item in trace)
                and bool(answer.strip()))
    status = "PASSOU" if complete else "INCOMPLETO"
    reason = result.get("completion_reason", "unknown")
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
        f"- Requisições à API: {len(result.get('requests', []))}",
        f"- Resultado do smoke test: **{status}**",
        f"- Motivo técnico: `{reason}`",
        f"- Limites: {args.max_requests} requisições; {args.max_tokens} tokens de saída por requisição",
        "- Observação: não houve implantação em produção ou medição de ganho operacional",
        "",
        "## Pergunta enviada",
        "",
        args.question,
        "",
        "## Resposta retornada",
        "",
        answer or "(Nenhum bloco de texto final retornado.)",
        "",
        "## Rastreabilidade das chamadas locais",
        "",
        "```json",
        fenced(json.dumps(trace, ensure_ascii=False, indent=2)),
        "```",
        "",
        "## Metadados das respostas da API (sem credenciais)",
        "",
        "```json",
        fenced(json.dumps(result.get("requests", []), ensure_ascii=False, indent=2)),
        "```",
        "",
        "## Configuração efetivamente enviada",
        "",
        "```json",
        fenced(json.dumps(result.get("settings", {}), ensure_ascii=False, indent=2)),
        "```",
        "",
        "## Critério do smoke test",
        "",
        "A execução é considerada concluída se a API respondeu, houve ao menos uma "
        "chamada de ferramenta bem-sucedida, nenhuma ferramenta falhou e o agente retornou "
        "texto com stop_reason=end_turn, sem truncamento por tokens ou limite de etapas. "
        "Isso não valida a precisão factual nem o comportamento "
        "em produção; confira os valores com os dados do projeto.",
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"{status}: {len(trace)} chamada(s) de ferramenta. Relatório salvo em {report_path}")
    if not complete:
        print(f"Motivo técnico: {reason}. Nenhuma continuação ou retry automático foi enviado.")
        return 1
    print("Confira o relatório antes de compartilhar ou publicá-lo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
