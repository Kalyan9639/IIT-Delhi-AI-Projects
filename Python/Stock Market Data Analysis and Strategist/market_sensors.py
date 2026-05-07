import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import norm

class MarketSensors:
    """
    Laser-focused on a single problem: TCS (Tata Consultancy Services) 
    as the proxy for the Indian IT Sector's health.
    """
    def __init__(self, ticker="TCS.NS"):
        self.ticker = ticker # Focused entirely on a single asset

    def get_market_snapshot(self, period="5d", interval="60m"):
        """
        Fetches historical data to calculate returns and current volatility for the single asset.
        """
        try:
            # Download just the single ticker
            data = yf.download(self.ticker, period=period, interval=interval)
            
            # yfinance returns a MultiIndex column sometimes, let's safely grab 'Close'
            if isinstance(data.columns, pd.MultiIndex):
                df = data['Close'][self.ticker].dropna()
            else:
                df = data['Close'].dropna()

            if df.empty:
                raise ValueError("No price data retrieved from Yahoo Finance.")
            
            # Calculate Hourly Returns (%)
            returns = df.pct_change().dropna()
            current_price = df.iloc[-1]
            last_return = returns.iloc[-1]
            
            # Statistical Math: Mean and Std Dev of returns
            mu = np.mean(returns)
            sigma = np.std(returns)
            
            # Z-Score: How many standard deviations is the current movement?
            z_score = (last_return - mu) / sigma if sigma != 0 else 0
            
            # Probablity Density (for the Bell Curve visualization)
            x_axis = np.linspace(mu - 4*sigma, mu + 4*sigma, 100)
            y_axis = norm.pdf(x_axis, mu, sigma)
            
            # Return a strictly formatted dictionary for this specific stock
            return {
                self.ticker: {
                    "price": round(float(current_price), 2),
                    "last_return_pct": round(float(last_return * 100), 2),
                    "z_score": round(float(z_score), 2),
                    # FIXED: Explicitly cast numpy.bool_ to standard Python bool
                    "is_anomaly": bool(abs(z_score) > 2.0), 
                    "curve_data": {"x": x_axis.tolist(), "y": y_axis.tolist(), "current_x": float(last_return)}
                }
            }
        except Exception as e:
            print(f"YFinance Sensor Error: {e}")
            # Fallback to prevent app crash
            return {
                self.ticker: {
                    "price": 0.0, "last_return_pct": 0.0, "z_score": 0.0,
                    "is_anomaly": False,
                    "curve_data": {"x": [0], "y": [0], "current_x": 0}
                }
            }