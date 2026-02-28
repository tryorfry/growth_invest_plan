"""Backtesting engine for technical strategies"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

class BacktestEngine:
    """Simulates trading strategies on historical price data"""
    
    @staticmethod
    def _calculate_metrics(data: pd.DataFrame, trades: List[Dict[str, float]], initial_capital: float) -> Dict[str, Any]:
        """Calculate advanced backtest metrics"""
        total_value = data['portfolio_value']
        final_value = total_value.iloc[-1]
        
        # Total / B&H Return
        total_return = (final_value - initial_capital) / initial_capital * 100
        bh_return = (data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0] * 100
        net_profit = final_value - initial_capital
        
        # Drawdown
        rolling_max = total_value.cummax()
        drawdown = (total_value - rolling_max) / rolling_max * 100
        max_drawdown = drawdown.min()
        data['drawdown'] = drawdown
        
        # Trade Metrics (Win Rate & Profit Factor)
        wins = 0
        losses = 0
        gross_profit = 0.0
        gross_loss = 0.0
        
        for trade in trades:
            if trade['type'] == 'sell':
                pnl = trade['price'] - trade['buy_price']
                if pnl > 0:
                    wins += 1
                    gross_profit += pnl
                else:
                    losses += 1
                    gross_loss += abs(pnl)
                    
        total_trades = wins + losses
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf') if gross_profit > 0 else 0
        
        return {
            'Final Value': f"${final_value:,.2f}",
            'Total Return': f"{total_return:.2f}%",
            'Buy & Hold Return': f"{bh_return:.2f}%",
            'Max Drawdown': f"{max_drawdown:.2f}%",
            'Win Rate': f"{win_rate:.1f}% ({wins}W/{losses}L)",
            'Profit Factor': f"{profit_factor:.2f}x",
            'Net Profit': f"${net_profit:,.2f}"
        }

    @staticmethod
    def run_ema_crossover(df: pd.DataFrame, short_ema: int = 20, long_ema: int = 50, initial_capital: float = 10000.0) -> Dict[str, Any]:
        """Test EMA Crossover strategy: Buy when short_ema > long_ema, sell otherwise"""
        data = df.copy()
        
        data[f'short_ema'] = data['Close'].ewm(span=short_ema, adjust=False).mean()
        data[f'long_ema'] = data['Close'].ewm(span=long_ema, adjust=False).mean()
        
        data['signal'] = 0.0
        data.iloc[short_ema:, data.columns.get_loc('signal')] = np.where(
            data['short_ema'].iloc[short_ema:] > data['long_ema'].iloc[short_ema:], 1.0, 0.0
        )
        data['position'] = data['signal'].diff()
        
        return BacktestEngine._simulate_trades(data, initial_capital)

    @staticmethod
    def run_rsi_strategy(df: pd.DataFrame, oversold: int = 30, overbought: int = 70, initial_capital: float = 10000.0) -> Dict[str, Any]:
        """Buy when RSI crosses below oversold, sell when it crosses above overbought"""
        data = df.copy()
        
        if 'RSI' not in data.columns:
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data['RSI'] = 100 - (100 / (1 + rs))
            
        data['signal'] = 0.0
        # Buy signal logic (1 when RSI < oversold, 0 when RSI > overbought, forward fill otherwise)
        signal_arr = np.zeros(len(data))
        current_signal = 0.0
        rsi_vals = data['RSI'].values
        for i in range(len(rsi_vals)):
            if rsi_vals[i] < oversold:
                current_signal = 1.0
            elif rsi_vals[i] > overbought:
                current_signal = 0.0
            signal_arr[i] = current_signal
            
        data['signal'] = signal_arr
        data['position'] = data['signal'].diff()
        
        return BacktestEngine._simulate_trades(data, initial_capital)
        
    @staticmethod
    def run_combined_strategy(df: pd.DataFrame, initial_capital: float = 10000.0) -> Dict[str, Any]:
        """Alpha Strategy: Buy when EMA20 > EMA50 AND RSI < 40 (pullback in uptrend)"""
        data = df.copy()
        
        data['EMA20'] = data['Close'].ewm(span=20, adjust=False).mean()
        data['EMA50'] = data['Close'].ewm(span=50, adjust=False).mean()
        
        if 'RSI' not in data.columns:
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data['RSI'] = 100 - (100 / (1 + rs))
            
        signal_arr = np.zeros(len(data))
        current_signal = 0.0
        
        for i in range(len(data)):
            # Buy logic
            if data['EMA20'].iloc[i] > data['EMA50'].iloc[i] and data['RSI'].iloc[i] < 45:
                current_signal = 1.0
            # Sell logic
            elif data['RSI'].iloc[i] > 70 or data['EMA20'].iloc[i] < data['EMA50'].iloc[i]:
                current_signal = 0.0
                
            signal_arr[i] = current_signal
            
        data['signal'] = signal_arr
        data['position'] = data['signal'].diff()
        
        return BacktestEngine._simulate_trades(data, initial_capital)

    @staticmethod
    def _simulate_trades(data: pd.DataFrame, initial_capital: float) -> Dict[str, Any]:
        """Internal simulator over calculated positions to generate logs and metrics"""
        cash = initial_capital
        holdings = 0.0
        total_value = []
        trades = []
        last_buy_price = 0.0
        
        for i, row in data.iterrows():
            if row['position'] == 1.0: # BUY
                if cash > 0:
                    holdings = cash / row['Close']
                    cash = 0
                    last_buy_price = row['Close']
                    trades.append({'date': i, 'type': 'buy', 'price': row['Close']})
                    
            elif row['position'] == -1.0: # SELL
                if holdings > 0:
                    cash = holdings * row['Close']
                    holdings = 0
                    trades.append({'date': i, 'type': 'sell', 'price': row['Close'], 'buy_price': last_buy_price})
            
            current_value = cash + (holdings * row['Close'])
            total_value.append(current_value)
            
        data['portfolio_value'] = total_value
        metrics = BacktestEngine._calculate_metrics(data, trades, initial_capital)
        
        return {
            'data': data,
            'metrics': metrics,
            'trades': trades
        }
