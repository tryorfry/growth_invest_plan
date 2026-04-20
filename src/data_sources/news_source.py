"""Source for fetching and analyzing News Sentiment"""

import yfinance as yf
from textblob import TextBlob
import pandas as pd
import asyncio
import streamlit as st
import requests
from typing import List, Dict, Any

from .base import DataSource

class NewsSentimentSource(DataSource):
    """Fetches recent news articles and scores them using Natural Language Processing"""
    
    def get_source_name(self) -> str:
        return "NewsSentimentNLP"
        
    async def fetch(self, ticker: str, **kwargs) -> Dict[str, Any]:
        """Async wrapper for the DataSource interface"""
        # Run the synchronous fetch in a thread pool to not block the event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.fetch_and_analyze_news, ticker)
        
    @st.cache_data(ttl=600)
    def fetch_and_analyze_news(_self, ticker: str, max_articles: int = 20) -> Dict[str, Any]:
        """
        Fetches recent news from Yahoo Finance and scores the headline sentiment.
        Uses a fallback RSS source if yfinance returns empty or fails SSL.
        """
        if _self.is_broken():
            return {"average_sentiment": 0.0, "articles": [], "sentiment_label": "Neutral", "status": "Cooling"}

        try:
            from bs4 import BeautifulSoup
            # Source 1: Yahoo Finance API
            news_items = []
            try:
                stock = yf.Ticker(ticker)
                news_items = stock.news
                if news_items:
                    print(f"✅ Found news for {ticker} via YFinance")
            except Exception as e: 
                print(f"⚠️ YFinance news failed for {ticker}: {e}")
            
            # Source 2: Finviz Scraper (High Reliability)
            if not news_items:
                try:
                    finviz_url = f"https://finviz.com/quote.ashx?t={ticker}"
                    resp = _self._get_response_sync(finviz_url)
                    if resp and resp.status_code == 200:
                        soup = BeautifulSoup(resp.content, 'html.parser')
                        news_table = soup.find("table", id="news-table")
                        if news_table:
                            rows = news_table.find_all("tr")
                            for row in rows[:max_articles]:
                                link_tag = row.find("a", class_="tab-link-news")
                                if link_tag:
                                    # Extract publisher from the text before the link or standard source list
                                    provider = "Finviz"
                                    publisher_tag = row.find("div", class_="news-link-right")
                                    if publisher_tag:
                                         provider = publisher_tag.get_text(strip=True)
                                    
                                    news_items.append({
                                        'title': link_tag.get_text(strip=True),
                                        'link': link_tag.get('href'),
                                        'publisher': provider,
                                        'providerPublishTime': 0 # Finviz time parsing is complex, we use current or fallback
                                    })
                            if news_items:
                                print(f"✅ Found news for {ticker} via Finviz")
                except Exception as ef:
                    print(f"⚠️ Finviz news failed for {ticker}: {ef}")

            # Source 3: Google News RSS (Last Resort)
            if not news_items:
                try:
                    import xml.etree.ElementTree as ET
                    rss_url = f"https://news.google.com/rss/search?q={ticker}+stock+news&hl=en-US&gl=US&ceid=US:en"
                    resp = _self._get_response_sync(rss_url)
                    if resp and resp.status_code == 200:
                        root = ET.fromstring(resp.content)
                        for item in root.findall('.//item')[:max_articles]:
                            news_items.append({
                                'title': item.find('title').text,
                                'link': item.find('link').text,
                                'publisher': 'Google News',
                                'providerPublishTime': pd.to_datetime(item.find('pubDate').text).timestamp() if item.find('pubDate') is not None else 0
                            })
                        if news_items:
                            print(f"✅ Found news for {ticker} via Google RSS")
                except Exception as er:
                    print(f"⚠️ RSS news failed for {ticker}: {er}")

            if not news_items:
                return {"average_sentiment": 0.0, "articles": [], "sentiment_label": "Neutral"}
                
            scored_articles = []
            total_sentiment = 0.0
            
            # Process results
            for item in news_items[:max_articles]:
                # Handle NEW yfinance structure (nested in 'content') or OLD structure (top-level)
                content = item.get('content', {}) if 'content' in item else item
                
                title = content.get('title', '')
                if not title: continue
                    
                blob = TextBlob(title)
                polarity = blob.sentiment.polarity
                
                label = "Bullish" if polarity > 0.15 else "Bearish" if polarity < -0.15 else "Neutral"
                
                # Extract date (pubDate in nested, providerPublishTime in old)
                ts = content.get('pubDate') or content.get('providerPublishTime') or item.get('providerPublishTime')
                dt = pd.to_datetime(ts) if isinstance(ts, str) else pd.to_datetime(ts, unit='s') if ts else pd.Timestamp.now()
                
                # Extract link
                link = content.get('canonicalUrl') or content.get('clickThroughUrl', {}).get('url') or item.get('link', '')
                
                # Extract publisher
                provider = content.get('provider', {})
                publisher = provider.get('displayName') if isinstance(provider, dict) else provider or item.get('publisher', 'Unknown')

                scored_articles.append({
                    "title": title,
                    "publisher": publisher,
                    "link": link,
                    "date": dt.strftime('%Y-%m-%d %H:%M'),
                    "sentiment_score": polarity,
                    "sentiment_label": label
                })
                total_sentiment += polarity
                
            if not scored_articles:
                # If yfinance returned headlines but we couldn't parse them, fallback 
                print(f"⚠️ Failed to parse YFinance headlines for {ticker}, falling back...")
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
            import traceback
            traceback.print_exc()
            return {"average_sentiment": 0.0, "articles": [], "sentiment_label": "Neutral", "error": str(e)}
