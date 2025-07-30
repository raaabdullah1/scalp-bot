"""
Dark Pool Detection Module
Uses free CCXT order book analysis to detect large trades and market anomalies
"""

import ccxt
import time
import math
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

class DarkPoolDetector:
    def __init__(self):
        # Initialize CCXT with public access (no auth required)
        self.exchange = ccxt.binance({
            'options': {'defaultType': 'future'},
            'enableRateLimit': True
        })
        
        # Detection parameters
        self.large_trade_threshold = 20  # BTC equivalent for large trades
        self.anomaly_threshold = 0.1     # 10% deviation for anomaly detection
        self.volume_spike_threshold = 3.0  # 3x average volume for spike detection
        
        # Cache for detection data
        self.detection_cache = {}
        self.cache_expiry = 30  # 30 seconds cache
        
        # Historical data for baseline calculations
        self.volume_baselines = {}
        self.price_baselines = {}
        
    def fetch_order_book(self, symbol: str, limit: int = 20) -> Optional[Dict[str, Any]]:
        """Fetch order book data (public method)"""
        try:
            order_book = self.exchange.fetch_order_book(symbol, limit=limit)
            return dict(order_book) if order_book is not None else None
        except Exception as e:
            print(f"Error fetching order book for {symbol}: {e}")
            return None
    
    def fetch_recent_trades(self, symbol: str, limit: int = 50) -> Optional[List[Dict[str, Any]]]:
        """Fetch recent trades (public method)"""
        try:
            trades = self.exchange.fetch_trades(symbol, limit=limit)
            return [dict(trade) for trade in trades] if trades is not None else None
        except Exception as e:
            print(f"Error fetching trades for {symbol}: {e}")
            return None
    
    def fetch_ohlcv_data(self, symbol: str, timeframe: str = '1m', limit: int = 60) -> Optional[List]:
        """Fetch OHLCV data for volume analysis (public method)"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            return ohlcv
        except Exception as e:
            print(f"Error fetching OHLCV for {symbol}: {e}")
            return None
    
    def detect_large_orders(self, order_book: Dict[str, Any]) -> Dict[str, Any]:
        """Detect large orders in order book"""
        try:
            bids = order_book.get('bids', [])
            asks = order_book.get('asks', [])
            
            large_bids = []
            large_asks = []
            
            # Analyze bid orders
            for price, volume in bids:
                if volume >= self.large_trade_threshold:
                    large_bids.append({
                        'price': price,
                        'volume': volume,
                        'size_category': self._categorize_order_size(volume)
                    })
            
            # Analyze ask orders
            for price, volume in asks:
                if volume >= self.large_trade_threshold:
                    large_asks.append({
                        'price': price,
                        'volume': volume,
                        'size_category': self._categorize_order_size(volume)
                    })
            
            # Calculate statistics
            total_large_bid_volume = sum(order['volume'] for order in large_bids)
            total_large_ask_volume = sum(order['volume'] for order in large_asks)
            
            return {
                'large_bids': large_bids,
                'large_asks': large_asks,
                'total_large_bid_volume': total_large_bid_volume,
                'total_large_ask_volume': total_large_ask_volume,
                'large_order_imbalance': total_large_bid_volume - total_large_ask_volume,
                'large_order_count': len(large_bids) + len(large_asks)
            }
            
        except Exception as e:
            print(f"Error detecting large orders: {e}")
            return {
                'large_bids': [],
                'large_asks': [],
                'total_large_bid_volume': 0,
                'total_large_ask_volume': 0,
                'large_order_imbalance': 0,
                'large_order_count': 0
            }
    
    def _categorize_order_size(self, volume: float) -> str:
        """Categorize order size"""
        if volume >= self.large_trade_threshold * 5:
            return 'whale'
        elif volume >= self.large_trade_threshold * 3:
            return 'large'
        elif volume >= self.large_trade_threshold:
            return 'medium'
        else:
            return 'small'
    
    def detect_volume_anomalies(self, symbol: str) -> Dict[str, Any]:
        """Detect volume anomalies using recent OHLCV data"""
        try:
            # Fetch recent OHLCV data
            ohlcv_data = self.fetch_ohlcv_data(symbol, '1m', 60)
            if not ohlcv_data or len(ohlcv_data) < 30:
                return self._get_default_volume_anomaly()
            
            # Calculate volume statistics
            volumes = [candle[5] for candle in ohlcv_data]
            current_volume = volumes[-1]
            avg_volume = sum(volumes[:-1]) / len(volumes[:-1])  # Exclude current candle
            
            # Calculate volume metrics
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            volume_z_score = (current_volume - avg_volume) / math.sqrt(sum((v - avg_volume) ** 2 for v in volumes[:-1]) / len(volumes[:-1])) if len(volumes) > 1 else 0
            
            # Detect anomalies
            is_volume_spike = volume_ratio >= self.volume_spike_threshold
            is_volume_drop = volume_ratio <= 0.3
            is_anomalous = abs(volume_z_score) > 2
            
            # Update baseline
            self.volume_baselines[symbol] = avg_volume
            
            return {
                'current_volume': current_volume,
                'average_volume': avg_volume,
                'volume_ratio': volume_ratio,
                'volume_z_score': volume_z_score,
                'is_volume_spike': is_volume_spike,
                'is_volume_drop': is_volume_drop,
                'is_anomalous': is_anomalous,
                'anomaly_type': self._classify_volume_anomaly(volume_ratio, volume_z_score)
            }
            
        except Exception as e:
            print(f"Error detecting volume anomalies for {symbol}: {e}")
            return self._get_default_volume_anomaly()
    
    def _classify_volume_anomaly(self, volume_ratio: float, volume_z_score: float) -> str:
        """Classify type of volume anomaly"""
        if volume_ratio >= 5:
            return 'extreme_spike'
        elif volume_ratio >= 3:
            return 'volume_spike'
        elif volume_ratio <= 0.2:
            return 'extreme_drop'
        elif volume_ratio <= 0.5:
            return 'volume_drop'
        elif abs(volume_z_score) > 3:
            return 'statistical_anomaly'
        else:
            return 'normal'
    
    def detect_price_anomalies(self, symbol: str) -> Dict[str, Any]:
        """Detect price anomalies using recent trades"""
        try:
            # Fetch recent trades
            trades = self.fetch_recent_trades(symbol, 100)
            if not trades or len(trades) < 20:
                return self._get_default_price_anomaly()
            
            # Calculate price statistics
            prices = [trade['price'] for trade in trades]
            current_price = prices[-1]
            avg_price = sum(prices[:-1]) / len(prices[:-1])
            
            # Calculate price metrics
            price_change = (current_price - avg_price) / avg_price * 100
            price_volatility = math.sqrt(sum((p - avg_price) ** 2 for p in prices[:-1]) / len(prices[:-1])) / avg_price * 100
            
            # Detect anomalies
            is_price_spike = abs(price_change) > self.anomaly_threshold * 100
            is_high_volatility = price_volatility > 5  # 5% volatility threshold
            
            # Update baseline
            self.price_baselines[symbol] = avg_price
            
            return {
                'current_price': current_price,
                'average_price': avg_price,
                'price_change_percent': price_change,
                'price_volatility': price_volatility,
                'is_price_spike': is_price_spike,
                'is_high_volatility': is_high_volatility,
                'anomaly_type': self._classify_price_anomaly(price_change, price_volatility)
            }
            
        except Exception as e:
            print(f"Error detecting price anomalies for {symbol}: {e}")
            return self._get_default_price_anomaly()
    
    def _classify_price_anomaly(self, price_change: float, volatility: float) -> str:
        """Classify type of price anomaly"""
        if abs(price_change) > 10:
            return 'extreme_move'
        elif abs(price_change) > 5:
            return 'significant_move'
        elif volatility > 10:
            return 'high_volatility'
        elif volatility > 5:
            return 'elevated_volatility'
        else:
            return 'normal'
    
    def detect_order_book_anomalies(self, order_book: Dict[str, Any]) -> Dict[str, Any]:
        """Detect anomalies in order book structure"""
        try:
            bids = order_book.get('bids', [])
            asks = order_book.get('asks', [])
            
            if not bids or not asks:
                return self._get_default_order_book_anomaly()
            
            # Calculate order book metrics
            bid_volumes = [bid[1] for bid in bids]
            ask_volumes = [ask[1] for ask in asks]
            
            total_bid_volume = sum(bid_volumes)
            total_ask_volume = sum(ask_volumes)
            
            # Calculate imbalance
            imbalance_ratio = (total_bid_volume - total_ask_volume) / (total_bid_volume + total_ask_volume) if (total_bid_volume + total_ask_volume) > 0 else 0
            
            # Detect structural anomalies
            is_imbalanced = abs(imbalance_ratio) > 0.3
            has_large_gaps = self._detect_price_gaps(bids, asks)
            has_unusual_depth = self._detect_depth_anomalies(bid_volumes, ask_volumes)
            
            return {
                'imbalance_ratio': imbalance_ratio,
                'total_bid_volume': total_bid_volume,
                'total_ask_volume': total_ask_volume,
                'is_imbalanced': is_imbalanced,
                'has_large_gaps': has_large_gaps,
                'has_unusual_depth': has_unusual_depth,
                'anomaly_type': self._classify_order_book_anomaly(imbalance_ratio, has_large_gaps, has_unusual_depth)
            }
            
        except Exception as e:
            print(f"Error detecting order book anomalies: {e}")
            return self._get_default_order_book_anomaly()
    
    def _detect_price_gaps(self, bids: List, asks: List) -> bool:
        """Detect large price gaps in order book"""
        try:
            if len(bids) < 2 or len(asks) < 2:
                return False
            
            # Check for gaps in bids
            for i in range(1, len(bids)):
                price_diff = bids[i-1][0] - bids[i][0]
                price_ratio = price_diff / bids[i][0]
                if price_ratio > 0.01:  # 1% gap
                    return True
            
            # Check for gaps in asks
            for i in range(1, len(asks)):
                price_diff = asks[i][0] - asks[i-1][0]
                price_ratio = price_diff / asks[i-1][0]
                if price_ratio > 0.01:  # 1% gap
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error detecting price gaps: {e}")
            return False
    
    def _detect_depth_anomalies(self, bid_volumes: List[float], ask_volumes: List[float]) -> bool:
        """Detect unusual depth patterns"""
        try:
            if len(bid_volumes) < 5 or len(ask_volumes) < 5:
                return False
            
            # Check for sudden volume drops
            for i in range(1, len(bid_volumes)):
                if bid_volumes[i] > 0 and bid_volumes[i-1] > 0:
                    volume_ratio = bid_volumes[i] / bid_volumes[i-1]
                    if volume_ratio < 0.1:  # 90% drop
                        return True
            
            for i in range(1, len(ask_volumes)):
                if ask_volumes[i] > 0 and ask_volumes[i-1] > 0:
                    volume_ratio = ask_volumes[i] / ask_volumes[i-1]
                    if volume_ratio < 0.1:  # 90% drop
                        return True
            
            return False
            
        except Exception as e:
            print(f"Error detecting depth anomalies: {e}")
            return False
    
    def _classify_order_book_anomaly(self, imbalance: float, has_gaps: bool, has_depth_anomaly: bool) -> str:
        """Classify type of order book anomaly"""
        if abs(imbalance) > 0.5:
            return 'extreme_imbalance'
        elif abs(imbalance) > 0.3:
            return 'significant_imbalance'
        elif has_gaps:
            return 'price_gaps'
        elif has_depth_anomaly:
            return 'depth_anomaly'
        else:
            return 'normal'
    
    def get_dark_pool_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive dark pool analysis"""
        try:
            # Check cache
            cache_key = f"dark_pool_{symbol}"
            if cache_key in self.detection_cache:
                cached_data = self.detection_cache[cache_key]
                if datetime.now().timestamp() - cached_data['timestamp'] < self.cache_expiry:
                    return cached_data['data']
            
            # Fetch order book
            order_book = self.fetch_order_book(symbol)
            if not order_book:
                return self._get_default_analysis(symbol)
            
            # Perform all detections
            large_orders = self.detect_large_orders(order_book)
            volume_anomalies = self.detect_volume_anomalies(symbol)
            price_anomalies = self.detect_price_anomalies(symbol)
            order_book_anomalies = self.detect_order_book_anomalies(order_book)
            
            # Calculate overall anomaly score
            anomaly_score = self._calculate_anomaly_score(
                large_orders, volume_anomalies, price_anomalies, order_book_anomalies
            )
            
            # Determine anomaly level
            if anomaly_score > 80:
                anomaly_level = 'high'
            elif anomaly_score > 50:
                anomaly_level = 'medium'
            else:
                anomaly_level = 'low'
            
            # Create analysis summary
            analysis = {
                'symbol': symbol,
                'anomaly_score': anomaly_score,
                'anomaly_level': anomaly_level,
                'large_orders': large_orders,
                'volume_anomalies': volume_anomalies,
                'price_anomalies': price_anomalies,
                'order_book_anomalies': order_book_anomalies,
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache the result
            self.detection_cache[cache_key] = {
                'data': analysis,
                'timestamp': datetime.now().timestamp()
            }
            
            return analysis
            
        except Exception as e:
            print(f"Error getting dark pool analysis for {symbol}: {e}")
            return self._get_default_analysis(symbol)
    
    def _calculate_anomaly_score(self, large_orders: Dict, volume_anomalies: Dict, 
                               price_anomalies: Dict, order_book_anomalies: Dict) -> float:
        """Calculate overall anomaly score (0-100)"""
        try:
            score = 0
            
            # Large orders contribution (0-30 points)
            if large_orders['large_order_count'] > 0:
                score += min(30, large_orders['large_order_count'] * 5)
            
            # Volume anomalies contribution (0-25 points)
            if volume_anomalies['is_anomalous']:
                score += 25
            elif volume_anomalies['is_volume_spike']:
                score += 15
            elif volume_anomalies['is_volume_drop']:
                score += 10
            
            # Price anomalies contribution (0-25 points)
            if price_anomalies['is_price_spike']:
                score += 25
            elif price_anomalies['is_high_volatility']:
                score += 15
            
            # Order book anomalies contribution (0-20 points)
            if order_book_anomalies['is_imbalanced']:
                score += 20
            elif order_book_anomalies['has_large_gaps']:
                score += 15
            elif order_book_anomalies['has_unusual_depth']:
                score += 10
            
            return min(100, score)
            
        except Exception as e:
            print(f"Error calculating anomaly score: {e}")
            return 0.0
    
    def _get_default_volume_anomaly(self) -> Dict[str, Any]:
        """Return default volume anomaly data"""
        return {
            'current_volume': 0,
            'average_volume': 0,
            'volume_ratio': 1,
            'volume_z_score': 0,
            'is_volume_spike': False,
            'is_volume_drop': False,
            'is_anomalous': False,
            'anomaly_type': 'normal'
        }
    
    def _get_default_price_anomaly(self) -> Dict[str, Any]:
        """Return default price anomaly data"""
        return {
            'current_price': 0,
            'average_price': 0,
            'price_change_percent': 0,
            'price_volatility': 0,
            'is_price_spike': False,
            'is_high_volatility': False,
            'anomaly_type': 'normal'
        }
    
    def _get_default_order_book_anomaly(self) -> Dict[str, Any]:
        """Return default order book anomaly data"""
        return {
            'imbalance_ratio': 0,
            'total_bid_volume': 0,
            'total_ask_volume': 0,
            'is_imbalanced': False,
            'has_large_gaps': False,
            'has_unusual_depth': False,
            'anomaly_type': 'normal'
        }
    
    def _get_default_analysis(self, symbol: str) -> Dict[str, Any]:
        """Return default analysis data"""
        return {
            'symbol': symbol,
            'anomaly_score': 0,
            'anomaly_level': 'low',
            'large_orders': self._get_default_volume_anomaly(),
            'volume_anomalies': self._get_default_volume_anomaly(),
            'price_anomalies': self._get_default_price_anomaly(),
            'order_book_anomalies': self._get_default_order_book_anomaly(),
            'timestamp': datetime.now().isoformat()
        } 