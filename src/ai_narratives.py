"""
Automated insight narratives: templated + optional LLM enhancement.
"""
from __future__ import annotations
import os
from typing import Dict
import math

def _fmt_currency(x: float) -> str:
    absx = abs(x)
    if absx >= 1e6:
        return f"£{x/1e6:.1f}M"
    if absx >= 1e3:
        return f"£{x/1e3:.1f}k"
    return f"£{x:.0f}"

def templated_story(kpis: Dict[str, float], top_country: str, top_product: str, mom_change: float | None) -> str:
    parts = []
    parts.append(f"Total revenue: {_fmt_currency(kpis.get('Total Revenue',0))}; Net revenue: {_fmt_currency(kpis.get('Net Revenue',0))}.")
    parts.append(f"Orders: {kpis.get('Orders',0)}, Customers: {kpis.get('Customers',0)}.")
    parts.append(f"Return impact this period: {_fmt_currency(kpis.get('Return Impact',0))}.")
    if top_country:
        parts.append(f"Top country by revenue: {top_country}.")
    if top_product:
        parts.append(f"Best‑selling product: {top_product}.")
    if mom_change is not None and not math.isnan(mom_change):
        trend = "↑" if mom_change > 0 else "↓"
        parts.append(f"Month‑over‑month revenue changed {trend} {abs(mom_change):.1f}%.")
    return " ".join(parts)

def llm_story(prompt: str) -> str:
    # Optional LLM enhancement if OPENAI_API_KEY present
    try:
        from openai import OpenAI
        client = OpenAI()
        msg = [
            {"role":"system","content":"You are a concise analytics writer. Use UK English and keep it under 150 words."},
            {"role":"user","content": prompt}
        ]
        resp = client.chat.completions.create(model="gpt-4o-mini", messages=msg, temperature=0.2)
        return resp.choices[0].message.content.strip()
    except Exception:
        return ""  # Silent fallback
