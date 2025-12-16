from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uvicorn
import pandas as pd
import threading
from contextlib import asynccontextmanager
import numpy as np 
from analytics import compute_spread_zscore, run_adf_test, compute_ols_beta 
from data_handler import get_ohlcv_data
from websocket_client import start_ws_client


ALERT_LOG = []
LIVE_ANALYTICS = {} 


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    threading.Thread(target=start_ws_client, daemon=True).start()
    print("WebSocket Ingestion started in background.")
    yield


app = FastAPI(title="Quant Analytics Backend", lifespan=lifespan)


class PairParams(BaseModel):
    symbol_y: str
    symbol_x: str
    timeframe: str
    window: int

class AlertRule(BaseModel):
    symbol: str
    metric: str 
    operator: str 
    value: float



@app.get("/api/v1/ohlc/{symbol}")
def get_ohlc(symbol: str):
    """API to get resampled OHLC data for plotting."""
    df = get_ohlcv_data(symbol.upper()) 
    
    if df.empty:
        return []
        
    
    return df.reset_index().to_dict(orient='records')

@app.post("/api/v1/analytics/zscore")
def get_analytics(params: PairParams):
    """API to calculate the Hedge Ratio, Spread, and Z-Score."""
    
    # 1. Fetch data
    df_y_ohlc = get_ohlcv_data(params.symbol_y)
    df_x_ohlc = get_ohlcv_data(params.symbol_x)

    if df_y_ohlc.empty or df_x_ohlc.empty:
        return []

    
    y = df_y_ohlc['close']
    x = df_x_ohlc['close']
    
    
    analytics_df = compute_spread_zscore(y, x, params.window)

    if analytics_df.empty:
        return []

    
    analytics_df = analytics_df.replace([np.inf, -np.inf], np.nan).dropna()
    
    if analytics_df.empty: 
        return []

    
    pair_key = f'{params.symbol_y}_{params.symbol_x}'
    LIVE_ANALYTICS[f'ZSCORE_{pair_key}'] = analytics_df['ZScore'].iloc[-1]
    LIVE_ANALYTICS[f'BETA_{pair_key}'] = analytics_df['Beta'].iloc[-1]
    
    
    return analytics_df.reset_index().to_dict(orient='records')

@app.post("/api/v1/analytics/adf")
def run_adf(params: PairParams):
    """API to run the Augmented Dickey-Fuller test on the spread."""
    try:
        
        df_y_ohlc = get_ohlcv_data(params.symbol_y)
        df_x_ohlc = get_ohlcv_data(params.symbol_x)
        
        if df_y_ohlc.empty or df_x_ohlc.empty:
             return {"status": "Data insufficient for ADF test."} 
        
        y = df_y_ohlc['close']
        x = df_x_ohlc['close']
        
        
        beta = compute_ols_beta(y, x)
        
        combined = pd.DataFrame({'Y': y, 'X': x}).dropna()
        spread = combined['Y'] - beta * combined['X']

        
        result = run_adf_test(spread.dropna()) 
        
        return {
            "status": "ADF Test results available.",
            "test_statistic": result['Test Statistic'],
            "p_value": result['p-value'],
            "critical_values": result['Critical Values'],
            "Result": result.get('Result', 'N/A')
        }
    except Exception as e:
        print(f"Error running ADF test: {e}")
        return {"status": f"ADF Test Failed: {e}"}

@app.get("/api/v1/alerts/live")
def get_live_alerts():
    """Returns the current log of triggered alerts."""
    current_alerts = []
    
    for key, z_score in LIVE_ANALYTICS.items():
        if key.startswith('ZSCORE') and abs(z_score) > 2.0:
             
             pair = key.split('_')[1:] 
             current_alerts.append(f"ALERT: Z-Score for {'_'.join(pair)} is at {z_score:.2f}")
    
    return current_alerts

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)