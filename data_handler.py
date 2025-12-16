import sqlite3
import pandas as pd
from typing import List, Dict, Any
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'db.sqlite')

def init_db():
    """Initializes the SQLite database table for sampled OHLC data."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ohlcv_data (
            timestamp TEXT NOT NULL,
            symbol TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            PRIMARY KEY (timestamp, symbol)
        )
    """)
    conn.commit()
    conn.close()

def store_ohlcv_data(df: pd.DataFrame, symbol: str, timeframe: str):
    """Stores the sampled OHLCV data into SQLite using INSERT OR REPLACE (UPSERT)."""
    if df.empty:
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
   
    df = df.reset_index()
    
    
    potential_ts_cols = [col for col in df.columns if col in ['timestamp', 'time', 'index']]
    
    if potential_ts_cols:
       
        df = df.rename(columns={potential_ts_cols[0]: 'timestamp'})
    else:
        
        conn.close()
        return

    
    for index, row in df.iterrows():
        try:
            timestamp_str = row['timestamp'].isoformat()
            
            cursor.execute("""
                INSERT OR REPLACE INTO ohlcv_data 
                (timestamp, symbol, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp_str,
                symbol,
                row['open'],
                row['high'],
                row['low'],
                row['close'],
                row['volume']
            ))
        except Exception:
            pass

    conn.commit()
    conn.close()

def get_ohlcv_data(symbol: str, limit: int = 500) -> pd.DataFrame:
    """Retrieves sampled OHLCV data from SQLite."""
    conn = sqlite3.connect(DB_PATH)
    query = f"""
        SELECT * FROM ohlcv_data
        WHERE symbol = '{symbol}'
        ORDER BY timestamp DESC
        LIMIT {limit}
    """
    df = pd.read_sql_query(
        query, 
        conn, 
        index_col='timestamp', 
        parse_dates=['timestamp'] 
    ) 
    conn.close()
    
   
    print(f"!!! DIAGNOSTIC: get_ohlcv_data fetched {len(df)} rows for {symbol}!!!") 
    
    return df.sort_index()

def resample_and_store(raw_ticks: List[Dict[str, Any]], timeframe: str, symbol: str):
    """Processes raw ticks, resamples, and stores the resulting OHLCV bars."""
    if not raw_ticks:
        return
        
    df = pd.DataFrame(raw_ticks)
    df['time'] = pd.to_datetime(df['time'], unit='ms')
    
    
    df = df.set_index('time')
    df.index.name = 'timestamp' 

   
    ohlcv = df['price'].resample(timeframe).ohlc()
    volume = df['qty'].resample(timeframe).sum().fillna(0)
    
    resampled_df = ohlcv.join(volume.rename('volume')).dropna()
    
 
    store_ohlcv_data(resampled_df, symbol, timeframe)
    
    if not resampled_df.empty:
        latest_ts = resampled_df.index[-1].isoformat()
        print(f"--- [INGESTION SUCCESS] Stored {timeframe} bar for {symbol} ending at {latest_ts} ---")
    

init_db()