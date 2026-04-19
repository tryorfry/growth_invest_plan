"""Source for fetching and analyzing News Sentiment"""

import yfinance as yf
from textblob import TextBlob
import pandas as pd
import asyncio
import streamlit as st
import requests
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
        
    @st.cache_data(ttl=600) # Reduced from 3600 to 10 minutes for freshness
    def fetch_and_analyze_news(_self, ticker: str, max_articles: int = 20) -> Dict[str, Any]:
        """
        Fetches recent news from Yahoo Finance and scores the headline sentiment.
        Uses a fallback RSS source if yfinance returns empty.
        """
        try:
            # Source 1: Yahoo Finance API
            stock = yf.Ticker(ticker)
            news_items = stock.news
            
            # Source 2 Fallback: RSS Feed if yfinance is empty
            if not news_items:
                try:
                    import xml.etree.ElementTree as ET
                    rss_url = f"https://news.google.com/rss/search?q={ticker}+stock&hl=en-US&gl=US&ceid=US:en"
                    resp = requests.get(rss_url, timeout=5)
                    if resp.status_code == 200:
                        root = ET.fromstring(resp.content)
                        news_items = []
                        for item in root.findall('.//item')[:max_articles]:
                            news_items.append({
                                'title': item.find('title').text,
                                'link': item.find('link').text,
                                'publisher': 'Google News',
                                'providerPublishTime': pd.to_datetime(item.find('pubDate').text).timestamp()
                            })
                except: pass

            if not news_items:
                return {"average_sentiment": 0.0, "articles": [], "sentiment_label": "Neutral"}
                
            scored_articles = []
            total_sentiment = 0.0
            
            # Process results
            for item in news_items[:max_articles]:
                title = item.get('title', '')
                if not title: continue
                    
                blob = TextBlob(title)
                polarity = blob.sentiment.polarity
                
                label = "Bullish" if polarity > 0.15 else "Bearish" if polarity < -0.15 else "Neutral"
                dt = pd.to_datetime(item.get('providerPublishTime', 0), unit='s')
                
                scored_articles.append({
                    "title": title,
                    "publisher": item.get('publisher', 'Unknown'),
                    "link": item.get('link', ''),
                    "date": dt.strftime('%Y-%m-%d %H:%M'),
                    "sentiment_score": polarity,
                    "sentiment_label": label
                })
                total_sentiment += polarity
                
            if not scored_articles:
                return {"average_sentiment": 0.0, "articles": [], "sentiment_label": "Neutral"}
                
            avg_sentiment = total_sentiment / len(scored_articles)
            overall_label = "Bullish" if avg_sentiment > 0.15 else "Bearish" if avg_sentiment < -0.15 else "Neutral"
                
            return {
                "average_sentiment": avg_sentiment,
                "sentiment_label": overall_label,
                "articles": scored_articles
            }
            
        except Exception as e:
            print(f"Error fetching news for {ticker}: {e}")
            return {"average_sentiment": 0.0, "articles": [], "sentiment_label": "Neutral", "error": str(e)}
