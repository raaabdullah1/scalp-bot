"""
Sentiment Analysis Module
Uses free RSS feeds and TextBlob for sentiment analysis
"""

import feedparser
import time
import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from textblob import TextBlob

class SentimentAnalyzer:
    def __init__(self):
        # Free RSS feed URLs
        self.cryptopanic_rss = "https://cryptopanic.com/api/v1/posts/?auth_token=free&currencies=BTC,ETH,BNB&filter=hot"
        self.coindesk_rss = "https://www.coindesk.com/arc/outboundfeeds/rss/"
        self.cointelegraph_rss = "https://cointelegraph.com/rss"
        
        # Cache for sentiment data
        self.sentiment_cache = {}
        self.cache_expiry = 300  # 5 minutes
        
        # Keywords for volatility detection
        self.volatility_keywords = [
            'crash', 'dump', 'pump', 'surge', 'rally', 'moon', 'rocket',
            'bear', 'bull', 'correction', 'breakout', 'breakdown',
            'fud', 'fomo', 'panic', 'sell-off', 'buying spree',
            'regulation', 'ban', 'adoption', 'partnership', 'upgrade',
            'fork', 'airdrop', 'burn', 'mint', 'liquidation'
        ]
        
        # Market sentiment keywords
        self.bullish_keywords = [
            'bullish', 'uptrend', 'rally', 'surge', 'moon', 'rocket',
            'breakout', 'accumulation', 'buying', 'adoption', 'partnership',
            'upgrade', 'burn', 'positive', 'gains', 'profit'
        ]
        
        self.bearish_keywords = [
            'bearish', 'downtrend', 'crash', 'dump', 'correction',
            'breakdown', 'distribution', 'selling', 'fud', 'panic',
            'regulation', 'ban', 'negative', 'losses', 'decline'
        ]
    
    def fetch_cryptopanic_rss(self) -> List[Dict[str, Any]]:
        """Fetch news from CryptoPanic RSS feed (free)"""
        try:
            feed = feedparser.parse(self.cryptopanic_rss)
            articles = []
            
            for entry in feed.entries[:20]:  # Get latest 20 articles
                article = {
                    'title': entry.get('title', ''),
                    'summary': entry.get('summary', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'source': 'CryptoPanic'
                }
                articles.append(article)
            
            return articles
        except Exception as e:
            print(f"Error fetching CryptoPanic RSS: {e}")
            return []
    
    def fetch_coindesk_rss(self) -> List[Dict[str, Any]]:
        """Fetch news from CoinDesk RSS feed (free)"""
        try:
            feed = feedparser.parse(self.coindesk_rss)
            articles = []
            
            for entry in feed.entries[:15]:  # Get latest 15 articles
                article = {
                    'title': entry.get('title', ''),
                    'summary': entry.get('summary', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'source': 'CoinDesk'
                }
                articles.append(article)
            
            return articles
        except Exception as e:
            print(f"Error fetching CoinDesk RSS: {e}")
            return []
    
    def fetch_cointelegraph_rss(self) -> List[Dict[str, Any]]:
        """Fetch news from CoinTelegraph RSS feed (free)"""
        try:
            feed = feedparser.parse(self.cointelegraph_rss)
            articles = []
            
            for entry in feed.entries[:15]:  # Get latest 15 articles
                article = {
                    'title': entry.get('title', ''),
                    'summary': entry.get('summary', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'source': 'CoinTelegraph'
                }
                articles.append(article)
            
            return articles
        except Exception as e:
            print(f"Error fetching CoinTelegraph RSS: {e}")
            return []
    
    def analyze_text_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment using TextBlob (free)"""
        try:
            # Clean text
            clean_text = re.sub(r'[^\w\s]', '', text.lower())
            
            # Create TextBlob object
            blob = TextBlob(clean_text)
            
            # Get polarity (-1 to 1) and subjectivity (0 to 1)
            sentiment: Any = blob.sentiment
            polarity = sentiment.polarity
            subjectivity = sentiment.subjectivity
            
            # Calculate confidence based on subjectivity
            confidence = 1 - subjectivity if subjectivity > 0 else 1
            
            return {
                'polarity': polarity,
                'subjectivity': subjectivity,
                'confidence': confidence
            }
        except Exception as e:
            print(f"Error analyzing text sentiment: {e}")
            return {'polarity': 0, 'subjectivity': 0.5, 'confidence': 0}
    
    def detect_volatility_keywords(self, text: str) -> Dict[str, Any]:
        """Detect volatility-related keywords in text"""
        try:
            text_lower = text.lower()
            
            # Count volatility keywords
            volatility_count = sum(1 for keyword in self.volatility_keywords if keyword in text_lower)
            
            # Count bullish/bearish keywords
            bullish_count = sum(1 for keyword in self.bullish_keywords if keyword in text_lower)
            bearish_count = sum(1 for keyword in self.bearish_keywords if keyword in text_lower)
            
            # Calculate volatility score (0-100)
            volatility_score = min(100, volatility_count * 10)
            
            # Determine sentiment bias
            if bullish_count > bearish_count:
                sentiment_bias = 'bullish'
                bias_strength = bullish_count / max(bullish_count + bearish_count, 1)
            elif bearish_count > bullish_count:
                sentiment_bias = 'bearish'
                bias_strength = bearish_count / max(bullish_count + bearish_count, 1)
            else:
                sentiment_bias = 'neutral'
                bias_strength = 0
            
            return {
                'volatility_score': volatility_score,
                'sentiment_bias': sentiment_bias,
                'bias_strength': bias_strength,
                'volatility_count': volatility_count,
                'bullish_count': bullish_count,
                'bearish_count': bearish_count
            }
        except Exception as e:
            print(f"Error detecting volatility keywords: {e}")
            return {
                'volatility_score': 0,
                'sentiment_bias': 'neutral',
                'bias_strength': 0,
                'volatility_count': 0,
                'bullish_count': 0,
                'bearish_count': 0
            }
    
    def analyze_article_sentiment(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment of a single article"""
        try:
            # Combine title and summary
            text = f"{article.get('title', '')} {article.get('summary', '')}"
            
            # Analyze sentiment
            sentiment = self.analyze_text_sentiment(text)
            volatility = self.detect_volatility_keywords(text)
            
            return {
                'title': article.get('title', ''),
                'source': article.get('source', ''),
                'sentiment': sentiment,
                'volatility': volatility,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error analyzing article sentiment: {e}")
            return {}
    
    def get_market_sentiment(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get overall market sentiment from multiple sources"""
        try:
            # Check cache
            cache_key = f"sentiment_{symbol or 'market'}"
            if cache_key in self.sentiment_cache:
                cached_data = self.sentiment_cache[cache_key]
                if datetime.now().timestamp() - cached_data['timestamp'] < self.cache_expiry:
                    return cached_data['data']
            
            # Fetch news from multiple sources
            articles = []
            articles.extend(self.fetch_cryptopanic_rss())
            articles.extend(self.fetch_coindesk_rss())
            articles.extend(self.fetch_cointelegraph_rss())
            
            if not articles:
                return self._get_default_sentiment()
            
            # Analyze sentiment for each article
            analyzed_articles = []
            total_polarity = 0
            total_subjectivity = 0
            total_volatility = 0
            total_bullish = 0
            total_bearish = 0
            
            for article in articles:
                analysis = self.analyze_article_sentiment(article)
                if analysis:
                    analyzed_articles.append(analysis)
                    
                    # Aggregate scores
                    total_polarity += analysis['sentiment']['polarity']
                    total_subjectivity += analysis['sentiment']['subjectivity']
                    total_volatility += analysis['volatility']['volatility_score']
                    total_bullish += analysis['volatility']['bullish_count']
                    total_bearish += analysis['volatility']['bearish_count']
            
            if not analyzed_articles:
                return self._get_default_sentiment()
            
            # Calculate averages
            num_articles = len(analyzed_articles)
            avg_polarity = total_polarity / num_articles
            avg_subjectivity = total_subjectivity / num_articles
            avg_volatility = total_volatility / num_articles
            
            # Determine overall sentiment
            if avg_polarity > 0.1:
                overall_sentiment = 'bullish'
                sentiment_score = min(1.0, avg_polarity * 2)
            elif avg_polarity < -0.1:
                overall_sentiment = 'bearish'
                sentiment_score = max(-1.0, avg_polarity * 2)
            else:
                overall_sentiment = 'neutral'
                sentiment_score = 0
            
            # Calculate event volatility score
            event_volatility_score = min(100, avg_volatility)
            
            # Determine market mood
            if event_volatility_score > 70:
                market_mood = 'high_volatility'
            elif event_volatility_score > 40:
                market_mood = 'moderate_volatility'
            else:
                market_mood = 'low_volatility'
            
            # Create sentiment summary
            sentiment_data = {
                'overall_sentiment': overall_sentiment,
                'sentiment_score': sentiment_score,
                'event_volatility_score': event_volatility_score,
                'market_mood': market_mood,
                'avg_polarity': avg_polarity,
                'avg_subjectivity': avg_subjectivity,
                'total_articles': num_articles,
                'bullish_articles': total_bullish,
                'bearish_articles': total_bearish,
                'analyzed_articles': analyzed_articles[:5],  # Top 5 articles
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache the result
            self.sentiment_cache[cache_key] = {
                'data': sentiment_data,
                'timestamp': datetime.now().timestamp()
            }
            
            return sentiment_data
            
        except Exception as e:
            print(f"Error getting market sentiment: {e}")
            return self._get_default_sentiment()
    
    def get_symbol_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get sentiment specific to a symbol"""
        try:
            # For now, use general market sentiment
            # In a more advanced implementation, you could filter articles by symbol
            market_sentiment = self.get_market_sentiment()
            
            # Add symbol-specific information
            symbol_sentiment = market_sentiment.copy()
            symbol_sentiment['symbol'] = symbol
            symbol_sentiment['symbol_specific'] = False  # Indicates this is general sentiment
            
            return symbol_sentiment
            
        except Exception as e:
            print(f"Error getting symbol sentiment for {symbol}: {e}")
            return self._get_default_sentiment()
    
    def _get_default_sentiment(self) -> Dict[str, Any]:
        """Return default sentiment when analysis fails"""
        return {
            'overall_sentiment': 'neutral',
            'sentiment_score': 0,
            'event_volatility_score': 25,
            'market_mood': 'low_volatility',
            'avg_polarity': 0,
            'avg_subjectivity': 0.5,
            'total_articles': 0,
            'bullish_articles': 0,
            'bearish_articles': 0,
            'analyzed_articles': [],
            'timestamp': datetime.now().isoformat()
        }
    
    def calculate_leverage_adjustment(self, sentiment_data: Dict[str, Any]) -> float:
        """Calculate leverage adjustment based on sentiment"""
        try:
            sentiment_score = sentiment_data.get('sentiment_score', 0)
            volatility_score = sentiment_data.get('event_volatility_score', 25)
            
            # Base leverage
            base_leverage = 3.0
            
            # Adjust based on sentiment
            if sentiment_score > 0.3:
                # Bullish sentiment - increase leverage slightly
                leverage_multiplier = 1.2
            elif sentiment_score < -0.3:
                # Bearish sentiment - decrease leverage
                leverage_multiplier = 0.8
            else:
                # Neutral sentiment
                leverage_multiplier = 1.0
            
            # Adjust based on volatility
            if volatility_score > 70:
                # High volatility - decrease leverage
                volatility_multiplier = 0.7
            elif volatility_score > 40:
                # Moderate volatility - slight decrease
                volatility_multiplier = 0.9
            else:
                # Low volatility - normal leverage
                volatility_multiplier = 1.0
            
            # Calculate final leverage
            adjusted_leverage = base_leverage * leverage_multiplier * volatility_multiplier
            
            # Ensure leverage is within reasonable bounds
            adjusted_leverage = max(1.0, min(5.0, adjusted_leverage))
            
            return round(adjusted_leverage, 1)
            
        except Exception as e:
            print(f"Error calculating leverage adjustment: {e}")
            return 3.0  # Default leverage
    
    def get_market_sentiment_summary(self, symbols: List[str]) -> Dict[str, Any]:
        """Get sentiment summary for multiple symbols"""
        try:
            sentiment_summary = {}
            
            for symbol in symbols:
                sentiment = self.get_symbol_sentiment(symbol)
                sentiment_summary[symbol] = {
                    'sentiment_score': sentiment.get('sentiment_score', 0),
                    'market_mood': sentiment.get('market_mood', 'neutral'),
                    'volatility_score': sentiment.get('event_volatility_score', 25)
                }
            
            return sentiment_summary
        except Exception as e:
            print(f"Error getting market sentiment summary: {e}")
            return {symbol: {'sentiment_score': 0, 'market_mood': 'neutral', 'volatility_score': 25} for symbol in symbols} 