"""
Monthly revenue forecasting: SARIMA (via pmdarima auto_arima if available, else a sensible default).
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Tuple

def prepare_ts(df: pd.DataFrame) -> pd.Series:
    ts = df.set_index("InvoiceDate_mod").resample("M")["Revenue"].sum()
    ts = ts.asfreq("M").fillna(0.0)
    return ts

def fit_forecast(ts: pd.Series, periods: int = 6) -> Tuple[pd.Series, object]:
    try:
        import pmdarima as pm
        model = pm.auto_arima(ts, seasonal=True, m=12, trace=False, suppress_warnings=True)
        model_fit = model
        fc = model.predict(n_periods=periods)
        idx = pd.period_range(ts.index[-1] + 1, periods=periods, freq="M").to_timestamp()
        forecast = pd.Series(fc, index=idx, name="Forecast")
        return forecast, model_fit
    except Exception:
        # Fallback SARIMA(1,1,1)(0,1,1)[12]
        from statsmodels.tsa.statespace.sarimax import SARIMAX
        model = SARIMAX(ts, order=(1,1,1), seasonal_order=(0,1,1,12), enforce_stationarity=False, enforce_invertibility=False)
        res = model.fit(disp=False)
        fut = res.get_forecast(steps=periods)
        forecast = fut.predicted_mean.rename("Forecast")
        return forecast, res

def forecast_df(df: pd.DataFrame, periods: int = 6) -> pd.DataFrame:
    ts = prepare_ts(df)
    fc, _ = fit_forecast(ts, periods=periods)
    out = pd.DataFrame({
        "Month": fc.index.to_period("M").astype(str),
        "Forecast": fc.values
    })
    return out
