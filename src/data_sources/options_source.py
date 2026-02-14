"""Options data source for fetching implied volatility and options metrics"""

import yfinance as yf
from typing import Dict, Any, Optional
from datetime import datetime


class OptionsSource:
    """Fetch options data and calculate metrics"""
    
    def fetch_options_data(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch options data for a stock.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with options metrics
        """
        try:
            stock = yf.Ticker(ticker)
            
            # Get options expiration dates
            expirations = stock.options
            if not expirations:
                return {}
            
            # Use the nearest expiration
            nearest_exp = expirations[0]
            
            # Get options chain
            opt_chain = stock.option_chain(nearest_exp)
            calls = opt_chain.calls
            puts = opt_chain.puts
            
            # Calculate put/call ratio
            put_volume = puts['volume'].sum() if 'volume' in puts.columns else 0
            call_volume = calls['volume'].sum() if 'volume' in calls.columns else 0
            put_call_ratio = put_volume / call_volume if call_volume > 0 else 0
            
            # Get implied volatility (average of ATM options)
            current_price = stock.info.get('currentPrice', 0)
            
            # Find ATM calls
            atm_calls = calls[abs(calls['strike'] - current_price) < current_price * 0.05]
            avg_iv_calls = atm_calls['impliedVolatility'].mean() if not atm_calls.empty else 0
            
            # Find ATM puts
            atm_puts = puts[abs(puts['strike'] - current_price) < current_price * 0.05]
            avg_iv_puts = atm_puts['impliedVolatility'].mean() if not atm_puts.empty else 0
            
            avg_iv = (avg_iv_calls + avg_iv_puts) / 2 if (avg_iv_calls > 0 and avg_iv_puts > 0) else 0
            
            return {
                'implied_volatility': avg_iv,
                'put_call_ratio': put_call_ratio,
                'nearest_expiration': nearest_exp,
                'total_call_volume': call_volume,
                'total_put_volume': put_volume,
                'fetched_at': datetime.now()
            }
            
        except Exception as e:
            print(f"Error fetching options data for {ticker}: {e}")
            return {}
