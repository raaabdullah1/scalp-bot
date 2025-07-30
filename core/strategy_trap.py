"""
Trap Trading Strategy Module
Implements liquidity grab detection and trap trading logic
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TrapSignal:
    symbol: str
    signal_type: str  # 'LONG' or 'SHORT'
    entry: float
    stop_loss: float
    take_profit: Tuple[float, float, float]  # TP1, TP2, TP3
    confidence: int  # 1-5
    indicators: Dict[str, bool]
    market_data: Dict[str, Any]
    timestamp: datetime

class TrapTradingStrategy:
    def __init__(self):
        self.name = "Trap Trading"
        self.required_indicators = [
            'ema_9', 'ema_21', 'rsi', 'macd', 'vwap', 'atr', 'volume'
        ]
    
    def detect_liquidity_grab(self, liquidation_map: Dict[str, Any], 
                            order_flow: Dict[str, Any]) -> bool:
        """Detect liquidity grab patterns using liquidation data and order flow"""
        try:
            # Check for liquidation clusters
            if not liquidation_map or 'clusters' not in liquidation_map:
                return False
            
            clusters = liquidation_map.get('clusters', [])
            if not clusters:
                return False
            
            # Look for significant liquidation clusters
            significant_clusters = [
                cluster for cluster in clusters 
                if cluster.get('size', 0) > 100000  # $100k+ liquidations
            ]
            
            if not significant_clusters:
                return False
            
            # Check order flow confirmation
            if not order_flow or 'imbalance' not in order_flow:
                return False
            
            imbalance = order_flow.get('imbalance', 0)
            if abs(imbalance) < 0.3:  # Need at least 30% order book imbalance
                return False
            
            return True
        except Exception as e:
            print(f"Error in detect_liquidity_grab: {e}")
            return False
    
    def find_trap_confirmation_price(self, data: pd.DataFrame, 
                                   liquidation_clusters: list) -> Optional[float]:
        """Find optimal trap confirmation price based on liquidation clusters"""
        try:
            if not liquidation_clusters:
                return None
            
            # Get current price
            current_price = data['close'].iloc[-1]
            
            # Find nearest significant liquidation cluster
            nearest_cluster = None
            min_distance = float('inf')
            
            for cluster in liquidation_clusters:
                cluster_price = cluster.get('price', 0)
                distance = abs(current_price - cluster_price)
                if distance < min_distance:
                    min_distance = distance
                    nearest_cluster = cluster
            
            if not nearest_cluster:
                return None
            
            # Set trap confirmation price with buffer
            buffer = current_price * 0.001  # 0.1% buffer
            cluster_price = nearest_cluster.get('price', 0)
            
            if current_price > cluster_price:
                # Price above cluster - look for short trap
                return cluster_price - buffer
            else:
                # Price below cluster - look for long trap
                return cluster_price + buffer
                
        except Exception as e:
            print(f"Error in find_trap_confirmation_price: {e}")
            return None
    
    def calculate_trap_targets(self, entry: float, atr: float, 
                             signal_type: str) -> Tuple[float, float, float, float]:
        """Calculate SL and TP levels for trap trading"""
        try:
            # SL: Next liquidation cluster or 1.5x ATR
            sl_distance = atr * 1.5
            
            # TP levels: 1:3 risk-reward ratio
            tp1_distance = atr * 0.5
            tp2_distance = atr * 1.0
            tp3_distance = atr * 1.5
            
            if signal_type == 'LONG':
                stop_loss = entry - sl_distance
                tp1 = entry + tp1_distance
                tp2 = entry + tp2_distance
                tp3 = entry + tp3_distance
            else:  # SHORT
                stop_loss = entry + sl_distance
                tp1 = entry - tp1_distance
                tp2 = entry - tp2_distance
                tp3 = entry - tp3_distance
            
            return stop_loss, tp1, tp2, tp3
        except Exception as e:
            print(f"Error in calculate_trap_targets: {e}")
            return 0, 0, 0, 0
    
    def validate_trap_setup(self, data: pd.DataFrame, 
                          liquidation_data: Dict[str, Any],
                          order_flow: Dict[str, Any]) -> Tuple[bool, Dict[str, bool]]:
        """Validate trap trading setup with multiple confirmation layers"""
        try:
            indicators = {
                'liquidity_grab': False,
                'ema_confirmation': False,
                'volume_confirmation': False,
                'rsi_divergence': False,
                'macd_confirmation': False
            }
            
            # 1. Liquidity grab detection
            indicators['liquidity_grab'] = self.detect_liquidity_grab(
                liquidation_data, order_flow)
            
            if not indicators['liquidity_grab']:
                return False, indicators
            
            # 2. EMA confirmation
            if len(data) >= 21:
                ema_9 = data['ema_9'].iloc[-1]
                ema_21 = data['ema_21'].iloc[-1]
                prev_ema_9 = data['ema_9'].iloc[-2]
                prev_ema_21 = data['ema_21'].iloc[-2]
                
                # Golden cross or death cross confirmation
                indicators['ema_confirmation'] = (
                    (ema_9 > ema_21 and prev_ema_9 <= prev_ema_21) or  # Golden cross
                    (ema_9 < ema_21 and prev_ema_9 >= prev_ema_21)     # Death cross
                )
            
            # 3. Volume confirmation
            if len(data) >= 10:
                avg_volume = data['volume'].iloc[-10:-1].mean()
                current_volume = data['volume'].iloc[-1]
                indicators['volume_confirmation'] = current_volume > (avg_volume * 1.5)
            
            # 4. RSI divergence
            if len(data) >= 14:
                rsi_values = data['rsi'].iloc[-14:]
                price_values = data['close'].iloc[-14:]
                
                # Check for bullish or bearish divergence
                price_slope = np.polyfit(range(len(price_values)), price_values, 1)[0]
                rsi_slope = np.polyfit(range(len(rsi_values)), rsi_values, 1)[0]
                
                # Bullish divergence: price making lower lows, RSI making higher lows
                # Bearish divergence: price making higher highs, RSI making lower highs
                indicators['rsi_divergence'] = (
                    (price_slope < 0 and rsi_slope > 0) or  # Bullish divergence
                    (price_slope > 0 and rsi_slope < 0)     # Bearish divergence
                )
            
            # 5. MACD confirmation
            if len(data) >= 26:
                macd_line = data['macd'].iloc[-1]
                signal_line = data['macd_signal'].iloc[-1]
                prev_macd = data['macd'].iloc[-2]
                prev_signal = data['macd_signal'].iloc[-2]
                
                # MACD crossover
                indicators['macd_confirmation'] = (
                    (macd_line > signal_line and prev_macd <= prev_signal) or  # Bullish crossover
                    (macd_line < signal_line and prev_macd >= prev_signal)     # Bearish crossover
                )
            
            # At least 3 out of 5 confirmations required
            confirmations = sum(indicators.values())
            return confirmations >= 3, indicators
            
        except Exception as e:
            print(f"Error in validate_trap_setup: {e}")
            return False, {}
    
    def generate_signal(self, symbol: str, data: pd.DataFrame, 
                       liquidation_data: Dict[str, Any],
                       order_flow: Dict[str, Any]) -> Optional[TrapSignal]:
        """Generate trap trading signal"""
        try:
            # Validate setup
            is_valid, indicators = self.validate_trap_setup(
                data, liquidation_data, order_flow)
            
            if not is_valid:
                return None
            
            # Determine signal type based on setup
            signal_type = 'LONG' if indicators.get('ema_confirmation') and \
                         data['ema_9'].iloc[-1] > data['ema_21'].iloc[-1] else 'SHORT'
            
            # Find trap confirmation price
            clusters = liquidation_data.get('clusters', [])
            entry = self.find_trap_confirmation_price(data, clusters)
            
            if not entry:
                return None
            
            # Calculate ATR for target calculation
            atr = data['atr'].iloc[-1] if len(data) > 0 else 0
            
            # Calculate SL and TP levels
            sl, tp1, tp2, tp3 = self.calculate_trap_targets(entry, atr, signal_type)
            
            # Calculate confidence based on confirmations
            confirmations = sum(indicators.values())
            confidence = min(5, confirmations)  # Max confidence is 5
            
            # Validate risk-reward ratio
            rr_ratio = abs(tp1 - entry) / abs(entry - sl) if sl != entry else 0
            if rr_ratio < 1.5:
                return None  # Skip signals with poor risk-reward
            
            # Create signal
            signal = TrapSignal(
                symbol=symbol,
                signal_type=signal_type,
                entry=round(entry, 6),
                stop_loss=round(sl, 6),
                take_profit=(round(tp1, 6), round(tp2, 6), round(tp3, 6)),
                confidence=confidence,
                indicators=indicators,
                market_data={
                    'atr': atr,
                    'volume_ratio': data['volume'].iloc[-1] / data['volume'].iloc[-10:-1].mean() \
                                  if len(data) >= 10 else 1
                },
                timestamp=datetime.now()
            )
            
            return signal
            
        except Exception as e:
            print(f"Error in generate_trap_signal: {e}")
            return None
