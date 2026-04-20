"""Centralized fundamental scoring logic for the 9-point investment checklist"""

from typing import Dict, Any, Tuple
import pandas as pd

def _safe_float_parse(val):
    """Local helper to prevent circular imports with src.utils"""
    if val is None or val == '' or val == 'N/A' or val == '-':
        return None
    try:
        if isinstance(val, (int, float)):
            return float(val)
        # Handle percentages and unit suffixes
        clean_val = str(val).replace('%', '').replace(',', '').strip()
        if not clean_val: return None
        
        multiplier = 1
        if clean_val.endswith('B'):
            multiplier = 1_000_000_000
            clean_val = clean_val[:-1]
        elif clean_val.endswith('M'):
            multiplier = 1_000_000
            clean_val = clean_val[:-1]
        elif clean_val.endswith('K'):
            multiplier = 1_000
            clean_val = clean_val[:-1]
            
        return float(clean_val) * multiplier
    except (ValueError, TypeError):
        return None

class ChecklistScorer:
    """Calculates the 9-point investment quality score for a ticker"""
    
    @staticmethod
    def calculate_score(analysis_data: Any) -> Tuple[int, int, Dict[str, bool]]:
        """
        Calculate score out of 9.
        Returns: (passed_count, total_points, details_dict)
        """
        details = {}
        pass_count = 0
        
        # Helper to safely parse and check
        def _get_val(key, data):
            if hasattr(data, 'finviz_data') and isinstance(data.finviz_data, dict):
                return data.finviz_data.get(key, '')
            if isinstance(data, dict):
                return data.get(key, '')
            return ''

        # 1. Market Cap >= 2B
        mc_str = _get_val('Market Cap', analysis_data)
        mc_val = _safe_float_parse(mc_str)
        details['Market Cap'] = mc_val is not None and mc_val >= 2_000_000_000
        
        # 2. Listed on US Exchange
        exchange = getattr(analysis_data, 'exchange', None)
        country = getattr(analysis_data, 'country', None)
        US_EXCHANGES = {'NMS', 'NGM', 'NCM', 'NYQ', 'ASE', 'PCX', 'BTS', 'NasdaqGS', 'NasdaqGM', 'NasdaqCM'}
        details['US Listing'] = (exchange in US_EXCHANGES) if exchange else (country in ['United States', 'USA'] if country else False)
        
        # 3. Analyst Recommendation Buy+
        details['Analyst Buy'] = False
        rec = getattr(analysis_data, 'analyst_recommendation', None)
        if rec:
            if isinstance(rec, (int, float)):
                details['Analyst Buy'] = rec <= 2.0 # 1.0 = Strong Buy, 2.0 = Buy
            elif isinstance(rec, str):
                details['Analyst Buy'] = rec.lower() in ['buy', 'strong_buy', 'strong buy', '1', '2']
        else:
            # Check Finviz data directly
            rec_str = _get_val('Recom', analysis_data)
            rec_val = _safe_float_parse(rec_str)
            if rec_val:
                details['Analyst Buy'] = rec_val <= 2.0
        
        # 4. Avg Volume >= 1M
        vol = getattr(analysis_data, 'average_volume', 0)
        details['Liquidity'] = vol is not None and vol >= 1_000_000
        
        # 5. ROE >= 15%
        roe_str = _get_val('ROE', analysis_data)
        roe_val = _safe_float_parse(roe_str)
        details['ROE'] = roe_val is not None and roe_val >= 15
        
        # 6. ROA >= 10%
        roa_str = _get_val('ROA', analysis_data)
        roa_val = _safe_float_parse(roa_str)
        details['ROA'] = roa_val is not None and roa_val >= 10
        
        # 7. EPS Growth Momentum
        eps_y = _safe_float_parse(_get_val('EPS this Y', analysis_data))
        eps_ny = _safe_float_parse(_get_val('EPS next Y', analysis_data))
        eps_5y = _safe_float_parse(_get_val('EPS next 5Y', analysis_data))
        details['EPS Growth'] = (
            (eps_y is not None and eps_y >= 10) or 
            (eps_ny is not None and eps_ny >= 10) or 
            (eps_5y is not None and eps_5y >= 8)
        )
        
        # 8. YoY Growth (Revenue/Earnings)
        rev_g = getattr(analysis_data, 'revenue_growth_yoy', None)
        eps_g = getattr(analysis_data, 'eps_growth_yoy', None)
        details['YoY Growth'] = (
            (rev_g is not None and rev_g >= 0.05) or 
            (eps_g is not None and eps_g >= 0.10)
        )
        
        # 9. Valuation (PE <= 30 OR PEG <= 2)
        pe_val = _safe_float_parse(_get_val('P/E', analysis_data))
        peg_val = _safe_float_parse(_get_val('PEG', analysis_data))
        # Handle PEG calculation if missing
        if peg_val is None and pe_val is not None and eps_5y is not None and eps_5y > 0:
            peg_val = pe_val / eps_5y
            
        details['Valuation'] = (
            (pe_val is not None and pe_val <= 30) or 
            (peg_val is not None and peg_val <= 2)
        )
        
        pass_count = sum(1 for v in details.values() if v)
        return pass_count, 9, details
