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
        if clean_val.endswith('T'):
            multiplier = 1_000_000_000_000
            clean_val = clean_val[:-1]
        elif clean_val.endswith('B'):
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
    def calculate_score(analysis_data: Any) -> Tuple[int, int, Dict[str, Dict[str, Any]]]:
        """
        Calculate score out of 9.
        Returns: (passed_count, total_points, details_dict)
        where details_dict is { "Point Name": {"pass": bool, "label": "display string"} }
        """
        details = {}
        
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
        mc_pass = mc_val is not None and mc_val >= 2_000_000_000
        details['Market Cap'] = {"pass": mc_pass, "label": f"Market Cap >= 2B? ({mc_str or 'N/A'})"}
        
        # 2. Listed on US Exchange
        exchange = getattr(analysis_data, 'exchange', None)
        country = getattr(analysis_data, 'country', None)
        US_EXCHANGES = {'NMS', 'NGM', 'NCM', 'NYQ', 'ASE', 'PCX', 'BTS', 'NasdaqGS', 'NasdaqGM', 'NasdaqCM'}
        us_listed = (exchange in US_EXCHANGES) if exchange else (country in ['United States', 'USA'] if country else False)
        listing_info = f"exchange: {exchange}" if exchange else f"country: {country or 'N/A'}"
        details['US Listing'] = {"pass": us_listed, "label": f"Listed on US exchange? ({listing_info})"}
        
        # 3. Analyst Recommendation Buy+
        details['Analyst Buy'] = {"pass": False, "label": "Analyst Recommendation Buy+"}
        rec = getattr(analysis_data, 'analyst_recommendation', None)
        rec_label = str(rec) if rec else "N/A"
        if rec:
            if isinstance(rec, (int, float)):
                details['Analyst Buy'] = {"pass": rec <= 2.0, "label": f"Analyst Buy or Better? ({rec})"}
            elif isinstance(rec, str):
                details['Analyst Buy'] = {"pass": rec.lower() in ['buy', 'strong_buy', 'strong buy', '1', '2'], "label": f"Analyst Buy or Better? ({rec})"}
        else:
            rec_str = _get_val('Recom', analysis_data)
            rec_val = _safe_float_parse(rec_str)
            if rec_val:
                details['Analyst Buy'] = {"pass": rec_val <= 2.0, "label": f"Analyst Buy or Better? ({rec_str})"}
            else:
                details['Analyst Buy'] = {"pass": False, "label": "Analyst Recommendation Meta Missing"}
        
        # 4. Avg Volume >= 1M
        vol = getattr(analysis_data, 'average_volume', 0)
        vol_str = f"{int(vol):,}" if vol and isinstance(vol, (int, float)) else str(vol or '0')
        details['Liquidity'] = {"pass": vol is not None and vol >= 1_000_000, "label": f"Avg Volume >= 1M? ({vol_str})"}
        
        # 5. ROE >= 15%
        roe_str = _get_val('ROE', analysis_data)
        roe_val = _safe_float_parse(roe_str)
        details['ROE'] = {"pass": roe_val is not None and roe_val >= 15, "label": f"ROE >= 15%? ({roe_str or 'N/A'})"}
        
        # 6. ROA >= 10%
        roa_str = _get_val('ROA', analysis_data)
        roa_val = _safe_float_parse(roa_str)
        details['ROA'] = {"pass": roa_val is not None and roa_val >= 10, "label": f"ROA >= 10%? ({roa_str or 'N/A'})"}
        
        # 7. EPS Growth Momentum
        eps_y_str = _get_val('EPS this Y', analysis_data)
        eps_ny_str = _get_val('EPS next Y', analysis_data)
        eps_5y_str = _get_val('EPS next 5Y', analysis_data)
        eps_y = _safe_float_parse(eps_y_str)
        eps_ny = _safe_float_parse(eps_ny_str)
        eps_5y = _safe_float_parse(eps_5y_str)
        
        eps_pass = (eps_y is not None and eps_y >= 10) or (eps_ny is not None and eps_ny >= 10) or (eps_5y is not None and eps_5y >= 8)
        details['EPS Growth'] = {"pass": eps_pass, "label": f"EPS Growth >= 10% (Y:{eps_y_str}, NY:{eps_ny_str}, 5Y:{eps_5y_str})"}
        
        # 8. YoY Growth (Revenue/Earnings)
        rev_g = getattr(analysis_data, 'revenue_growth_yoy', None)
        eps_g = getattr(analysis_data, 'eps_growth_yoy', None)
        rev_g_str = f"{rev_g*100:.1f}%" if rev_g is not None else "N/A"
        eps_g_str = f"{eps_g*100:.1f}%" if eps_g is not None else "N/A"
        
        details['YoY Growth'] = {"pass": (rev_g is not None and rev_g >= 0.05) or (eps_g is not None and eps_g >= 0.10), 
                                 "label": f"YoY Growth (Rev:{rev_g_str}, EPS:{eps_g_str})"}
        
        # 9. Valuation (PE <= 30 OR PEG <= 2)
        pe_str = _get_val('P/E', analysis_data)
        peg_str = _get_val('PEG', analysis_data)
        pe_val = _safe_float_parse(pe_str)
        peg_val = _safe_float_parse(peg_str)
        
        if peg_val is None and pe_val is not None and eps_5y is not None and eps_5y > 0:
            peg_val = pe_val / eps_5y
            peg_str = f"{peg_val:.2f} (calc)"
            
        val_pass = (pe_val is not None and pe_val <= 30) or (peg_val is not None and peg_val <= 2)
        details['Valuation'] = {"pass": val_pass, "label": f"P/E <= 30 ({pe_str or 'N/A'}) OR PEG <= 2 ({peg_str or 'N/A'})"}
        
        pass_count = sum(1 for v in details.values() if v["pass"])
        return pass_count, 9, details
