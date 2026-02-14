"""Test script for new features: alerts, watchlist, Excel export"""

import asyncio
from src.database import Database
from src.analyzer import StockAnalyzer
from src.watchlist import WatchlistManager
from src.alerts.alert_engine import AlertEngine
from src.exporters.excel_exporter import ExcelExporter
from src.data_sources.options_source import OptionsSource
from src.data_sources.insider_source import InsiderSource
from src.data_sources.short_interest_source import ShortInterestSource
from src.pattern_recognition import PatternRecognition


async def test_watchlist():
    """Test watchlist functionality"""
    print("\n" + "="*60)
    print("Testing Watchlist Management")
    print("="*60)
    
    db = Database()
    wm = WatchlistManager(db.get_session())
    
    # Create watchlist
    watchlist = wm.get_default_watchlist()
    print(f"✅ Created/Retrieved watchlist: {watchlist.name}")
    
    # Add stocks
    for ticker in ['AAPL', 'NVDA', 'GOOGL']:
        wm.add_stock_to_watchlist(watchlist.id, ticker, f"Added {ticker} for testing")
        print(f"✅ Added {ticker} to watchlist")
    
    # Get stocks
    stocks = wm.get_watchlist_stocks(watchlist.id)
    print(f"\n📋 Watchlist contains {len(stocks)} stocks:")
    for stock in stocks:
        print(f"  - {stock['ticker']}: {stock['notes']}")


async def test_alerts():
    """Test alert system"""
    print("\n" + "="*60)
    print("Testing Alert System")
    print("="*60)
    
    db = Database()
    session = db.get_session()
    alert_engine = AlertEngine(use_email=True)
    
    # Create test alerts
    print("\n📢 Creating test alerts...")
    
    # Price alert
    alert1 = alert_engine.create_alert(
        session, 'AAPL', 'price', 'above', 250.0, email_enabled=True
    )
    if alert1:
        print(f"✅ Created price alert: AAPL above $250")
    
    # RSI alert
    alert2 = alert_engine.create_alert(
        session, 'NVDA', 'rsi', 'above', 70.0, email_enabled=True
    )
    if alert2:
        print(f"✅ Created RSI alert: NVDA RSI above 70 (overbought)")
    
    # Test alert checking
    print("\n🔍 Testing alert evaluation...")
    analyzer = StockAnalyzer()
    analysis = await analyzer.analyze('AAPL')
    
    if analysis:
        triggered = alert_engine.check_alerts(session, analysis)
        if triggered:
            print(f"⚠️  {len(triggered)} alert(s) triggered!")
            for alert in triggered:
                print(f"  - {alert['alert_type']}: {alert['message'][:50]}...")
        else:
            print("✅ No alerts triggered (conditions not met)")


async def test_excel_export():
    """Test Excel export"""
    print("\n" + "="*60)
    print("Testing Excel Export")
    print("="*60)
    
    analyzer = StockAnalyzer()
    analyses = []
    
    for ticker in ['AAPL', 'NVDA']:
        print(f"Analyzing {ticker}...")
        analysis = await analyzer.analyze(ticker)
        if analysis:
            analyses.append(analysis)
    
    if analyses:
        exporter = ExcelExporter()
        filename = exporter.export_analysis(analyses, "test_export.xlsx")
        print(f"✅ Exported analysis to: {filename}")


async def test_advanced_analytics():
    """Test advanced analytics features"""
    print("\n" + "="*60)
    print("Testing Advanced Analytics")
    print("="*60)
    
    ticker = 'AAPL'
    
    # Options data
    print(f"\n📊 Fetching options data for {ticker}...")
    options_source = OptionsSource()
    options_data = options_source.fetch_options_data(ticker)
    if options_data:
        print(f"  Implied Volatility: {options_data.get('implied_volatility', 0):.2%}")
        print(f"  Put/Call Ratio: {options_data.get('put_call_ratio', 0):.2f}")
    
    # Insider trading
    print(f"\n👔 Fetching insider trading data for {ticker}...")
    insider_source = InsiderSource()
    insider_data = await insider_source.fetch_insider_data(ticker)
    if insider_data:
        print(f"  Insider Ownership: {insider_data.get('insider_ownership_pct', 0):.2f}%")
        print(f"  Recent Transactions: {insider_data.get('recent_transactions', 0)}")
    
    # Short interest
    print(f"\n📉 Fetching short interest for {ticker}...")
    short_source = ShortInterestSource()
    short_data = short_source.fetch_short_interest(ticker)
    if short_data:
        print(f"  Short % of Float: {short_data.get('short_percent_of_float', 0):.2f}%")
        print(f"  Days to Cover: {short_data.get('short_ratio', 0):.2f}")
    
    # Pattern recognition
    print(f"\n🕯️  Detecting candlestick patterns for {ticker}...")
    analyzer = StockAnalyzer()
    analysis = await analyzer.analyze(ticker)
    if analysis and analysis.history is not None:
        pattern_detector = PatternRecognition()
        patterns = pattern_detector.get_recent_patterns(analysis.history, days=30)
        if patterns:
            print(f"  Found {len(patterns)} patterns in last 30 days:")
            for pattern in patterns[-5:]:  # Show last 5
                print(f"    - {pattern['pattern']} on {pattern['date'].strftime('%Y-%m-%d')}: {pattern['signal']}")
        else:
            print("  No patterns detected in last 30 days")


async def main():
    """Run all tests"""
    print("\n🚀 Stock Analysis Tool - Feature Testing")
    print("="*60)
    
    try:
        await test_watchlist()
        await test_alerts()
        await test_excel_export()
        await test_advanced_analytics()
        
        print("\n" + "="*60)
        print("✅ All tests completed!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
