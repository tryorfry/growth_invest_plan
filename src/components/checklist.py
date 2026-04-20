from src.analyzer import StockAnalysis
from src.logic.scorer import ChecklistScorer

def render_checklist(analysis: StockAnalysis):
    """Render the Investment Checklist in the dashboard"""
    st.divider()
    st.subheader("✅ 9-Point Investment Checklist")
    
    # Use centralized scorer
    score, total, details = ChecklistScorer.calculate_score(analysis)
    
    # Render score header
    color = "green" if score >= 8 else ("blue" if score >= 6 else "orange")
    st.markdown(f"#### Overall Score: :{color}[{score}/{total}]")
    
    # Render points
    for point_name, result in details.items():
        icon = "✅" if result["pass"] else "⚠️"
        st.markdown(f"{icon} **{result['label']}**")
    
    # 10. Extras (Items not part of the 9-point fundamental score but useful for timing)
 10. Extras
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
