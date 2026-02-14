"""Backtesting engine for technical strategies"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

class BacktestEngine:
    """Simulates trading strategies on historical price data"""
    
    @staticmethod
    def run_ema_crossover(df: pd.DataFrame, short_ema: int = 20, long_ema: int = 50, initial_capital: float = 10000.0) -> Dict[str, Any]:
        """Test EMA Crossover strategy: Buy when short_ema > long_ema, sell otherwise"""
        data = df.copy()
        
        # Calculate EMAs
        data[f'short_ema'] = data['Close'].ewm(span=short_ema, adjust=False).mean()
        data[f'long_ema'] = data['Close'].ewm(span=long_ema, adjust=False).mean()
        
        # Generate Signals
        data['signal'] = 0.0
        data.iloc[short_ema:, data.columns.get_loc('signal')] = np.where(
            data['short_ema'].iloc[short_ema:] > data['long_ema'].iloc[short_ema:], 1.0, 0.0
        )
        data['position'] = data['signal'].diff()
        
        # Performance Tracking
        cash = initial_capital
        holdings = 0.0
        total_value = []
        
        for i, row in data.iterrows():
            if row['position'] == 1.0: # BUY
                if cash > 0:
                    holdings = cash / row['Close']
                    cash = 0
            elif row['position'] == -1.0: # SELL
                if holdings > 0:
                    cash = holdings * row['Close']
                    holdings = 0
            
            # Record total value at each step
            current_value = cash + (holdings * row['Close'])
            total_value.append(current_value)
            
        data['portfolio_value'] = total_value
        
        # Calculate Metrics
        final_value = total_value[-1]
        total_return = (final_value - initial_capital) / initial_capital * 100
        
        # Buy and Hold comparison
        bh_return = (data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0] * 100
        
        return {
            'data': data,
            'metrics': {
                'Final Value': f"${final_value:,.2f}",
                'Total Return': f"{total_return:.2f}%",
                'Buy & Hold Return': f"{bh_return:.2f}%",
                'Net Profit': f"${(final_value - initial_capital):,.2f}"
            }
        }

    @staticmethod
    def run_rsi_strategy(df: pd.DataFrame, oversold: int = 30, overbought: int = 70, initial_capital: float = 10000.0) -> Dict[str, Any]:
        """Buy when RSI crosses below oversold, sell when it crosses above overbought"""
        data = df.copy()
        
        # RSI Calculation (if not present)
        if 'RSI' not in data.columns:
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data['RSI'] = 100 - (100 / (1 + rs))
            
        # Strategy Logic
        cash = initial_capital
        holdings = 0.0
        total_value = []
        
        for i, row in data.iterrows():
            if row['RSI'] < oversold and cash > 0: # BUY
                holdings = cash / row['Close']
                cash = 0
            elif row['RSI'] > overbought and holdings > 0: # SELL
                cash = holdings * row['Close']
                holdings = 0
                
            total_value.append(cash + (holdings * row['Close']))
            
        data['portfolio_value'] = total_value
        
        final_value = total_value[-1]
        total_return = (final_value - initial_capital) / initial_capital * 100
        bh_return = (data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0] * 100
        
        return {
            'data': data,
            'metrics': {
                'Final Value': f"${final_value:,.2f}",
                'Total Return': f"{total_return:.2f}%",
                'Buy & Hold Return': f"{bh_return:.2f}%",
                'Net Profit': f"${(final_value - initial_capital):,.2f}"
            }
        }
