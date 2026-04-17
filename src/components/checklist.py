import streamlit as st
from src.analyzer import StockAnalysis
from src.utils import _safe_float_parse

def render_checklist(analysis: StockAnalysis):
    """Render the Investment Checklist in the dashboard"""
    st.divider()
    st.subheader("✅ Investment Checklist")
    
    def _chk(text: str, passed: bool):
        icon = "✅" if passed else "⚠️"
        st.markdown(f"{icon} **{text}**")

    # 1. Market Cap >= 2B
    mc_str = analysis.finviz_data.get('Market Cap', '')
    mc_val = _safe_float_parse(mc_str)
    mc_pass = mc_val is not None and mc_val >= 2_000_000_000
    _chk(f"Market Cap >= 2 B? ({mc_str})", mc_pass)
    
    # 2. Listed on a US exchange?
    exchange = getattr(analysis, 'exchange', None)
    country = getattr(analysis, 'country', None)
    US_EXCHANGES = {
        'NMS', 'NGM', 'NCM', 'NYQ', 'ASE', 'PCX', 'BTS', 
        'NasdaqGS', 'NasdaqGM', 'NasdaqCM'
    }
    us_listed = (exchange in US_EXCHANGES) if exchange else (country in ['United States', 'USA'] if country else False)
    listing_label = f"exchange: {exchange}" if exchange else f"country: {country or 'N/A'}"
    _chk(f"Listed on US exchange? ({listing_label})", us_listed)
    
    # 3. Analyst recommendation Buy or Better
    rec = getattr(analysis, 'analyst_recommendation', '')
    rec_pass = rec in ['buy', 'strong_buy'] if rec else False
    _chk(f"Analyst recommendation Buy or Better? ({rec or 'N/A'})", rec_pass)
    
    # 4. Average volume >= 1M
    vol = getattr(analysis, 'average_volume', 0)
    vol_pass = vol is not None and vol >= 1_000_000
    vol_str = f"{int(vol):,}" if vol else "N/A"
    _chk(f"Average volume >= 1 million? ({vol_str})", vol_pass)
    
    # 5. ROE
    roe_str = analysis.finviz_data.get('ROE', '')
    roe_val = _safe_float_parse(roe_str)
    roe_good = roe_val is not None and roe_val >= 15
    roe_badge = " ⭐ (Very Good)" if roe_val is not None and roe_val >= 20 else ""
    _chk(f"ROE >= 15%{roe_badge} ({roe_str})", roe_good)
    
    # 6. ROA
    roa_str = analysis.finviz_data.get('ROA', '')
    roa_val = _safe_float_parse(roa_str)
    roa_good = roa_val is not None and roa_val >= 10
    roa_badge = " ⭐ (Very Good)" if roa_val is not None and roa_val >= 20 else ""
    _chk(f"ROA >= 10%{roa_badge} ({roa_str})", roa_good)
    
    # 7. EPS Growth
    eps_y_str = analysis.finviz_data.get('EPS this Y', '')
    eps_y_val = _safe_float_parse(eps_y_str)
    _chk(f"EPS growth this year >= 10% ({eps_y_str})", eps_y_val is not None and eps_y_val >= 10)
    
    eps_ny_str = analysis.finviz_data.get('EPS next Y', '')
    eps_ny_val = _safe_float_parse(eps_ny_str)
    _chk(f"EPS growth next year >= 10% ({eps_ny_str})", eps_ny_val is not None and eps_ny_val >= 10)
    
    eps_5y_str = analysis.finviz_data.get('EPS next 5Y', '')
    eps_5y_val = _safe_float_parse(eps_5y_str)
    _chk(f"EPS growth 5 year >= 8% ({eps_5y_str})", eps_5y_val is not None and eps_5y_val >= 8)
    
    # 8. Revenue & Earnings YoY
    rev_g = getattr(analysis, 'revenue_growth_yoy', None)
    op_g = getattr(analysis, 'op_income_growth_yoy', None)
    eps_g = getattr(analysis, 'eps_growth_yoy', None)
    
    _chk(f"Revenue YoY growth >= 5%? ({f'{rev_g*100:.2f}%' if rev_g is not None else 'N/A'})", rev_g is not None and rev_g >= 0.05)
    _chk(f"Operating income YoY growth >= 5%? ({f'{op_g*100:.2f}%' if op_g is not None else 'N/A'})", op_g is not None and op_g >= 0.05)
    _chk(f"EPS (Diluted) YoY growth >= 10%? ({f'{eps_g*100:.2f}%' if eps_g is not None else 'N/A'})", eps_g is not None and eps_g >= 0.10)
    
    # 9. PE or PEG
    pe_str = analysis.finviz_data.get('P/E', '')
    pe_val = _safe_float_parse(pe_str)
    peg_str = analysis.finviz_data.get('PEG', '')
    peg_val = _safe_float_parse(peg_str)
    
    if peg_val is None and pe_val is not None and eps_5y_val is not None and eps_5y_val > 0:
        peg_val = pe_val / eps_5y_val
        peg_str = f"{peg_val:.2f} (calc)"
        
    _chk(f"P/E <= 30 ({pe_str}) OR PEG <= 2 ({peg_str})", (pe_val is not None and pe_val <= 30) or (peg_val is not None and peg_val <= 2))
    
    # 10. Extras
    action = getattr(analysis, 'marketbeat_action_recent', None)
    next_earn = getattr(analysis, 'next_earnings_date', None)
    days_until = getattr(analysis, 'days_until_earnings', None)
    max_buy = getattr(analysis, 'max_buy_price', None)
    
    st.markdown("---")
    st.markdown(f"**🟢 Recent Analyst Upgrade/Downgrade:** {str(action) if action else 'N/A'}")
    
    if next_earn:
        date_str = next_earn.date() if hasattr(next_earn, 'date') else str(next_earn)[:10]
        st.markdown(f"**📅 Next Quarter Earnings Date:** {date_str} (in {days_until} days)" if days_until else f"**📅 Next Quarter Earnings Date:** {date_str}")
    else:
        st.markdown("**📅 Next Quarter Earnings Date:** N/A")
        
    if max_buy:
        st.markdown(f"**💵 Calculated MBP (MATP ÷ 1.15):** ${max_buy:.2f}")
    else:
        matp = getattr(analysis, 'median_price_target', None)
        price = getattr(analysis, 'current_price', None)
        if matp and price and price > matp:
            st.warning(f"⚠️ **Above Analyst Targets:** Current price (${price:.2f}) exceeds analyst consensus target (${matp:.2f}).")
        else:
            st.markdown("**💵 Max Buy Price:** N/A")
    st.divider()
