import pytest
import pandas as pd
from foodflow.data import generate_demo_orders
from foodflow.analytics import clean_orders, analyze_orders, kpis, recommended_actions, restaurant_ranking, get_store_details, report_md
from foodflow.agent import call_tool


def test_data_reproducible():
    a = generate_demo_orders(30)
    b = generate_demo_orders(30)
    pd.testing.assert_frame_equal(a, b)


def test_main_analysis():
    data = generate_demo_orders(1200)
    result = analyze_orders(data)
    assert result["kpis"]["total_orders"] == 1200
    assert result["kpis"]["delivered_orders"] + result["kpis"]["cancelled_orders"] == 1200
    assert len(result["ranking"]) == 10
    assert result["alerts"]
    assert "LOJA-03" in [x["restaurant_id"] for x in result["ranking"][:5]]
    assert "propostas" in report_md(result).lower()


def test_reject_duplicate_ids():
    data = generate_demo_orders(10)
    data.loc[1, "order_id"] = data.loc[0, "order_id"]
    with pytest.raises(ValueError, match="único"):
        clean_orders(data)


def test_reject_missing_delivery_time():
    data = generate_demo_orders(30)
    idx = data.index[data["status"] == "delivered"][0]
    data.loc[idx, "actual_minutes"] = None
    with pytest.raises(ValueError, match="actual_minutes"):
        clean_orders(data)


def test_cancelled_orders_not_counted_as_late():
    data = pd.DataFrame([{"order_id": "x1", "restaurant_id": "A", "region": "Centro", "created_at": "2026-10-01", "promised_minutes": 20, "actual_minutes": None, "order_value_brl": 10.0, "status": "cancelled"}])
    result = analyze_orders(data)
    assert result["kpis"]["late_rate_pct"] == 0
    assert result["kpis"]["cancellation_rate_pct"] == 100


def test_tools_read_only():
    data = clean_orders(generate_demo_orders(80))
    assert call_tool("get_kpis", {}, data)["total_orders"] == 80
    assert isinstance(call_tool("rank_restaurants", {"limit": 3}, data), list)
    assert "error" in call_tool("delete_data", {}, data)
    assert "error" in get_store_details(data, "nao-existe")
