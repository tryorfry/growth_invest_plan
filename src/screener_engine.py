"""Screener engine to filter stocks based on growth parameters"""

from typing import List, Dict, Any, Tuple
from src.models import Analysis
from src.analyzer import StockAnalysis

def _safe_float_parse(val) -> float:
    try:
        if isinstance(val, str):
            clean_val = val.replace('%', '').replace(',', '').strip()
            return float(clean_val)
        return float(val) if val is not None else None
    except (ValueError, TypeError):
        return None

class ScreenerEngine:
    """Evaluates StockAnalysis objects against growth criteria"""
    
    @staticmethod
    def evaluate(analysis: StockAnalysis) -> Tuple[bool, int, int, List[str]]:
        """
        Evaluate an analysis against strict growth criteria.
        Returns:
            (is_passing, score, max_score, list_of_reasons)
        """
        score = 0
        max_score = 9
        reasons = []
        
        # 1. Market Cap > 2B
        mc_str = analysis.finviz_data.get('Market Cap', '')
        mc_pass = False
        if mc_str.endswith('B'):
            try:
                if float(mc_str[:-1]) >= 2.0:
                    mc_pass = True
            except:
                pass
        elif mc_str.endswith('T'):
            mc_pass = True
            
        if mc_pass:
            score += 1
        else:
            reasons.append("Market Cap < 2B")
            
        # 2. Analyst Recommendation (Buy/Strong Buy)
        rec = getattr(analysis, 'analyst_recommendation', '')
        if rec in ['buy', 'strong_buy']:
            score += 1
        else:
            reasons.append("Analyst Rec not Buy")
            
        # 3. Volume > 1M
        vol = getattr(analysis, 'average_volume', 0)
        if vol is not None and vol >= 1_000_000:
            score += 1
        else:
            reasons.append("Volume < 1M")
            
        # 4. ROE >= 15%
        roe_val = _safe_float_parse(analysis.finviz_data.get('ROE', ''))
        if roe_val is not None and roe_val >= 15:
            score += 1
        else:
            reasons.append("ROE < 15%")
            
        # 5. ROA >= 10%
        roa_val = _safe_float_parse(analysis.finviz_data.get('ROA', ''))
        if roa_val is not None and roa_val >= 10:
            score += 1
        else:
            reasons.append("ROA < 10%")
            
        # 6. EPS Growth (Current & Next Year >= 10%)
        eps_y_val = _safe_float_parse(analysis.finviz_data.get('EPS this Y', ''))
        eps_ny_val = _safe_float_parse(analysis.finviz_data.get('EPS next Y', ''))
        if (eps_y_val is not None and eps_y_val >= 10) and (eps_ny_val is not None and eps_ny_val >= 10):
            score += 1
        else:
            reasons.append("EPS Growth < 10%")
            
        # 7. Revenue & Op Income YoY >= 5%
        rev_g = getattr(analysis, 'revenue_growth_yoy', None)
        op_g = getattr(analysis, 'op_income_growth_yoy', None)
        if (rev_g is not None and rev_g >= 0.05) and (op_g is not None and op_g >= 0.05):
            score += 1
        else:
            reasons.append("Rev/OpInc Growth < 5%")
            
        # 8. Valuation (P/E < 30 OR PEG < 2)
        pe_val = _safe_float_parse(analysis.finviz_data.get('P/E', ''))
        peg_val = _safe_float_parse(analysis.finviz_data.get('PEG', ''))
        if (pe_val is not None and pe_val <= 30) or (peg_val is not None and peg_val <= 2):
            score += 1
        else:
            reasons.append("P/E > 30 and PEG > 2")
            
        # 9. Risk/Reward >= 1.5 (From setup_notes)
        rr_pass = False
        setup_notes = getattr(analysis, 'setup_notes', [])
        for note in setup_notes:
            if "Risk/Reward Ratio is" in note and "✅" in note:
                rr_pass = True
            if "Blue Sky" in note and "✅" in note:
                rr_pass = True
                
        if rr_pass:
            score += 1
        else:
            reasons.append("Poor Risk/Reward or Resistance Ceiling")
            
        # Determination: Pass if score >= 7 and RR passes
        is_passing = (score >= 7) and rr_pass
        
        return is_passing, score, max_score, reasons
