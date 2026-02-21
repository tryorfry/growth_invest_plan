"""Mathematical models for probability and simulations"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple

class MonteCarloEngine:
    """Runs Monte Carlo simulations using Geometric Brownian Motion (GBM)"""
    
    @staticmethod
    def simulate_gbm(current_price: float, history: pd.DataFrame, days_out: int = 30, num_simulations: int = 10000) -> Dict[str, Any]:
        """
        Simulate future price paths using historical daily returns.
        
        Args:
            current_price (float): Starting price for the simulation.
            history (pd.DataFrame): DataFrame containing at least a 'Close' column of historical prices.
            days_out (int): Number of trading days to project forward.
            num_simulations (int): Number of Monte Carlo paths to generate.
            
        Returns:
            Dict containing the paths matrix, percentiles, expected value, and the historical metrics used.
        """
        if history is None or history.empty or 'Close' not in history.columns or len(history) < 30:
            return None
            
        # Calculate trailing daily returns
        closes = history['Close']
        daily_returns = closes.pct_change().dropna()
        
        # Calculate drift and volatility parameters
        mu = daily_returns.mean()
        sigma = daily_returns.std()
        
        # Set up variables for simulation
        dt = 1 # 1 day
        
        # Generate random shocks: Z ~ N(0, 1) matrix of size (days_out, num_simulations)
        # Using numpy vectorized operations for speed
        np.random.seed(42) # For reproducibility in displays
        Z = np.random.normal(loc=0.0, scale=1.0, size=(days_out, num_simulations))
        
        # Calculate daily drift (adjusted for volatility drag)
        daily_drift = mu - (0.5 * sigma**2)
        
        # Calculate daily step multiplier for each path
        daily_steps = np.exp(daily_drift * dt + sigma * np.sqrt(dt) * Z)
        
        # Initialize paths matrix
        # Row 0 is the current price
        paths = np.zeros((days_out + 1, num_simulations))
        paths[0] = current_price
        
        # Compute cumulative product across the columns to trace the price paths
        for t in range(1, days_out + 1):
            paths[t] = paths[t-1] * daily_steps[t-1]
            
        # Extract the final prices (the last row of the paths matrix)
        final_prices = paths[-1]
        
        # Calculate important percentiles (5th, 25th, 50th, 75th, 95th)
        percentiles = {
            "p5": float(np.percentile(final_prices, 5)),
            "p25": float(np.percentile(final_prices, 25)),
            "p50": float(np.percentile(final_prices, 50)),
            "p75": float(np.percentile(final_prices, 75)),
            "p95": float(np.percentile(final_prices, 95))
        }
        
        # Get probability of being above current price
        prob_higher = float(np.mean(final_prices > current_price))
        
        return {
            "paths": paths,                # Array of shape (days_out + 1, num_simulations)
            "final_prices": final_prices,  # 1D array of the final endpoints
            "percentiles": percentiles,
            "expected_value": float(np.mean(final_prices)),
            "prob_higher": prob_higher,
            "metrics": {
                "daily_mean_return": float(mu),
                "daily_volatility": float(sigma),
                "days_out": days_out,
                "num_simulations": num_simulations
            }
        }
