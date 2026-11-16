"""Synthetic demonstration data: no iFood or third-party real transaction data."""
from __future__ import annotations
from datetime import datetime, timedelta
from random import Random
import pandas as pd


def generate_demo_orders(n: int = 1200, seed: int = 42) -> pd.DataFrame:
    """Create reproducible simulated delivery orders with planted operational bottlenecks."""
    rng = Random(seed)
    n = max(1, min(int(n), 15000))
    stores = [f"LOJA-{i:02d}" for i in range(1, 11)]
    regions = ["Centro", "Zona Norte", "Zona Sul", "Zona Oeste"]
    start = datetime(2026, 10, 1, 11, 0)
    rows: list[dict] = []
    for i in range(n):
        store = rng.choice(stores)
        region = regions[(int(store[-2:]) - 1) % len(regions)]
        created = start + timedelta(minutes=rng.randint(0, 14 * 24 * 60))
        promised = rng.choice([25, 30, 35, 40, 45])
        base_delay = rng.gauss(-2, 9)
        if store == "LOJA-03":
            base_delay += 19  # Planned elevated lateness in synthetic fixture.
        if created.hour in [12, 13, 19, 20]:
            base_delay += 5
        cancelled_prob = 0.19 if store == "LOJA-07" else 0.035
        cancelled = rng.random() < cancelled_prob
        actual = None if cancelled else max(8, round(promised + base_delay))
        rows.append({
            "order_id": f"PED-{i+1:05d}",
            "restaurant_id": store,
            "region": region,
            "created_at": created.isoformat(timespec="minutes"),
            "promised_minutes": promised,
            "actual_minutes": actual,
            "order_value_brl": round(rng.uniform(21, 135), 2),
            "status": "cancelled" if cancelled else "delivered",
        })
    return pd.DataFrame(rows).sort_values("created_at").reset_index(drop=True)
