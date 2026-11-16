"""Daily-report automation, suitable for Task Scheduler/cron/GitHub Actions."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import pandas as pd
from .analytics import analyze_orders, report_md
from .data import generate_demo_orders


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera relatório automático de operações de delivery")
    parser.add_argument("--input", help="Caminho de CSV com os pedidos; se omitido, usa dados sintéticos")
    parser.add_argument("--out", default="reports", help="Diretório de relatórios")
    args = parser.parse_args()
    df = pd.read_csv(args.input) if args.input else generate_demo_orders()
    report = analyze_orders(df)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "analise.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "resumo.md").write_text(report_md(report), encoding="utf-8")
    print(f"Arquivos gerados: {out / 'analise.json'} e {out / 'resumo.md'}")
    print(f"Alertas: {len(report['alerts'])} | Pedidos: {report['kpis']['total_orders']}")

if __name__ == "__main__":
    main()
