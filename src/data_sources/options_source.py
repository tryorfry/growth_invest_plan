"""Options data source for fetching implied volatility and options metrics"""

import yfinance as yf
import pandas as pd
from typing import Dict, Any, Optional, List
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

    def scan_unusual_activity(self, ticker: str, min_volume: int = 500, vol_oi_ratio: float = 3.0) -> List[Dict[str, Any]]:
        """
        Scan all available expiration dates for a ticker to find unusual options activity.
        Definition of Unusual: Volume > Open Interest * vol_oi_ratio AND Volume > min_volume
        
        Args:
            ticker: Stock ticker
            min_volume: Minimum contract volume to flag
            vol_oi_ratio: Multiplier for Vol/OI
            
        Returns:
            List of dictionaries containing unusual option prints.
        """
        results = []
        try:
            stock = yf.Ticker(ticker)
            expirations = stock.options
            
            if not expirations:
                return []
                
            current_price = stock.info.get('currentPrice', None) or stock.history(period="1d")['Close'].iloc[-1]
            
            for exp in expirations[:4]:  # Scan nearest 4 expirations to save API time
                chain = stock.option_chain(exp)
                
                for opt_type, data in [("Call", chain.calls), ("Put", chain.puts)]:
                    if data.empty:
                        continue
                        
                    # Calculate DTE (Days to Expiration)
                    exp_date = datetime.strptime(exp, "%Y-%m-%d")
                    dte = (exp_date - datetime.now()).days
                    
                    for _, row in data.iterrows():
                        vol = row.get('volume', 0)
                        oi = row.get('openInterest', 0)
                        
                        if pd.isna(vol) or pd.isna(oi):
                            continue
                            
                        # Rule for unusual activity
                        if vol > min_volume and (oi == 0 or (vol / oi) >= vol_oi_ratio):
                            # Calculate moneyness
                            strike = row['strike']
                            if opt_type == "Call":
                                otm_pct = ((strike - current_price) / current_price * 100) if strike > current_price else 0
                            else:
                                otm_pct = ((current_price - strike) / current_price * 100) if strike < current_price else 0
                                
                            premium = vol * row.get('lastPrice', 0) * 100
                            
                            results.append({
                                'type': opt_type,
                                'strike': strike,
                                'exp_date': exp,
                                'dte': max(0, dte),
                                'volume': int(vol),
                                'open_interest': int(oi) if oi > 0 else 0,
                                'vol_oi_ratio': round(vol / oi, 1) if oi > 0 else float('inf'),
                                'last_price': row.get('lastPrice', 0),
                                'implied_vol': row.get('impliedVolatility', 0),
                                'premium_est': premium,
                                'otm_pct': round(otm_pct, 1)
                            })
                            
            # Sort by highest premium
            results.sort(key=lambda x: x['premium_est'], reverse=True)
            return results
            
        except Exception as e:
            print(f"Error scanning unusual options for {ticker}: {e}")
            return []
