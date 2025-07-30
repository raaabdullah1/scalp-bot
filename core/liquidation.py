"""
Liquidation Analysis Module
Uses free CCXT order book analysis to detect liquidation clusters and zones
"""

import ccxt
import time
import math
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

class LiquidationAnalyzer:
    def __init__(self):
        # Initialize CCXT with public access (no auth required)
        self.exchange = ccxt.binance({
            'options': {'defaultType': 'future'},
            'enableRateLimit': True
        })
        
        # Liquidation analysis parameters
        self.large_order_threshold = 20  # BTC equivalent for large orders
        self.cluster_threshold = 0.5     # Price range for clustering (%)
        self.liquidation_risk_threshold = 0.7  # Risk threshold for alerts
        
        # Cache for liquidation data
        self.liquidation_cache = {}
        self.cache_expiry = 60  # 1 minute cache
        
    def fetch_order_book(self, symbol: str, limit: int = 20) -> Optional[Dict[str, Any]]:
        """Fetch order book data (public method)"""
        try:
            order_book = self.exchange.fetch_order_book(symbol, limit=limit)
            return dict(order_book) if order_book is not None else None
        except Exception as e:
            print(f"Error fetching order book for {symbol}: {e}")
            return None
    
    def analyze_order_book_imbalance(self, order_book: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze order book imbalance to detect potential liquidation zones"""
        try:
            bids = order_book.get('bids', [])
            asks = order_book.get('asks', [])
            
            if not bids or not asks:
                return self._get_default_imbalance()
            
            # Calculate total volume at different price levels
            bid_volumes = {}
            ask_volumes = {}
            
            # Aggregate bid volumes
            for price, volume in bids:
                price_key = round(price, 2)  # Round to 2 decimal places
                bid_volumes[price_key] = bid_volumes.get(price_key, 0) + volume
            
            # Aggregate ask volumes
            for price, volume in asks:
                price_key = round(price, 2)  # Round to 2 decimal places
                ask_volumes[price_key] = ask_volumes.get(price_key, 0) + volume
            
            # Calculate mid price
            best_bid = bids[0][0]
            best_ask = asks[0][0]
            mid_price = (best_bid + best_ask) / 2
            
            # Find large order clusters
            large_bid_clusters = self._find_large_clusters(bid_volumes, mid_price, 'bid')
            large_ask_clusters = self._find_large_clusters(ask_volumes, mid_price, 'ask')
            
            # Calculate imbalance ratio
            total_bid_volume = sum(bid_volumes.values())
            total_ask_volume = sum(ask_volumes.values())
            
            if total_bid_volume + total_ask_volume == 0:
                imbalance_ratio = 0
            else:
                imbalance_ratio = (total_bid_volume - total_ask_volume) / (total_bid_volume + total_ask_volume)
            
            # Detect potential liquidation zones
            liquidation_zones = self._detect_liquidation_zones(
                large_bid_clusters, large_ask_clusters, mid_price
            )
            
            return {
                'imbalance_ratio': imbalance_ratio,
                'total_bid_volume': total_bid_volume,
                'total_ask_volume': total_ask_volume,
                'mid_price': mid_price,
                'large_bid_clusters': large_bid_clusters,
                'large_ask_clusters': large_ask_clusters,
                'liquidation_zones': liquidation_zones,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error analyzing order book imbalance: {e}")
            return self._get_default_imbalance()
    
    def _find_large_clusters(self, volumes: Dict[float, float], mid_price: float, side: str) -> List[Dict[str, Any]]:
        """Find large order clusters in order book"""
        try:
            clusters = []
            sorted_prices = sorted(volumes.keys())
            
            if not sorted_prices:
                return clusters
            
            # Group nearby prices into clusters
            current_cluster = {
                'start_price': sorted_prices[0],
                'end_price': sorted_prices[0],
                'total_volume': volumes[sorted_prices[0]],
                'order_count': 1,
                'side': side
            }
            
            for i in range(1, len(sorted_prices)):
                price = sorted_prices[i]
                prev_price = sorted_prices[i-1]
                
                # Check if price is within cluster threshold
                price_diff = abs(price - prev_price) / mid_price
                
                if price_diff <= self.cluster_threshold / 100:
                    # Extend current cluster
                    current_cluster['end_price'] = price
                    current_cluster['total_volume'] += volumes[price]
                    current_cluster['order_count'] += 1
                else:
                    # Check if current cluster is large enough
                    if current_cluster['total_volume'] >= self.large_order_threshold:
                        clusters.append(current_cluster.copy())
                    
                    # Start new cluster
                    current_cluster = {
                        'start_price': price,
                        'end_price': price,
                        'total_volume': volumes[price],
                        'order_count': 1,
                        'side': side
                    }
            
            # Check final cluster
            if current_cluster['total_volume'] >= self.large_order_threshold:
                clusters.append(current_cluster)
            
            return clusters
            
        except Exception as e:
            print(f"Error finding large clusters: {e}")
            return []
    
    def _detect_liquidation_zones(self, bid_clusters: List[Dict], ask_clusters: List[Dict], mid_price: float) -> List[Dict[str, Any]]:
        """Detect potential liquidation zones based on order clusters"""
        try:
            liquidation_zones = []
            
            # Analyze bid clusters for potential long liquidation zones
            for cluster in bid_clusters:
                if cluster['side'] == 'bid':
                    # Large bid cluster might indicate support zone
                    # If price breaks below this zone, it could trigger long liquidations
                    zone = {
                        'type': 'long_liquidation_zone',
                        'price_range': (cluster['start_price'], cluster['end_price']),
                        'volume': cluster['total_volume'],
                        'risk_level': self._calculate_risk_level(cluster['total_volume']),
                        'distance_from_mid': (mid_price - cluster['end_price']) / mid_price * 100
                    }
                    liquidation_zones.append(zone)
            
            # Analyze ask clusters for potential short liquidation zones
            for cluster in ask_clusters:
                if cluster['side'] == 'ask':
                    # Large ask cluster might indicate resistance zone
                    # If price breaks above this zone, it could trigger short liquidations
                    zone = {
                        'type': 'short_liquidation_zone',
                        'price_range': (cluster['start_price'], cluster['end_price']),
                        'volume': cluster['total_volume'],
                        'risk_level': self._calculate_risk_level(cluster['total_volume']),
                        'distance_from_mid': (cluster['start_price'] - mid_price) / mid_price * 100
                    }
                    liquidation_zones.append(zone)
            
            return liquidation_zones
            
        except Exception as e:
            print(f"Error detecting liquidation zones: {e}")
            return []
    
    def _calculate_risk_level(self, volume: float) -> str:
        """Calculate risk level based on volume"""
        if volume >= self.large_order_threshold * 3:
            return 'high'
        elif volume >= self.large_order_threshold * 2:
            return 'medium'
        elif volume >= self.large_order_threshold:
            return 'low'
        else:
            return 'minimal'
    
    def get_liquidation_density(self, symbol: str) -> float:
        """Get liquidation density score (0-100) based on order book analysis"""
        try:
            # Check cache
            cache_key = f"liquidation_{symbol}"
            if cache_key in self.liquidation_cache:
                cached_data = self.liquidation_cache[cache_key]
                if datetime.now().timestamp() - cached_data['timestamp'] < self.cache_expiry:
                    return cached_data['density']
            
            # Fetch order book
            order_book = self.fetch_order_book(symbol)
            if not order_book:
                return 50.0  # Default value
            
            # Analyze imbalance
            analysis = self.analyze_order_book_imbalance(order_book)
            
            # Calculate density score based on imbalance and clusters
            imbalance_ratio = abs(analysis['imbalance_ratio'])
            cluster_count = len(analysis['large_bid_clusters']) + len(analysis['large_ask_clusters'])
            
            # Weight factors
            imbalance_weight = 0.6
            cluster_weight = 0.4
            
            # Calculate density score (0-100)
            density_score = (
                imbalance_ratio * 100 * imbalance_weight +
                min(cluster_count * 10, 100) * cluster_weight
            )
            
            # Cache the result
            self.liquidation_cache[cache_key] = {
                'density': density_score,
                'timestamp': datetime.now().timestamp()
            }
            
            return min(100, max(0, density_score))
            
        except Exception as e:
            print(f"Error getting liquidation density for {symbol}: {e}")
            return 50.0  # Default value
    
    def get_liquidation_clusters(self, symbol: str) -> Dict[str, Any]:
        """Get detailed liquidation cluster information"""
        try:
            # Fetch order book
            order_book = self.fetch_order_book(symbol)
            if not order_book:
                return self._get_default_clusters()
            
            # Analyze order book
            analysis = self.analyze_order_book_imbalance(order_book)
            
            # Calculate cluster statistics
            total_clusters = len(analysis['large_bid_clusters']) + len(analysis['large_ask_clusters'])
            total_volume = analysis['total_bid_volume'] + analysis['total_ask_volume']
            
            # Find high-risk zones
            high_risk_zones = [
                zone for zone in analysis['liquidation_zones']
                if zone['risk_level'] in ['high', 'medium']
            ]
            
            return {
                'symbol': symbol,
                'total_clusters': total_clusters,
                'total_volume': total_volume,
                'imbalance_ratio': analysis['imbalance_ratio'],
                'mid_price': analysis['mid_price'],
                'bid_clusters': analysis['large_bid_clusters'],
                'ask_clusters': analysis['large_ask_clusters'],
                'liquidation_zones': analysis['liquidation_zones'],
                'high_risk_zones': high_risk_zones,
                'risk_score': self._calculate_overall_risk(analysis),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting liquidation clusters for {symbol}: {e}")
            return self._get_default_clusters()
    
    def _calculate_overall_risk(self, analysis: Dict[str, Any]) -> float:
        """Calculate overall liquidation risk score (0-100)"""
        try:
            # Factors contributing to risk
            imbalance_risk = abs(analysis['imbalance_ratio']) * 50
            cluster_risk = min(len(analysis['large_bid_clusters']) + len(analysis['large_ask_clusters']), 10) * 5
            zone_risk = len(analysis['liquidation_zones']) * 3
            
            # Calculate weighted risk score
            risk_score = imbalance_risk + cluster_risk + zone_risk
            
            return min(100, max(0, risk_score))
            
        except Exception as e:
            print(f"Error calculating overall risk: {e}")
            return 50.0
    
    def predict_liquidation_cascade(self, symbol: str, current_price: float) -> Dict[str, Any]:
        """Predict potential liquidation cascade based on order book analysis"""
        try:
            # Get liquidation clusters
            clusters_data = self.get_liquidation_clusters(symbol)
            
            # Find nearby liquidation zones
            nearby_zones = []
            for zone in clusters_data['liquidation_zones']:
                zone_mid = (zone['price_range'][0] + zone['price_range'][1]) / 2
                distance = abs(current_price - zone_mid) / current_price * 100
                
                if distance <= 5:  # Within 5% of current price
                    nearby_zones.append({
                        **zone,
                        'distance': distance,
                        'cascade_probability': self._calculate_cascade_probability(zone, distance)
                    })
            
            # Sort by cascade probability
            nearby_zones.sort(key=lambda x: x['cascade_probability'], reverse=True)
            
            # Calculate overall cascade risk
            if nearby_zones:
                max_cascade_prob = max(zone['cascade_probability'] for zone in nearby_zones)
                avg_cascade_prob = sum(zone['cascade_probability'] for zone in nearby_zones) / len(nearby_zones)
            else:
                max_cascade_prob = 0
                avg_cascade_prob = 0
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'nearby_zones': nearby_zones,
                'max_cascade_probability': max_cascade_prob,
                'avg_cascade_probability': avg_cascade_prob,
                'overall_risk': 'high' if max_cascade_prob > 70 else 'medium' if max_cascade_prob > 40 else 'low',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error predicting liquidation cascade for {symbol}: {e}")
            return self._get_default_cascade_prediction(symbol, current_price)
    
    def _calculate_cascade_probability(self, zone: Dict[str, Any], distance: float) -> float:
        """Calculate probability of liquidation cascade for a zone"""
        try:
            # Base probability from risk level
            risk_multipliers = {
                'high': 0.8,
                'medium': 0.5,
                'low': 0.3,
                'minimal': 0.1
            }
            
            base_prob = risk_multipliers.get(zone['risk_level'], 0.3)
            
            # Adjust for distance (closer = higher probability)
            distance_factor = max(0, 1 - distance / 5)  # 0% distance = 100% factor
            
            # Adjust for volume (higher volume = higher probability)
            volume_factor = min(1, zone['volume'] / (self.large_order_threshold * 5))
            
            # Calculate final probability
            probability = base_prob * distance_factor * volume_factor
            
            return min(100, probability * 100)
            
        except Exception as e:
            print(f"Error calculating cascade probability: {e}")
            return 0.0
    
    def _get_default_imbalance(self) -> Dict[str, Any]:
        """Return default imbalance data"""
        return {
            'imbalance_ratio': 0,
            'total_bid_volume': 0,
            'total_ask_volume': 0,
            'mid_price': 0,
            'large_bid_clusters': [],
            'large_ask_clusters': [],
            'liquidation_zones': [],
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_default_clusters(self) -> Dict[str, Any]:
        """Return default cluster data"""
        return {
            'symbol': '',
            'total_clusters': 0,
            'total_volume': 0,
            'imbalance_ratio': 0,
            'mid_price': 0,
            'bid_clusters': [],
            'ask_clusters': [],
            'liquidation_zones': [],
            'high_risk_zones': [],
            'risk_score': 50.0,
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_default_cascade_prediction(self, symbol: str, current_price: float) -> Dict[str, Any]:
        """Return default cascade prediction"""
        return {
            'symbol': symbol,
            'current_price': current_price,
            'nearby_zones': [],
            'max_cascade_probability': 0,
            'avg_cascade_probability': 0,
            'overall_risk': 'low',
            'timestamp': datetime.now().isoformat()
        } 