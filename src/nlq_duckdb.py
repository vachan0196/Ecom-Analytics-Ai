"""
Natural Language Query -> SQL over DuckDB + Pandas.
- Safe pattern matcher for common questions (no LLM required)
- Optional LLM path if OPENAI_API_KEY is set for broader coverage
"""
from __future__ import annotations
import re
import duckdb
import pandas as pd
from typing import Optional

def register_df(conn, df: pd.DataFrame, name: str = "sales"):
    conn.register(name, df)

def safe_translate(question: str) -> Optional[str]:
    q = question.lower().strip()

    # Examples:
    # "total revenue in 2024"
    m = re.search(r"total revenue(?: in (\d{4}))?", q)
    if m:
        year = m.group(1)
        if year:
            return f"SELECT SUM(Revenue) AS total_revenue FROM sales WHERE EXTRACT(YEAR FROM InvoiceDate_mod) = {year};"
        return "SELECT SUM(Revenue) AS total_revenue FROM sales;"

    # "top 10 products by revenue in france in q2 2024"
    m = re.search(r"top (\d+)\s+products.*?revenue(?: in ([a-z\s]+))?(?:.*?q([1-4]))?(?:.*?(\d{4}))?", q)
    if m:
        topn = int(m.group(1))
        country = m.group(2).title().strip() if m.group(2) else None
        qtr = m.group(3)
        year = m.group(4)
        where = []
        if country:
            where.append(f"lower(Country) = lower('{country}')")
        if qtr and year:
            months = {'1':'(1,2,3)','2':'(4,5,6)','3':'(7,8,9)','4':'(10,11,12)'}[qtr]
            where.append(f"EXTRACT(YEAR FROM InvoiceDate_mod) = {year} AND EXTRACT(MONTH FROM InvoiceDate_mod) IN {months}")
        clause = ("WHERE " + " AND ".join(where)) if where else ""
        return f"""
        SELECT COALESCE(Description, StockCode) AS Product, SUM(Revenue) AS Revenue
        FROM sales
        {clause}
        GROUP BY 1
        ORDER BY Revenue DESC
        LIMIT {topn};
        """

    # "revenue by country in 2025"
    m = re.search(r"revenue by country(?: in (\d{4}))?", q)
    if m:
        year = m.group(1)
        if year:
            return f"SELECT Country, SUM(Revenue) AS Revenue FROM sales WHERE EXTRACT(YEAR FROM InvoiceDate_mod) = {year} GROUP BY 1 ORDER BY 2 DESC;"
        return "SELECT Country, SUM(Revenue) AS Revenue FROM sales GROUP BY 1 ORDER BY 2 DESC;"

    # "monthly revenue for uk"
    m = re.search(r"monthly revenue(?: for ([a-z\s]+))?", q)
    if m:
        country = m.group(1).title().strip() if m.group(1) else None
        clause = f"WHERE lower(Country) = lower('{country}')" if country else ""
        return f"""
        SELECT strftime(InvoiceDate_mod, '%Y-%m') AS Month, SUM(Revenue) AS Revenue
        FROM sales
        {clause}
        GROUP BY 1 ORDER BY 1;
        """
    return None

def llm_translate(question: str, schema_hint: str) -> Optional[str]:
    try:
        from openai import OpenAI
        client = OpenAI()
        sys = "You translate English questions into safe ANSI SQL for DuckDB. Only use the given table & columns."
        user = f"Schema:\n{schema_hint}\nQuestion:\n{question}\nReturn only SQL; no commentary."
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":sys},{"role":"user","content":user}],
            temperature=0.0
        )
        sql = resp.choices[0].message.content.strip().strip('`')
        return sql
    except Exception:
        return None

def run_nlq(df: pd.DataFrame, question: str, use_llm: bool = True) -> pd.DataFrame:
    conn = duckdb.connect()
    register_df(conn, df, "sales")

    sql = safe_translate(question)
    if not sql and use_llm:
        schema_hint = "sales(Invoice, StockCode, Description, Quantity, InvoiceDate_mod TIMESTAMP, Price, Customer_ID, Country, Revenue, Is_Return, Year, Month)"
        sql = llm_translate(question, schema_hint)

    if not sql:
        raise ValueError("Could not translate question. Try a different phrasing.")

    return conn.execute(sql).df()
