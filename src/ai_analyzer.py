import os
import logging
from typing import Dict, Any, Optional

# Attempt to import the new SDK, gracefully fading if not installed yet
try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

logger = logging.getLogger(__name__)

class AIAnalyzer:
    """Wrapper class for generating AI insights via Google Gemini."""
    
    def __init__(self):
        self.api_key = self._get_api_key()
        self.client = None
        
        if self.api_key and HAS_GENAI:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Client: {e}")
                self.client = None

    def _get_api_key(self) -> Optional[str]:
        """Tries to fetch the Gemini API key from Streamlit secrets or OS env."""
        # Check Streamlit secrets first (Cloud environment)
        try:
            import streamlit as st
            if "GEMINI_API_KEY" in st.secrets:
                return st.secrets["GEMINI_API_KEY"]
        except ImportError:
            pass
        except Exception:
            pass
            
        # Fallback to local environment variable
        return os.getenv("GEMINI_API_KEY")

    def is_available(self) -> bool:
        """Checks if the AI service is ready to be called."""
        return self.client is not None and HAS_GENAI

    def generate_thesis(self, symbol: str, stock_data: Dict[str, Any]) -> str:
        """
        Generates a 1-paragraph investment thesis based on the provided technical data.
        """
        if not self.is_available():
            return "⚠️ AI Analysis is currently unavailable. Please ensure your `GEMINI_API_KEY` is configured."
            
        prompt = self._construct_prompt(symbol, stock_data)
        
        try:
            # We use gemini-2.5-flash as it is lightning fast and free-tier generous
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "You are an elite, no-nonsense Wall Street quantitative analyst. "
                        "Write strictly ONE concise, hard-hitting executive summary paragraph (max 4-5 sentences) "
                        "detailing the outlook for the provided stock. "
                        "Focus exclusively on the technical levels, implied sentiment, and risk/reward ratio. "
                        "Do not use bullet points. Do not give financial advice. Give a raw read on the data."
                    ),
                    temperature=0.3, # Keep it analytical and grounded
                )
            )
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini API Error: {e}")
            return f"❌ Failed to generate thesis: {str(e)}"

    def _construct_prompt(self, symbol: str, data: Dict[str, Any]) -> str:
        """Formats the raw dictionary data into a readable text prompt for the LLM."""
        
        lines = [f"Please analyze {symbol} based on the following current market telemetry:\n"]
        
        # Pull safe defaults if nested data is missing
        current_price = data.get("current_price", "Unknown")
        trend = data.get("trend", "Unknown")
        support = data.get("support", "Unknown")
        resistance = data.get("resistance", "Unknown")
        
        lines.append(f"- Current Price: ${current_price}")
        lines.append(f"- Moving Average Trend: {trend}")
        lines.append(f"- Nearest Support Level: ${support}")
        lines.append(f"- Nearest Resistance Level: ${resistance}")
        
        if "sentiment" in data:
            s_score = data["sentiment"].get("score", "N/A")
            s_label = data["sentiment"].get("label", "Neutral")
            lines.append(f"- News Sentiment Score: {s_score} ({s_label})")
            
        if "hvn" in data:
            lines.append(f"- High Volume Node (HVN / Smart Money Level): ${data['hvn']}")
            
        if "earnings" in data:
            lines.append(f"- Post-Earnings Drift Status: {data['earnings'].get('drift_direction', 'None')}")
            
        lines.append("\nBased purely on these metrics, provide a single-paragraph trade thesis.")
        return "\n".join(lines)
