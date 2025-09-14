# --- Make imports robust when running from /dashboard_streamlit ---
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import os
import json
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from src.data_prep import load_raw, clean
from src import eda, rfm, forecast
from src.nlq_duckdb import run_nlq
from src.ai_narratives import templated_story, llm_story

# ---- Env / Secrets ----
load_dotenv()  # .env for local dev
# Prefer Streamlit secrets in the cloud
if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

# ---- Page config ----
st.set_page_config(page_title="E-commerce Analytics & Forecasting", layout="wide")
st.title("🛒 E-commerce Analytics & Forecasting (AI-Ready)")

# ---- Data source options (Cloud-safe) ----
st.sidebar.subheader("Data source")

use_sample = st.sidebar.toggle("Use sample dataset (recommended for cloud)", value=True)
uploaded_file = st.sidebar.file_uploader("Or upload CSV", type=["csv"])

# Local path is only for desktop users; in Streamlit Cloud this likely won't exist
default_local = r"D:\Ai projects\New folder (2)\online_retail_modern.csv"
local_path = st.sidebar.text_input("Local CSV path (desktop only)", value=default_local)

# Cached loaders
@st.cache_data(show_spinner=False)
def get_cleaned_from_csvbuffer(file) -> pd.DataFrame:
    raw = pd.read_csv(file, low_memory=False)
    # normalise like data_prep.load_raw does
    raw.columns = [c.strip().replace(" ", "_").replace("-", "_") for c in raw.columns]
    # some datasets might use InvoiceDate not InvoiceDate_mod
    if "InvoiceDate" in raw.columns and "InvoiceDate_mod" not in raw.columns:
        raw.rename(columns={"InvoiceDate": "InvoiceDate_mod"}, inplace=True)
    if "UnitPrice" in raw.columns and "Price" not in raw.columns:
        raw.rename(columns={"UnitPrice": "Price"}, inplace=True)
    return clean(raw)

@st.cache_data(show_spinner=False)
def get_cleaned_from_path(path: str) -> pd.DataFrame:
    df = load_raw(path)
    return clean(df)

@st.cache_data(show_spinner=False)
def get_cleaned_sample() -> pd.DataFrame:
    # sample lives in repo: /samples/online_retail_modern_sample.csv
    sample_path = os.path.join(os.path.dirname(__file__), "..", "samples", "online_retail_modern_sample.csv")
    if not os.path.exists(sample_path):
        raise FileNotFoundError("Sample file missing. Please add samples/online_retail_modern_sample.csv to the repo.")
    return get_cleaned_from_path(sample_path)

# Decide data source priority: upload > sample toggle > local path
try:
    if uploaded_file is not None:
        df = get_cleaned_from_csvbuffer(uploaded_file)
    elif use_sample:
        df = get_cleaned_sample()
    else:
        if os.path.exists(local_path):
            df = get_cleaned_from_path(local_path)
        else:
            st.error("No data source available. Use the sample dataset or upload a CSV.")
            st.stop()
except Exception as e:
    st.error(f"Failed to load/clean data: {e}")
    st.stop()

# ---- Filters ----
countries = ["All"] + sorted([c for c in df["Country"].dropna().unique().tolist()])
sel_country = st.sidebar.selectbox("Country", countries, index=0)
date_min, date_max = df["InvoiceDate_mod"].min(), df["InvoiceDate_mod"].max()
sel_range = st.sidebar.date_input("Date range", (date_min, date_max), min_value=date_min, max_value=date_max)

mask = (df["InvoiceDate_mod"] >= pd.to_datetime(sel_range[0])) & (df["InvoiceDate_mod"] <= pd.to_datetime(sel_range[1]))
if sel_country != "All":
    mask &= (df["Country"] == sel_country)
df_f = df.loc[mask].copy()

# ---- KPIs ----
k = eda.kpis(df_f)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Revenue", f"£{k['Total Revenue']:,.0f}")
c2.metric("Net Revenue", f"£{k['Net Revenue']:,.0f}")
c3.metric("Orders", f"{k['Orders']:,}")
c4.metric("Customers", f"{k['Customers']:,}")

# ---- Charts ----
mrev = eda.monthly_revenue(df_f)
fig_m = px.line(mrev, x="Month", y="Revenue", title="Monthly Revenue")
st.plotly_chart(fig_m, use_container_width=True)

topn = eda.top_products(df_f, n=10)
fig_p = px.bar(topn, x="Revenue", y="Description", orientation="h", title="Top 10 Products by Revenue")
st.plotly_chart(fig_p, use_container_width=True)

byc = eda.revenue_by_country(df_f)
fig_c = px.bar(byc.head(15), x="Country", y="Revenue", title="Revenue by Country (Top 15)")
st.plotly_chart(fig_c, use_container_width=True)

# ---- RFM ----
st.subheader("👥 Customer Segmentation (RFM)")
rfm_tbl = rfm.rfm_table(df_f)
st.dataframe(rfm_tbl.head(25))

# ---- Forecast ----
st.subheader("📈 Forecast (next 6 months)")
fc = forecast.forecast_df(df_f, periods=6)
fig_fc = px.line(fc, x="Month", y="Forecast", title="Forecasted Monthly Revenue (next 6m)")
st.plotly_chart(fig_fc, use_container_width=True)

# ---- Automated narrative ----
st.subheader("🧠 Automated Narrative")
try:
    top_country = byc.iloc[0]["Country"] if not byc.empty else ""
except Exception:
    top_country = ""
try:
    top_product = topn.iloc[0]["Description"] if not topn.empty else ""
except Exception:
    top_product = ""

# MoM change on filtered data
try:
    mom = (mrev["Revenue"].iloc[-1] - mrev["Revenue"].iloc[-2]) / max(1e-9, abs(mrev["Revenue"].iloc[-2])) * 100
except Exception:
    mom = None

base_story = templated_story(k, top_country, top_product, mom)
st.write(base_story)

use_llm = st.toggle("Enhance with LLM (requires OPENAI_API_KEY)", value=False)
if use_llm and os.getenv("OPENAI_API_KEY"):
    better = llm_story("Rewrite this ecommerce analytics summary for execs: " + base_story)
    if better:
        st.write(better)

# ---- NLQ ----
st.subheader("💬 Ask a question in plain English")
q = st.text_input("e.g., Top 10 products by revenue in France in Q2 2024")
if st.button("Run NLQ") and q:
    try:
        ans = run_nlq(df_f, q, use_llm=use_llm and bool(os.getenv('OPENAI_API_KEY')))
        st.dataframe(ans)
        # quick chart if possible
        if "Month" in ans.columns and "Revenue" in ans.columns:
            st.plotly_chart(px.line(ans, x="Month", y="Revenue", title=q), use_container_width=True)
        elif "Revenue" in ans.columns and ans.shape[0] <= 30:
            cols = [c for c in ans.columns if c.lower() not in {"revenue"}]
            if cols:
                st.plotly_chart(px.bar(ans, x=cols[0], y="Revenue", title=q), use_container_width=True)
    except Exception as e:
        st.error(str(e))

st.caption("Tip: On Streamlit Cloud, use the sample or upload a CSV. Add OPENAI_API_KEY in app secrets to enable LLM.")
