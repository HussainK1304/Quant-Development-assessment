import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import time 


API_BASE_URL = "http://localhost:8000/api/v1"
SYMBOL_OPTIONS = ['BTCUSDT', 'ETHUSDT']


@st.cache_data(ttl=1) 
def fetch_ohlc_data(symbol):
    try:
        response = requests.get(f"{API_BASE_URL}/ohlc/{symbol}")
        response.raise_for_status()
        data = pd.DataFrame(response.json())
        
        if not data.empty:
            data['timestamp'] = pd.to_datetime(data['timestamp'], errors='coerce') 
            data = data.dropna(subset=['timestamp']) 
            return data.set_index('timestamp').sort_index()
        return pd.DataFrame()
        
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=1)
def fetch_analytics_data(symbol_y, symbol_x, timeframe, window):
    try:
        params = {
            "symbol_y": symbol_y,
            "symbol_x": symbol_x,
            "timeframe": timeframe,
            "window": window
        }
        response = requests.post(f"{API_BASE_URL}/analytics/zscore", json=params)
        response.raise_for_status()
        data = pd.DataFrame(response.json())
        if not data.empty:
            data['timestamp'] = pd.to_datetime(data['timestamp'], errors='coerce')
            data = data.dropna(subset=['timestamp'])
            return data.set_index('timestamp').sort_index()
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

def trigger_adf_test(symbol_y, symbol_x, timeframe, window):
    try:
        params = {
            "symbol_y": symbol_y,
            "symbol_x": symbol_x,
            "timeframe": timeframe,
            "window": window
        }
        response = requests.post(f"{API_BASE_URL}/analytics/adf", json=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"ADF Test Failed: {e}")
        return {"status": "ADF Test failed."}

# --- Plotting Functions ---

def plot_price_chart(df: pd.DataFrame, symbol: str) -> go.Figure:
    """Plots a candlestick chart."""
    fig = go.Figure(data=[
        go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name=symbol
        )
    ])
    fig.update_layout(xaxis_rangeslider_visible=False, title=f'{symbol} Price Chart')
    return fig

def plot_zscore_chart(df: pd.DataFrame) -> go.Figure:
    """Plots the Spread and Z-Score."""
    fig = go.Figure()
    
    
    fig.add_trace(go.Scatter(x=df.index, y=df['Spread'], name='Spread', yaxis='y1'))
    
    
    fig.add_trace(go.Scatter(x=df.index, y=df['ZScore'], name='Z-Score', yaxis='y2'))
    
    
    fig.add_hline(y=2, line_dash="dash", line_color="red", yref='y2')
    fig.add_hline(y=-2, line_dash="dash", line_color="red", yref='y2')
    
    fig.update_layout(
        title='Spread and Z-Score',
        yaxis=dict(title='Spread', side='left'),
        yaxis2=dict(title='Z-Score', side='right', overlaying='y', range=[-3, 3]),
        hovermode="x unified",
    )
    return fig

# --- Main Streamlit App ---

def main():
    st.set_page_config(layout="wide", page_title="Real-Time Quant Dashboard")

    st.title("📈 Real-Time Quant Analytics Dashboard")

    
    with st.sidebar:
        st.header("App Controls")
        st.info("Ensure the FastAPI backend is running on port 8000 first!")

        
        st.subheader("Symbol Selection")
        sym_y = st.selectbox("Symbol Y (Dependent)", SYMBOL_OPTIONS, index=0)
        sym_x = st.selectbox("Symbol X (Independent)", SYMBOL_OPTIONS, index=1)
        
       
        st.subheader("Data & Model Params")
        timeframe = st.sidebar.selectbox('Resample Timeframe', ['1s','1m', '5m', '1h', '1d'], index=0)
        rolling_window = st.slider("Rolling Window (Z-Score/Correlation)", min_value=1, max_value=200, value=20, step=1)
        
        
        if st.button("Run ADF Test"):
            with st.spinner("Running ADF Test on Spread..."):
                adf_result = trigger_adf_test(sym_y, sym_x, timeframe, rolling_window)
                st.subheader("ADF Test Results")
                st.json(adf_result)

         
        st.subheader("Data Export")
        download_button_placeholder = st.empty()
        
    
    dashboard_placeholder = st.empty()
    
    data_status_placeholder = st.empty()

    
    # --- Main Refresh Loop ---
    while True:
        
        
        df_y = fetch_ohlc_data(sym_y)
        df_x = fetch_ohlc_data(sym_x)
        analytics_df = fetch_analytics_data(sym_y, sym_x, timeframe, rolling_window)

        
        data_status_placeholder.info(
            f"Data status: {sym_y} rows: {len(df_y)}, {sym_x} rows: {len(df_x)}, Analytics rows: {len(analytics_df)}"
        )

        unique_key_suffix = time.time()

        with dashboard_placeholder.container():
            
            
            if df_y.empty or df_x.empty:
                st.warning(f"Waiting for sufficient {timeframe} data to be ingested for {sym_y} and {sym_x}. Please wait.")
            else:
                
                
                col1, col2, col3 = st.columns(3)
                
                has_analytics_data = not analytics_df.empty and len(analytics_df) >= rolling_window
                
                 
                latest_beta = analytics_df['Beta'].iloc[-1] if has_analytics_data else 0.0
                col1.metric("Hedge Ratio (Beta)", f"{latest_beta:.4f}")
                
                
                latest_zscore_val = analytics_df['ZScore'].iloc[-1] if has_analytics_data else None
                
                if latest_zscore_val is not None:
                    latest_zscore = float(latest_zscore_val)
                    col2.metric("Latest Z-Score", f"{latest_zscore:.2f}", delta=f"{'ALERT' if abs(latest_zscore) > 2 else 'OK'}")
                else:
                    col2.metric("Latest Z-Score", "Calculating...")
                
                
                live_alerts = []
                try:
                    alert_response = requests.get(f"{API_BASE_URL}/alerts/live")
                    alert_response.raise_for_status()
                    live_alerts = alert_response.json()
                    col3.metric("Live Alerts Triggered", len(live_alerts))
                except:
                    col3.metric("Live Alerts Triggered", "N/A")
                
                if live_alerts:
                    st.warning("⚠️ ALERT LOG: " + ", ".join(live_alerts))

                st.markdown("---")

                
                chart_col1, chart_col2 = st.columns(2)
                
                
                with chart_col1:
                    st.subheader(f"Price Chart ({timeframe})")
                    st.plotly_chart(plot_price_chart(df_y, sym_y), use_container_width=True, key=f"price_chart_{sym_y}_{unique_key_suffix}")
                    
                
                with chart_col2:
                    st.subheader("Spread and Z-Score")
                    if has_analytics_data:
                        st.plotly_chart(plot_zscore_chart(analytics_df), use_container_width=True, key=f"zscore_chart_{sym_y}_{sym_x}_{unique_key_suffix}")
                    else:
                        st.info(f"Collecting enough data for the rolling window of {rolling_window} bars...")
                
                
                st.markdown("---")
                st.subheader("Processed Analytics Data")
                
                
                display_df = pd.merge(df_y['close'].rename(f'{sym_y}_Close'), 
                                    df_x['close'].rename(f'{sym_x}_Close'), 
                                    left_index=True, 
                                    right_index=True, 
                                    how='inner')
                
                final_df = pd.merge(display_df, 
                                    analytics_df[['Spread', 'ZScore', 'Beta']], 
                                    left_index=True, 
                                    right_index=True, 
                                    how='inner')
                                    
                st.dataframe(final_df.iloc[-50:]) 
                
                
                with download_button_placeholder.container():
                    st.download_button(
                        label="Download Full Processed CSV",
                        data=final_df.to_csv().encode('utf-8'),
                        file_name=f'analytics_export_{sym_y}_{sym_x}_{timeframe}.csv',
                        mime='text/csv',
                        
                        key=f'download_button_{unique_key_suffix}' 
                    )
        
        
        time.sleep(0.5)

if __name__ == "__main__":
    main()