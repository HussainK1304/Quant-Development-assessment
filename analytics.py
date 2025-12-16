import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller

def compute_ols_beta(y: pd.Series, x: pd.Series) -> float:
    """Computes the Hedge Ratio (Beta) via OLS Regression."""
    # Ensure indices are aligned
    data = pd.DataFrame({'Y': y, 'X': x}).dropna()
    if data.empty:
        return 0.0
        
    
    X = sm.add_constant(data['X'])
    try:
        model = sm.OLS(data['Y'], X).fit()
        return model.params['X']
    except Exception:
        
        return 0.0

def compute_spread_zscore(y: pd.Series, x: pd.Series, window: int) -> pd.DataFrame:
    """Computes Spread and Rolling Z-Score."""
    beta = compute_ols_beta(y, x) 
    
    
    combined = pd.DataFrame({'Y': y, 'X': x}).dropna()
    spread = combined['Y'] - beta * combined['X']
    
    
    rolling_mean = spread.rolling(window=window).mean()
    rolling_std = spread.rolling(window=window).std()
    
    
    z_score = np.divide(spread - rolling_mean, rolling_std, 
                        out=np.full_like(spread, np.nan), where=rolling_std!=0)
    
    results = pd.DataFrame({
        'Spread': spread,
        'ZScore': z_score,
        'Beta': beta
    })
    return results

def run_adf_test(series: pd.Series) -> dict:
    """Performs the Augmented Dickey-Fuller test for stationarity."""
    if len(series) < 10:
        return {
            'Test Statistic': np.nan,
            'p-value': np.nan,
            'Critical Values': {},
            'Result': "Insufficient data points"
        }
        
    result = adfuller(series.dropna())
    

    result_str = 'Stationary (Reject Null Hypothesis)' if result[1] < 0.05 else 'Non-Stationary (Fail to Reject Null Hypothesis)'
    
    return {
        'Test Statistic': result[0],
        'p-value': result[1],
        'Lags Used': result[2],
        'Number of Observations': result[3],
        'Critical Values': result[4],
        'Result': result_str
    }