"""
Market Scanner Module
Scans Binance futures markets using free CCXT public methods
"""

import ccxt
import time
import math
from typing import List, Dict, Any, Optional
from datetime import datetime

class MarketScanner:
    def __init__(self):
        # Initialize CCXT with public access (no auth required)
        self.exchange = ccxt.binance({
            'options': {'defaultType': 'future'},
            'enableRateLimit': True
        })
        
        # Filtering criteria (relaxed for testing)
        self.min_volume_usd = 1_000_000   # $1M for testing (was $50M)
        self.max_funding_rate = 0.001     # 0.1% for testing (was 0.05%)
        self.min_funding_rate = -0.001    # -0.1% for testing (was -0.05%)
        self.max_spread = 0.01            # 1% for testing (was 0.1%)
        
        # Cache for market data
        self.market_cache = {}
        self.cache_expiry = 60  # 60 seconds
        
    def fetch_all_futures_pairs(self) -> List[str]:
        """Fetch all available futures pairs from Binance (public method)"""
        try:
            # Load markets (public method, no auth required)
            markets = self.exchange.load_markets()
            futures_pairs = []
            
            for symbol, market in markets.items():
                if market['type'] == 'future' and market['active']:
                    futures_pairs.append(symbol)
            
            print(f"Found {len(futures_pairs)} futures pairs")
            return futures_pairs
        except Exception as e:
            print(f"Error fetching futures pairs: {e}")
            return []
    
    def fetch_ticker_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch ticker data for a symbol (public method)"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return dict(ticker) if ticker is not None else None
        except Exception as e:
            print(f"Error fetching ticker for {symbol}: {e}")
            return None

    def fetch_funding_rate(self, symbol: str) -> Optional[float]:
        """Fetch funding rate for a symbol (public method)"""
        try:
            funding_info = self.exchange.fetch_funding_rate(symbol)
            return funding_info.get('fundingRate', 0)
        except Exception as e:
            print(f"Error fetching funding rate for {symbol}: {e}")
            return None

    def fetch_order_book(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch order book to calculate spread (public method)"""
        try:
            order_book = self.exchange.fetch_order_book(symbol, limit=20)
            # Ensure order_book is a dictionary before accessing
            if isinstance(order_book, dict) and order_book.get('asks') and order_book.get('bids'):
                # Safely access order book data
                asks = order_book.get('asks', [])
                bids = order_book.get('bids', [])
                
                if asks and bids:
                    best_ask = asks[0][0] if isinstance(asks[0], (list, tuple)) and len(asks[0]) > 0 else 0
                    best_bid = bids[0][0] if isinstance(bids[0], (list, tuple)) and len(bids[0]) > 0 else 0
                    
                    # Ensure we have numeric values before calculation
                    if isinstance(best_ask, (int, float)) and isinstance(best_bid, (int, float)) and best_bid != 0:
                        spread = (best_ask - best_bid) / best_bid
                    else:
                        spread = 0
                else:
                    spread = 0
            else:
                spread = 0
            return {
                'spread': spread, 
                'best_ask': best_ask, 
                'best_bid': best_bid,
                'order_book': order_book
            }
        except Exception as e:
            print(f"Error fetching order book for {symbol}: {e}")
            return None

    def fetch_ohlcv_data(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> Optional[List]:
        """Fetch OHLCV data for volatility calculation (public method)"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            return ohlcv
        except Exception as e:
            print(f"Error fetching OHLCV for {symbol}: {e}")
            return None

    def calculate_atr(self, ohlcv_data: List) -> float:
        """Calculate Average True Range for volatility"""
        if len(ohlcv_data) < 14:
            return 0
        
        try:
            true_ranges = []
            for i in range(1, len(ohlcv_data)):
                high = ohlcv_data[i][2]
                low = ohlcv_data[i][3]
                prev_close = ohlcv_data[i-1][4]
                
                tr1 = high - low
                tr2 = abs(high - prev_close)
                tr3 = abs(low - prev_close)
                true_range = max(tr1, tr2, tr3)
                true_ranges.append(true_range)
            
            # Calculate 14-period ATR
            atr = sum(true_ranges[-14:]) / 14
            return atr
        except Exception as e:
            print(f"Error calculating ATR: {e}")
            return 0
    
    def calculate_technical_score(self, ohlcv_data: List) -> float:
        """Calculate technical score based on RSI, MACD, VWAP confluence"""
        if len(ohlcv_data) < 26:
            return 0
        
        try:
            closes = [candle[4] for candle in ohlcv_data]
            
            # Simple RSI calculation
            gains = []
            losses = []
            for i in range(1, len(closes)):
                change = closes[i] - closes[i-1]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
            
            avg_gain = sum(gains[-14:]) / 14 if gains else 0
            avg_loss = sum(losses[-14:]) / 14 if losses else 0
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            # Simple MACD
            ema12 = sum(closes[-12:]) / 12
            ema26 = sum(closes[-26:]) / 26
            macd = ema12 - ema26
            
            # Simple VWAP
            volumes = [candle[5] for candle in ohlcv_data]
            vwap = sum(closes[i] * volumes[i] for i in range(len(closes))) / sum(volumes)
            current_price = closes[-1]
            vwap_slope = (current_price - vwap) / vwap * 100
            
            # Calculate technical score (0-100)
            rsi_score = 50 - abs(rsi - 50)  # Higher score when RSI is neutral
            macd_score = 50 + (macd / current_price * 1000)  # Higher score for positive MACD
            vwap_score = 50 + vwap_slope  # Higher score for positive VWAP slope
            
            technical_score = (rsi_score + macd_score + vwap_score) / 3
            return max(0, min(100, technical_score))
            
        except Exception as e:
            print(f"Error calculating technical score: {e}")
            return 0
    
    def get_liquidation_density(self, symbol: str, order_book: Optional[Dict[str, Any]] = None) -> float:
        """Calculate liquidation density using order book analysis (free method)"""
        try:
            if not order_book:
                return 0.0  # Default value for deployment version
            
            # Analyze order book for liquidation clusters
            bids = order_book.get('bids', [])
            asks = order_book.get('asks', [])
            
            if not bids or not asks:
                return 50.0
            
            # Calculate bid/ask imbalance
            total_bid_volume = sum(bid[1] for bid in bids[:10])  # Top 10 bids
            total_ask_volume = sum(ask[1] for ask in asks[:10])  # Top 10 asks
            
            # Calculate imbalance ratio
            imbalance_ratio = abs(total_bid_volume - total_ask_volume) / max(total_bid_volume, total_ask_volume)
            
            # Convert to liquidation density score (0-100)
            liquidation_density = min(100, imbalance_ratio * 100)
            
            return liquidation_density
            
        except Exception as e:
            print(f"Error calculating liquidation density for {symbol}: {e}")
            return 50.0  # Default value
    
    def scan_and_filter_markets(self) -> List[Dict[str, Any]]:
        """Scan all markets and apply filters using free CCXT methods"""
        print("Starting market scan...")
        
        # Fetch all futures pairs
        all_pairs = self.fetch_all_futures_pairs()
        if not all_pairs:
            return []
        
        filtered_markets = []
        
        for symbol in all_pairs:
            try:
                print(f"Scanning {symbol}...")
                
                # Fetch market data (public methods)
                ticker = self.fetch_ticker_data(symbol)
                if not ticker:
                    continue
                
                # Volume filter
                volume_usd = ticker.get('quoteVolume', 0)
                if volume_usd < self.min_volume_usd:
                    continue
                
                # Funding rate filter
                funding_rate = self.fetch_funding_rate(symbol)
                if funding_rate is not None:
                    if funding_rate > self.max_funding_rate or funding_rate < self.min_funding_rate:
                        continue
                
                # Spread filter
                order_book_data = self.fetch_order_book(symbol)
                if order_book_data:
                    spread = order_book_data['spread']
                    if spread > self.max_spread:
                        continue
                else:
                    # If we can't get spread, skip this symbol
                    continue
                
                # Fetch OHLCV for technical analysis
                ohlcv = self.fetch_ohlcv_data(symbol)
                if not ohlcv:
                    continue
                
                # Calculate metrics
                atr = self.calculate_atr(ohlcv)
                technical_score = self.calculate_technical_score(ohlcv)
                liquidation_density = self.get_liquidation_density(symbol, order_book_data.get('order_book') or {})
                
                # Create market data
                market_data = {
                    'symbol': symbol,
                    'price': ticker['last'],
                    'volume_24h': volume_usd,
                    'funding_rate': funding_rate or 0,
                    'spread': order_book_data['spread'],
                    'atr': atr,
                    'technical_score': technical_score,
                    'liquidation_density': liquidation_density,
                    'ticker': ticker,
                    'order_book': order_book_data,
                    'ohlcv': ohlcv
                }
                
                filtered_markets.append(market_data)
                
                # Rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
                continue
        
        print(f"Filtered {len(filtered_markets)} markets from {len(all_pairs)} total")
        return filtered_markets
    
    def rank_markets(self, markets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank markets by volatility, liquidation density, and technical score"""
        if not markets:
            return []
        
        try:
            # Normalize scores (0-100)
            max_atr = max(m['atr'] for m in markets) if markets else 1
            max_technical = max(m['technical_score'] for m in markets) if markets else 1
            max_liquidation = max(m['liquidation_density'] for m in markets) if markets else 1
            
            for market in markets:
                # Normalize ATR (higher is better for volatility)
                market['atr_normalized'] = (market['atr'] / max_atr) * 100
                
                # Technical score is already 0-100
                market['technical_normalized'] = market['technical_score']
                
                # Normalize liquidation density
                market['liquidation_normalized'] = (market['liquidation_density'] / max_liquidation) * 100
                
                # Calculate combined score
                market['combined_score'] = (
                    market['atr_normalized'] * 0.4 +
                    market['technical_normalized'] * 0.4 +
                    market['liquidation_normalized'] * 0.2
                )
            
            # Sort by combined score
            ranked_markets = sorted(markets, key=lambda x: x['combined_score'], reverse=True)
            
            return ranked_markets
            
        except Exception as e:
            print(f"Error ranking markets: {e}")
            return markets
    
    def get_top_markets(self, limit: int = 30) -> List[Dict[str, Any]]:
        """Get top ranked markets for trading"""
        try:
            # Scan and filter markets
            filtered_markets = self.scan_and_filter_markets()
            
            # Rank markets
            ranked_markets = self.rank_markets(filtered_markets)
            
            # Return top markets
            top_markets = ranked_markets[:limit]
            
            print(f"Selected top {len(top_markets)} markets for trading")
            for i, market in enumerate(top_markets):
                print(f"{i+1}. {market['symbol']} - Score: {market['combined_score']:.2f}")
            
            return top_markets
            
        except Exception as e:
            print(f"Error getting top markets: {e}")
            return []
    
    def get_markets(self) -> List[Dict[str, Any]]:
        """Get markets (alias for get_top_markets for test compatibility)"""
        return self.get_top_markets()
    
    def get_market_summary(self, markets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary statistics for scanned markets"""
        if not markets:
            return {
                'total_markets': 0,
                'avg_volume': 0,
                'avg_funding_rate': 0,
                'avg_spread': 0,
                'top_symbols': []
            }
        
        try:
            total_markets = len(markets)
            avg_volume = sum(m['volume_24h'] for m in markets) / total_markets
            avg_funding_rate = sum(m['funding_rate'] for m in markets) / total_markets
            avg_spread = sum(m['spread'] for m in markets) / total_markets
            
            # Top symbols by score
            top_symbols = [(m['symbol'], m['combined_score']) for m in markets[:10]]
            
            return {
                'total_markets': total_markets,
                'avg_volume': avg_volume,
                'avg_funding_rate': avg_funding_rate,
                'avg_spread': avg_spread,
                'top_symbols': top_symbols
            }
        except Exception as e:
            print(f"Error getting market summary: {e}")
            return {
                'total_markets': 0,
                'avg_volume': 0,
                'avg_funding_rate': 0,
                'avg_spread': 0,
                'top_symbols': []
            } 