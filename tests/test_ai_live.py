from src.ai_analyzer import AIAnalyzer

ai = AIAnalyzer()
print(f"Key loaded: {bool(ai.api_key)}")
print(f"GenAI Available: {ai.is_available()}")

if ai.is_available():
    payload = {
        "current_price": 226.05,
        "trend": "Bullish",
        "support": 218.00,
        "resistance": 230.50,
        "sentiment": {"score": 0.65, "label": "Positive"}
    }
    print("Requesting thesis...")
    res = ai.generate_thesis("AAPL", payload)
    print("\n--- AI THESIS ---")
    print(res)
