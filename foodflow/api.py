"""Small FastAPI for JSON workflows (n8n/Make/Zapier) and reproducible demos."""
from __future__ import annotations
from typing import Any
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .analytics import analyze_orders
from .data import generate_demo_orders

app = FastAPI(title="FoodFlow AI API", version="1.0.0", description="API de demonstração. Não oficial do iFood.")

class OrderBatch(BaseModel):
    orders: list[dict[str, Any]] = Field(min_length=1, max_length=15000)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "foodflow-ai", "environment": "demo"}

@app.get("/demo-analysis")
def demo_analysis() -> dict[str, Any]:
    return analyze_orders(generate_demo_orders())

@app.post("/analyze")
def analyze(payload: OrderBatch) -> dict[str, Any]:
    try:
        return analyze_orders(pd.DataFrame(payload.orders))
    except (ValueError, TypeError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
