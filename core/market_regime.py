"""
Market Regime Detection Module
Detects market conditions and adjusts strategy weights accordingly
"""

import math
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

class MarketRegimeDetector:
    def __init__(self):
        self.regime_cache = {}
        self.cache_expiry = 300  # 5 minutes
        
        # Regime thresholds
        self.trend_threshold = 25  # ADX threshold for trend strength
        self.volatility_threshold = 0.02  # 2% volatility threshold
    
    def calculate_volatility_rank(self, prices: List[float]) -> float:
        """Calculate volatility rank using standard deviation"""
        try:
            if len(prices) < 2:
                return 0.0
            
            # Calculate returns
            returns = []
            for i in range(1, len(prices)):
                if prices[i-1] != 0:
                    return_val = (prices[i] - prices[i-1]) / prices[i-1]
                    returns.append(return_val)
            
            if len(returns) < 2:
                return 0.0
            
            # Calculate mean return
            mean_return = sum(returns) / len(returns)
            
            # Calculate standard deviation
            variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
            std_dev = math.sqrt(variance)
            
            # Annualize volatility (assuming hourly data for crypto)
            annualized_vol = std_dev * math.sqrt(8760)  # 8760 hours in a year
            
            return annualized_vol
            
        except Exception as e:
            print(f"Error calculating volatility rank: {e}")
            return 0.0
    
    def detect_trend_strength(self, adx_values: List[float]) -> str:
        """Detect trend strength based on ADX values"""
        try:
            if not adx_values:
                return 'sideways'
            
            current_adx = adx_values[-1]
            
            if current_adx > 40:
                return 'strong_trend'
            elif current_adx > 25:
                return 'moderate_trend'
            else:
                return 'sideways'
                
        except Exception as e:
            print(f"Error detecting trend strength: {e}")
            return 'sideways'
    
    def detect_volatility_regime(self, volatility: float) -> str:
        """Detect volatility regime"""
        try:
            if volatility > 0.8:  # 80% annualized volatility
                return 'high_volatility'
            elif volatility > 0.4:  # 40% annualized volatility
                return 'moderate_volatility'
            else:
                return 'low_volatility'
                
        except Exception as e:
            print(f"Error detecting volatility regime: {e}")
            return 'low_volatility'
    
    def detect_market_regime(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect overall market regime using DataFrame data"""
        try:
            symbol = data['symbol'].iloc[0] if 'symbol' in data.columns else 'unknown'
            
            # Check cache
            cache_key = f"regime_{symbol}"
            if cache_key in self.regime_cache:
                cached_data = self.regime_cache[cache_key]
                if datetime.now().timestamp() - cached_data['timestamp'] < self.cache_expiry:
                    return cached_data['data']
            
            if len(data) < 20:
                return self._get_default_regime(symbol)
            
            # Extract prices
            prices = data['close'].tolist()
            
            # Calculate volatility
            volatility = self.calculate_volatility_rank(prices)
            
            # Get ADX values
            adx_values = data['adx'].tolist() if 'adx' in data.columns else []
            
            # Detect regimes
            volatility_regime = self.detect_volatility_regime(volatility)
            trend_strength = self.detect_trend_strength(adx_values) if adx_values else 'unknown'
            
            # Determine overall regime
            if trend_strength == 'strong_trend' and volatility_regime == 'high_volatility':
                overall_regime = 'trending_volatile'
            elif trend_strength == 'strong_trend' and volatility_regime == 'low_volatility':
                overall_regime = 'trending_stable'
            elif trend_strength == 'sideways' and volatility_regime == 'high_volatility':
                overall_regime = 'sideways_volatile'
            else:
                overall_regime = 'sideways_stable'
            
            # Calculate strategy weights
            strategy_weights = self._calculate_strategy_weights(overall_regime, volatility)
            
            regime_data = {
                'symbol': symbol,
                'overall_regime': overall_regime,
                'trend_strength': trend_strength,
                'volatility_regime': volatility_regime,
                'volatility': volatility,
                'adx_value': adx_values[-1] if adx_values else 20,
                'volatility_rank': volatility * 100,  # Convert to 0-100 scale
                'strategy_weights': strategy_weights,
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache the result
            self.regime_cache[cache_key] = {
                'data': regime_data,
                'timestamp': datetime.now().timestamp()
            }
            
            return regime_data
            
        except Exception as e:
            print(f"Error detecting market regime: {e}")
            return self._get_default_regime('unknown')
    
    def _calculate_strategy_weights(self, regime: str, volatility: float) -> Dict[str, float]:
        """Calculate strategy weights based on market regime"""
        try:
            # New strategy weighting approach
            if regime == 'trending_volatile':
                # Strong trending, high volatility market - favor SMC
                return {'SMC': 0.6, 'Trap': 0.3, 'Scalp': 0.1}
            elif regime == 'trending_stable':
                # Strong trending, low volatility market - balanced approach
                return {'SMC': 0.5, 'Trap': 0.3, 'Scalp': 0.2}
            elif regime == 'sideways_volatile':
                # Sideways, high volatility market - favor Trap Trading
                return {'Trap': 0.6, 'SMC': 0.2, 'Scalp': 0.2}
            elif regime == 'sideways_stable':
                # Sideways, low volatility market - favor Scalping
                return {'Scalp': 0.7, 'Trap': 0.3, 'SMC': 0.0}
            else:
                # Default balanced approach
                return {'SMC': 0.4, 'Trap': 0.3, 'Scalp': 0.3}
                
        except Exception as e:
            print(f"Error calculating strategy weights: {e}")
            return {'SMC': 0.4, 'Trap': 0.3, 'Scalp': 0.3}
    
    def get_regime_summary(self, markets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary of market regimes across all markets"""
        try:
            if not markets:
                return self._get_default_summary()
            
            regime_counts = {}
            total_volatility = 0
            total_markets = len(markets)
            
            for market in markets:
                regime = market.get('overall_regime', 'unknown')
                volatility = market.get('volatility', 0)
                
                regime_counts[regime] = regime_counts.get(regime, 0) + 1
                total_volatility += volatility
            
            avg_volatility = total_volatility / total_markets if total_markets > 0 else 0
            
            # Determine dominant regime
            dominant_regime = max(regime_counts.items(), key=lambda x: x[1])[0] if regime_counts else 'unknown'
            
            return {
                'total_markets': total_markets,
                'regime_distribution': regime_counts,
                'dominant_regime': dominant_regime,
                'average_volatility': avg_volatility,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting regime summary: {e}")
            return self._get_default_summary()
    
    def _get_default_regime(self, symbol: str) -> Dict[str, Any]:
        """Return default regime data"""
        return {
            'symbol': symbol,
            'overall_regime': 'sideways_stable',
            'trend_strength': 'sideways',
            'volatility_regime': 'low_volatility',
            'volatility': 0.2,
            'adx_value': 20,
            'volatility_rank': 50,
            'strategy_weights': {
                'SMC': 0.4,
                'Trap': 0.3,
                'Scalp': 0.3
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_default_summary(self) -> Dict[str, Any]:
        """Return default summary data"""
        return {
            'total_markets': 0,
            'regime_distribution': {},
            'dominant_regime': 'unknown',
            'average_volatility': 0.0,
            'timestamp': datetime.now().isoformat()
        } 