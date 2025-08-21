"""
Customer segmentation via RFM (Recency, Frequency, Monetary).
- Recency: days since last purchase (lower is better)
- Frequency: number of invoices
- Monetary: total revenue
Quantile-based scoring (1–5), then segment label like "Champions", "Loyal", etc.
"""
from __future__ import annotations
import pandas as pd
import numpy as np

def rfm_table(df: pd.DataFrame, asof: pd.Timestamp | None = None) -> pd.DataFrame:
    if asof is None:
        asof = pd.to_datetime(df["InvoiceDate_mod"].max()) + pd.Timedelta(days=1)

    r = df.groupby("Customer_ID")["InvoiceDate_mod"].max().reset_index()
    r["Recency"] = (asof - r["InvoiceDate_mod"]).dt.days

    f = df.groupby("Customer_ID")["Invoice"].nunique().reset_index().rename(columns={"Invoice":"Frequency"})
    m = df.groupby("Customer_ID")["Revenue"].sum().reset_index().rename(columns={"Revenue":"Monetary"})

    rfm = r.merge(f, on="Customer_ID").merge(m, on="Customer_ID")

    # Scores: Recency reversed (lower recency -> higher score)
    rfm["R_Score"] = pd.qcut(rfm["Recency"], 5, labels=[5,4,3,2,1]).astype(int)
    rfm["F_Score"] = pd.qcut(rfm["Frequency"].rank(method="first"), 5, labels=[1,2,3,4,5]).astype(int)
    rfm["M_Score"] = pd.qcut(rfm["Monetary"].rank(method="first"), 5, labels=[1,2,3,4,5]).astype(int)
    rfm["RFM_Score"] = rfm[["R_Score","F_Score","M_Score"]].sum(axis=1)

    # Simple segment mapping
    def seg(row):
        if row["R_Score"]>=4 and row["F_Score"]>=4 and row["M_Score"]>=4:
            return "Champions"
        if row["R_Score"]>=4 and row["F_Score"]>=3:
            return "Loyal"
        if row["R_Score"]<=2 and row["F_Score"]<=2 and row["M_Score"]<=2:
            return "At Risk"
        if row["R_Score"]<=2 and row["M_Score"]>=4:
            return "Big Spenders (Dormant)"
        return "Regulars"

    rfm["Segment"] = rfm.apply(seg, axis=1)
    return rfm.sort_values(["RFM_Score","Monetary"], ascending=[False,False])
