
# Ecom-Analytics-Ai
E-commerce Analytics &amp; Forecasting Dashboard (Python + Streamlit + AI).  Features data cleaning, RFM segmentation, SARIMA forecasting, automated narratives, and natural-language queries.
=======
# E‑commerce Analytics & Forecasting (AI‑Ready)
End‑to‑end Data Analytics project using a modernized **UCI Online Retail II** dataset (dates shifted to 2023–2025).  
Tech: Python, Pandas, Plotly, Statsmodels, DuckDB, Streamlit (+ optional LLM for NLQ & narratives).

## What you’ll show recruiters
- Clean, well‑documented data pipeline (wrangling, data quality checks, reproducible saves)
- KPI dashboard (revenue, top products, country trends) in Streamlit *(or Power BI)*
- Customer Segmentation (RFM) with quantile scoring
- Sales Forecasting (3–6 months) on monthly revenue (SARIMA via statsmodels / pmdarima)
- **AI features**: Natural‑Language Query (NL→SQL over DuckDB) and Automated Narratives (templated + optional LLM)
- Storytelling: clear README, screenshots, CV bullets

## Dataset
Assume your CSV lives here on Windows:
```
D:\Ai projects\New folder (2)\online_retail_modern.csv
```
Columns: `Invoice, StockCode, Description, Quantity, InvoiceDate_mod, Price, Customer ID, Country, Revenue`  
*(If `Revenue` missing, it will be computed as `Quantity * Price`.)*

## Quickstart
1) **Create venv & install**
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
```
2) **Set your path** in `config.py`:
```python
DATA_PATH = r"D:\Ai projects\New folder (2)\online_retail_modern.csv"
```
3) **Build cleaned dataset** (one‑off):
```bash
python -m src.data_prep
```
Outputs: `data/cleaned_online_retail.parquet`

4) **Run the Streamlit app**:
```bash
streamlit run dashboard_streamlit/app.py
```
Optional: put your OpenAI key in `.env` to enable NLQ + LLM narratives.

## Power BI (optional)
- Import `data/cleaned_online_retail.parquet` (or the original CSV) into Power BI.
- Use measures from `powerbi/DAX_measures.txt` for KPIs.
- Add line chart (Monthly Revenue), bar chart (Top Products), map (Revenue by Country).
- Add **Smart Narrative** for automated summaries.

## Project structure
```
ecom_analytics_ai/
  ├─ src/
  │   ├─ data_prep.py
  │   ├─ eda.py
  │   ├─ rfm.py
  │   ├─ forecast.py
  │   ├─ ai_narratives.py
  │   └─ nlq_duckdb.py
  ├─ dashboard_streamlit/
  │   └─ app.py
  ├─ powerbi/
  │   └─ DAX_measures.txt
  ├─ config.py
  ├─ requirements.txt
  ├─ .env.example
  └─ README.md
```

## CV bullets (sample)
- Built an **E‑commerce Analytics & Forecasting** app on a modernized UCI dataset: automated data cleaning, RFM segmentation, and SARIMA forecasting; delivered a Streamlit KPI dashboard used to surface **top‑product, country, and seasonality insights**.
- Implemented **AI‑assisted NLQ** over DuckDB (NL→SQL) and **automated narrative** generation, reducing ad‑hoc analysis time by **~60%** while standardizing stakeholder reporting.
- Ensured **reproducibility** with modular Python package, versioned requirements, and environment‑driven configuration; provided Power BI version with DAX KPIs.

## LinkedIn post (template)
> Shipped a CV‑ready **E‑commerce Analytics & Forecasting** dashboard (Python + Streamlit).  
> Highlights: data cleaning pipeline, **RFM** customer segments, **SARIMA** monthly revenue forecast (+6M), and **NLQ** (ask “Which 10 products drove the most revenue in France in Q2 2024?” and get results).  
> Repo + screenshots in comments. Happy to share the template!

## Notes
- If COGS/margins aren’t available, present revenue + returns as quality proxies.
- Returns: negatives in `Quantity` are treated as returns; we keep them but also report a “net revenue” KPI.
>>>>>>> e6a3085 (Initial commit - E-commerce Analytics & Forecasting Dashboard)
