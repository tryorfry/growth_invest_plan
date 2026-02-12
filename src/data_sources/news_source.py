
from typing import Dict, Any, Optional
import yfinance as yf
from textblob import TextBlob
import asyncio

from .base import DataSource

class NewsSource(DataSource):
    """Fetches news and calculates sentiment from Yahoo Finance"""
    
    def get_source_name(self) -> str:
        return "News"
    
    async def fetch(self, ticker: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Fetch news and analyze sentiment.
        
        Args:
            ticker: Stock ticker symbol
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._fetch_sync, ticker)

    def _fetch_sync(self, ticker: str) -> Optional[Dict[str, Any]]:
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            
            if not news:
                return None
            
            headlines = []
            sentiment_scores = []
            
            for item in news:
                title = item.get('title', '')
                if not title:
                    continue
                
                # Simple sentiment analysis using TextBlob
                blob = TextBlob(title)
                score = blob.sentiment.polarity
                sentiment_scores.append(score)
                headlines.append(f"{title} ({score:.2f})")
            
            if not sentiment_scores:
                return None
                
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            
            # Simple summarization based on average score
            if avg_sentiment > 0.1:
                feeling = "Bullish"
            elif avg_sentiment < -0.1:
                feeling = "Bearish"
            else:
                feeling = "Neutral"
            
            summary = f"{feeling} ({avg_sentiment:.2f}) based on latest {len(headlines)} headlines"
            
            return {
                "news_sentiment": avg_sentiment, 
                "news_summary": summary,
                "headlines": headlines
            }
            
        except Exception as e:
            print(f"Error fetching News: {e}")
            return None
