"""
Data loading & cleaning for Online Retail II (modernized 2023–2025).
- Parses InvoiceDate_mod
- Ensures numeric types
- Computes Revenue if missing
- Flags returns (Quantity < 0)
- Drops exact duplicate rows
- Saves cleaned parquet for downstream steps
"""
from __future__ import annotations
import os
import pandas as pd
from pathlib import Path
from . import eda  # for helpers
import warnings
warnings.filterwarnings("ignore")

# Allow running as a module or script
try:
    from config import DATA_PATH, CLEAN_DIR, CLEAN_FILE  # type: ignore
except Exception:
    # Fallback for direct run
    DATA_PATH = r"D:\Ai projects\New folder (2)\online_retail_modern.csv"
    CLEAN_DIR = "data"
    CLEAN_FILE = "cleaned_online_retail.parquet"

def load_raw(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8", low_memory=False)
    # Normalize column names
    df.columns = [c.strip().replace(" ", "_").replace("-", "_") for c in df.columns]
    # Expected columns (some datasets use 'CustomerID' vs 'Customer_ID')
    rename_map = {
        "CustomerID": "Customer_ID",
        "Customer Id": "Customer_ID",
        "Customer id": "Customer_ID",
        "InvoiceDate_mod": "InvoiceDate_mod",
        "InvoiceDate": "InvoiceDate_mod",  # fallback if not modernized
        "UnitPrice": "Price"
    }
    for k, v in rename_map.items():
        if k in df.columns and v not in df.columns:
            df.rename(columns={k: v}, inplace=True)
    return df

def clean(df: pd.DataFrame) -> pd.DataFrame:
    # Types
    if "InvoiceDate_mod" in df.columns:
        df["InvoiceDate_mod"] = pd.to_datetime(df["InvoiceDate_mod"], errors="coerce")
    else:
        raise ValueError("Missing 'InvoiceDate_mod' column.")

    # Ensure Price/Quantity numeric
    for col in ["Quantity", "Price"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Compute Revenue if missing
    if "Revenue" not in df.columns:
        df["Revenue"] = df["Quantity"] * df["Price"]

    # Customer_ID as string
    if "Customer_ID" in df.columns:
        df["Customer_ID"] = df["Customer_ID"].astype("Int64").astype("string")
    elif "Customer" in df.columns:
        df["Customer_ID"] = df["Customer"].astype("string")
    else:
        # Create pseudo IDs if totally missing (rare)
        df["Customer_ID"] = df.groupby("Invoice").ngroup().astype("int").astype("string")

    # Basic quality flags
    df["Is_Return"] = (df["Quantity"] < 0)

    # Drop exact duplicates
    df = df.drop_duplicates()

    # Drop rows with null criticals
    df = df.dropna(subset=["InvoiceDate_mod", "Quantity", "Price"])

    # Keep only reasonable price/qty
    df = df[(df["Price"] >= 0) & (df["Quantity"] != 0)]

    # Add Year/Month for convenience
    df["Year"] = df["InvoiceDate_mod"].dt.year
    df["Month"] = df["InvoiceDate_mod"].dt.to_period("M").astype(str)

    # Country normalization
    if "Country" in df.columns:
        df["Country"] = df["Country"].str.strip()

    return df

def save_clean(df: pd.DataFrame, out_dir: str = CLEAN_DIR, out_file: str = CLEAN_FILE) -> str:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    out_path = os.path.join(out_dir, out_file)
    df.to_parquet(out_path, index=False)
    return out_path

def main():
    print(f"Loading: {DATA_PATH}")
    raw = load_raw(DATA_PATH)
    print(f"Raw shape: {raw.shape}")
    df = clean(raw)
    print(f"Cleaned shape: {df.shape}")
    out = save_clean(df)
    print(f"Saved cleaned dataset to: {out}")

if __name__ == "__main__":
    main()
