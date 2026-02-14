"""Valuation models for intrinsic value calculation"""

import math
from typing import Dict, Any, Optional
from .analyzer import StockAnalysis

class ValuationCalculator:
    """Calculates intrinsic value using various financial models"""
    
    @staticmethod
    def calculate_graham_number(analysis: StockAnalysis) -> Optional[float]:
        """
        Calculate the Graham Number.
        Formula: sqrt(22.5 * EPS * BookValue)
        """
        eps = analysis.basic_eps
        book_value = analysis.book_value
        
        if eps is None or book_value is None or eps <= 0 or book_value <= 0:
            return None
            
        try:
            return math.sqrt(22.5 * eps * book_value)
        except (ValueError, ZeroDivisionError):
            return None

    @staticmethod
    def calculate_dcf(analysis: StockAnalysis, growth_rate: Optional[float] = None, discount_rate: float = 0.10, years: int = 5) -> Optional[Dict[str, Any]]:
        """
        Calculate intrinsic value using a simplified DCF model.
        
        Args:
            analysis: StockAnalysis object
            growth_rate: Custom growth rate (optional, otherwise use analysis.earnings_growth)
            discount_rate: Required rate of return (default 10%)
            years: Projection horizon
            
        Returns:
            Dictionary with intrinsic value and breakdown or None
        """
        fcf = analysis.free_cash_flow
        shares = analysis.shares_outstanding
        debt = analysis.total_debt or 0
        cash = analysis.total_cash or 0
        
        # Determine growth rate (if not provided, use earnings_growth or a conservative 5%)
        if growth_rate is None:
            growth_rate = analysis.earnings_growth or 0.05
            
        # Cap high growth rates for safety in terminal value
        growth_rate = min(growth_rate, 0.25)
        
        if fcf is None or shares is None or fcf <= 0 or shares <= 0:
            return None
            
        try:
            # 1. Project Cash Flows
            projected_fcfs = []
            present_values = []
            
            current_fcf = fcf
            for i in range(1, years + 1):
                current_fcf *= (1 + growth_rate)
                projected_fcfs.append(current_fcf)
                
                pv = current_fcf / ((1 + discount_rate) ** i)
                present_values.append(pv)
            
            # 2. Terminal Value (using 2% perpetual growth)
            perpetual_growth = 0.02
            terminal_value = projected_fcfs[-1] * (1 + perpetual_growth) / (discount_rate - perpetual_growth)
            terminal_pv = terminal_value / ((1 + discount_rate) ** years)
            
            # 3. Enterprise Value
            enterprise_value = sum(present_values) + terminal_pv
            
            # 4. Equity Value (EV + Cash - Debt)
            equity_value = enterprise_value + cash - debt
            
            # 5. Value per Share
            intrinsic_value = equity_value / shares
            
            return {
                "intrinsic_value": intrinsic_value,
                "enterprise_value": enterprise_value,
                "equity_value": equity_value,
                "growth_rate_used": growth_rate,
                "discount_rate_used": discount_rate,
                "projected_fcf": projected_fcfs
            }
        except Exception as e:
            print(f"Error calculating DCF: {e}")
            return None
