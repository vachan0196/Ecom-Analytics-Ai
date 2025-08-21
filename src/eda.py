"""
EDA helpers: KPIs, aggregations, and plots (dataframe outputs).
Use Plotly in the Streamlit app for visuals.
"""
from __future__ import annotations
import pandas as pd

def kpis(df: pd.DataFrame) -> dict:
    total_revenue = float(df["Revenue"].sum())
    orders = df["Invoice"].nunique() if "Invoice" in df.columns else df.shape[0]
    customers = df["Customer_ID"].nunique()
    returns = float(df.loc[df["Is_Return"], "Revenue"].sum())
    net_revenue = float(df.loc[~df["Is_Return"], "Revenue"].sum() + returns)  # returns negative
    return {
        "Total Revenue": total_revenue,
        "Net Revenue": net_revenue,
        "Orders": int(orders),
        "Customers": int(customers),
        "Return Impact": returns
    }

def revenue_by_country(df: pd.DataFrame) -> pd.DataFrame:
    grp = df.groupby("Country", dropna=False)["Revenue"].sum().reset_index().sort_values("Revenue", ascending=False)
    return grp

def top_products(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    cols = [c for c in ["Description", "StockCode"] if c in df.columns]
    grp = df.groupby(cols, dropna=False)["Revenue"].sum().reset_index().sort_values("Revenue", ascending=False)
    return grp.head(n)

def monthly_revenue(df: pd.DataFrame) -> pd.DataFrame:
    m = df.set_index("InvoiceDate_mod").resample("M")["Revenue"].sum().reset_index()
    m["Month"] = m["InvoiceDate_mod"].dt.to_period("M").astype(str)
    return m[["Month", "Revenue"]]

def sales_pivot_country_month(df: pd.DataFrame) -> pd.DataFrame:
    tmp = df.copy()
    tmp["Month"] = tmp["InvoiceDate_mod"].dt.to_period("M").astype(str)
    pv = tmp.pivot_table(index="Month", columns="Country", values="Revenue", aggfunc="sum", fill_value=0)
    return pv.reset_index()
