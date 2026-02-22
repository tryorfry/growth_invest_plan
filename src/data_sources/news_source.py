"""Source for fetching and analyzing News Sentiment"""

import yfinance as yf
from textblob import TextBlob
import pandas as pd
import asyncio
import streamlit as st
from typing import List, Dict, Any

class NewsSentimentSource:
    """Fetches recent news articles and scores them using Natural Language Processing"""
    
    def get_source_name(self) -> str:
        return "NewsSentimentNLP"
        
    async def fetch(self, ticker: str) -> Dict[str, Any]:
        """Async wrapper for the DataSource interface"""
        # Run the synchronous fetch in a thread pool to not block the event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.fetch_and_analyze_news, ticker)
        
    @st.cache_data(ttl=3600)
    def fetch_and_analyze_news(_self, ticker: str, max_articles: int = 20) -> Dict[str, Any]:
        """
        Fetches recent news from Yahoo Finance and scores the headline sentiment.
        
        Args:
            ticker (str): Stock symbol.
            max_articles (int): Maximum number of articles to process.
            
        Returns:
            Dict containing average sentiment and a list of scored articles.
        """
        try:
            stock = yf.Ticker(ticker)
            news_items = stock.news
            
            if not news_items:
                return {"average_sentiment": 0.0, "articles": [], "sentiment_label": "Neutral"}
                
            scored_articles = []
            total_sentiment = 0.0
            
            # YFinance news is a list of dicts. Usually has 'title', 'link', 'publisher', 'providerPublishTime'
            for item in news_items[:max_articles]:
                title = item.get('title', '')
                if not title:
                    continue
                    
                # Use TextBlob to calculate Polarity (-1.0 to 1.0)
                blob = TextBlob(title)
                polarity = blob.sentiment.polarity
                
                # Determine label
                if polarity > 0.15:
                    label = "Bullish"
                elif polarity < -0.15:
                    label = "Bearish"
                else:
                    label = "Neutral"
                    
                dt = pd.to_datetime(item.get('providerPublishTime', 0), unit='s')
                
                scored_articles.append({
                    "title": title,
                    "publisher": item.get('publisher', 'Unknown'),
                    "link": item.get('link', ''),
                    "date": dt.strftime('%Y-%m-%d %H:%M'),
                    "timestamp": dt,
                    "sentiment_score": polarity,
                    "sentiment_label": label
                })
                
                total_sentiment += polarity
                
            if not scored_articles:
                return {"average_sentiment": 0.0, "articles": [], "sentiment_label": "Neutral"}
                
            avg_sentiment = total_sentiment / len(scored_articles)
            
            if avg_sentiment > 0.15:
                overall_label = "Bullish"
            elif avg_sentiment < -0.15:
                overall_label = "Bearish"
            else:
                overall_label = "Neutral"
                
            return {
                "average_sentiment": avg_sentiment,
                "sentiment_label": overall_label,
                "articles": scored_articles
            }
            
        except Exception as e:
            print(f"Error fetching news for {ticker}: {e}")
            return {"average_sentiment": 0.0, "articles": [], "sentiment_label": "Neutral", "error": str(e)}
