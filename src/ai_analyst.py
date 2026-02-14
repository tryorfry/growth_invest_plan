"""AI Analyst using Gemini to generate investment narratives"""

import os
import google.generativeai as genai
from typing import Optional
from src.analyzer import StockAnalysis

class AIAnalyst:
    """Uses Gemini LLM to analyze stock metrics and generate a thesis"""
    
    def __init__(self):
        # API Key should be in environment variables (for Local and Streamlit Cloud)
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
            self.enabled = True
        else:
            self.enabled = False
            
    async def generate_thesis(self, analysis: StockAnalysis) -> str:
        """Construct a prompt from analysis data and get AI verdict"""
        if not self.enabled:
            return "AI Analysis is disabled. Please set GEMINI_API_KEY in your environment secrets."
            
        # Construct the detailed prompt
        prompt = self._construct_prompt(analysis)
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating AI thesis: {str(e)}"
            
    def _construct_prompt(self, analysis: StockAnalysis) -> str:
        """Create a data-rich prompt for the LLM"""
        # Formulate technical summary
        tech_summary = (
            f"Ticker: {analysis.ticker}\n"
            f"Price: ${analysis.current_price:.2f}\n"
            f"RSI (14): {analysis.rsi:.1f}\n"
            f"ATR: {analysis.atr:.2f}\n"
            f"EMA 20/50/200: {analysis.ema20:.2f} / {analysis.ema50:.2f} / {analysis.ema200:.2f}\n"
            f"MACD: {analysis.macd:.2f}\n"
        )
        
        # Formulate fundamental summary
        fund_summary = ""
        if analysis.finviz_data:
            fund_summary = "\n".join([f"{k}: {v}" for k, v in analysis.finviz_data.items() if k != 'ticker'])
            
        # Formulate valuation summary
        val_summary = (
            f"Basic EPS: {analysis.basic_eps}\n"
            f"Median Price Target: ${analysis.median_price_target if analysis.median_price_target else 'N/A'}\n"
        )
        
        # News/Sentiment
        sent_summary = (
            f"Recent News Sentiment: {analysis.news_sentiment:.2f}\n"
            f"News Summary: {analysis.news_summary}\n"
        )
        
        full_prompt = (
            f"You are a professional growth investment analyst. Analyze the following data for {analysis.ticker} "
            f"and provide a concise, professional investment thesis.\n\n"
            f"--- DATA ---\n"
            f"{tech_summary}\n"
            f"FUNDAMENTALS:\n{fund_summary}\n\n"
            f"VALUATION:\n{val_summary}\n"
            f"SENTIMENT:\n{sent_summary}\n"
            f"--- TASK ---\n"
            f"Please provide:\n"
            f"1. Bull Case (2-3 bullet points)\n"
            f"2. Bear Case (2-3 bullet points)\n"
            f"3. Final Verdict (Buy/Hold/Sell) with a 1-sentence logic.\n"
            f"Keep it professional and data-driven."
        )
        return full_prompt
