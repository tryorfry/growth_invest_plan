"""Mathematical models for Options Pricing"""

import math
from typing import Dict, Any

class OptionsProfitCalculator:
    """Calculates theoretical Options pricing using the Black-Scholes Model"""
    
    @staticmethod
    def norm_cdf(x: float) -> float:
        """Standard normal cumulative distribution function"""
        return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0
        
    @staticmethod
    def norm_pdf(x: float) -> float:
        """Standard normal probability density function"""
        return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)
        
    @classmethod
    def black_scholes(cls, S: float, K: float, T: float, r: float, sigma: float, option_type: str = 'call') -> float:
        """
        Calculate the theoretical price of a European option.
        
        Args:
            S (float): Current stock price
            K (float): Strike price
            T (float): Time to expiration in years (e.g., 30 days = 30/365)
            r (float): Risk-free interest rate (e.g., 0.05 for 5%)
            sigma (float): Implied Volatility (e.g., 0.20 for 20%)
            option_type (str): 'call' or 'put'
            
        Returns:
            float: Theoretical option price
        """
        # Edge cases
        if T <= 0:
            if option_type == 'call':
                return max(0.0, S - K)
            return max(0.0, K - S)
        if sigma <= 0:
            return 0.0
            
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        if option_type == 'call':
            price = S * cls.norm_cdf(d1) - K * math.exp(-r * T) * cls.norm_cdf(d2)
        elif option_type == 'put':
            price = K * math.exp(-r * T) * cls.norm_cdf(-d2) - S * cls.norm_cdf(-d1)
        else:
            raise ValueError("option_type must be 'call' or 'put'")
            
        return price
        
    @classmethod
    def calculate_greeks(cls, S: float, K: float, T: float, r: float, sigma: float, option_type: str = 'call') -> Dict[str, float]:
        """Calculate Option Greeks (Delta, Gamma, Theta, Vega, Rho)"""
        if T <= 0 or sigma <= 0:
            return {"delta": 0.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0, "rho": 0.0}
            
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        # Gamma and Vega are the same for calls and puts
        gamma = cls.norm_pdf(d1) / (S * sigma * math.sqrt(T))
        vega = S * cls.norm_pdf(d1) * math.sqrt(T) / 100.0  # divided by 100 for 1% change format
        
        if option_type == 'call':
            delta = cls.norm_cdf(d1)
            theta_term1 = -(S * cls.norm_pdf(d1) * sigma) / (2 * math.sqrt(T))
            theta_term2 = r * K * math.exp(-r * T) * cls.norm_cdf(d2)
            theta = (theta_term1 - theta_term2) / 365.0  # Daily theta
            rho = (K * T * math.exp(-r * T) * cls.norm_cdf(d2)) / 100.0
        else:
            delta = cls.norm_cdf(d1) - 1.0
            theta_term1 = -(S * cls.norm_pdf(d1) * sigma) / (2 * math.sqrt(T))
            theta_term2 = r * K * math.exp(-r * T) * cls.norm_cdf(-d2)
            theta = (theta_term1 + theta_term2) / 365.0  # Daily theta
            rho = (-K * T * math.exp(-r * T) * cls.norm_cdf(-d2)) / 100.0
            
        return {
            "delta": delta,
            "gamma": gamma,
            "theta": theta,
            "vega": vega,
            "rho": rho
        }

    @classmethod
    def generate_pl_curve(cls, entry_price: float, target_price: float, current_iv: float, 
                          days_to_exp: int = 30, risk_free_rate: float = 0.042) -> Dict[str, Any]:
        """
        Generate a theoretical P/L curve data set for a recommended Call Option based on Growth Targets.
        Automatically recommends a slightly Out-Of-The-Money (OTM) strike price by default.
        """
        # Suggest a strike ~5% above entry
        suggested_strike = round(entry_price * 1.05, 2)
        T = days_to_exp / 365.0
        
        # Provide a default IV if we don't have one
        if not current_iv or current_iv <= 0:
            current_iv = 0.30  # Default 30% Vol
            
        # Current Theoretical Price
        current_option_price = cls.black_scholes(
            S=entry_price, K=suggested_strike, T=T, r=risk_free_rate, sigma=current_iv, option_type='call'
        )
        current_cost = current_option_price * 100  # 1 Option Contract = 100 shares
        
        # Plot curve varying the underlying asset price from -20% to +30%
        prices = []
        profits = []
        
        min_price = entry_price * 0.8
        max_price = max(target_price * 1.1, entry_price * 1.3)
        step = (max_price - min_price) / 40.0
        
        curr_p = min_price
        while curr_p <= max_price:
            # Theoretical price assuming we hold until 1 week before expiration 
            # (so theta decay has happened, T = 7/365)
            # OR we can just show P/L AT expiration
            eval_T = 7.0 / 365.0
            opt_price_at_target_date = cls.black_scholes(
                S=curr_p, K=suggested_strike, T=eval_T, r=risk_free_rate, sigma=current_iv, option_type='call'
            )
            
            pl_dollars = (opt_price_at_target_date * 100) - current_cost
            
            prices.append(curr_p)
            profits.append(pl_dollars)
            curr_p += step
            
        return {
            "suggested_strike": suggested_strike,
            "days_to_expiration": days_to_exp,
            "contract_cost": current_cost,
            "implied_volatility": current_iv,
            "risk_free_rate": risk_free_rate,
            "curve_prices": prices,
            "curve_profit_loss": profits
        }
