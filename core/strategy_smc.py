"""
Smart Money Concepts (SMC) Strategy Module
Implements order block, FVG, and breaker detection
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class SMCSignal:
    symbol: str
    signal_type: str  # 'LONG' or 'SHORT'
    entry: float
    stop_loss: float
    take_profit: Tuple[float, float, float]  # TP1, TP2, TP3
    confidence: int  # 1-5
    indicators: Dict[str, bool]
    market_data: Dict[str, Any]
    timestamp: datetime

class SMCStrategy:
    def __init__(self):
        self.name = "Smart Money Concepts"
        self.required_indicators = [
            'ema_20', 'ema_50', 'rsi', 'macd', 'vwap', 'atr', 'volume'
        ]
    
    def detect_order_blocks(self, data: pd.DataFrame, 
                          lookback_period: int = 50) -> List[Dict[str, Any]]:
        """Detect order blocks (OB) in the market data"""
        try:
            order_blocks = []
            
            if len(data) < lookback_period:
                return order_blocks
            
            # Look for impulsive moves with low volume retracements
            for i in range(lookback_period, len(data)):
                # Check for impulsive candle
                candle_body = abs(data['close'].iloc[i] - data['open'].iloc[i])
                candle_range = data['high'].iloc[i] - data['low'].iloc[i]
                
                # Impulsive candle: large body relative to range
                if candle_body > candle_range * 0.7 and candle_range > 0:
                    # Check if followed by small retracement candles
                    retracement_candles = 0
                    for j in range(i+1, min(i+5, len(data))):
                        retracement_body = abs(data['close'].iloc[j] - data['open'].iloc[j])
                        retracement_range = data['high'].iloc[j] - data['low'].iloc[j]
                        
                        if retracement_range > 0 and retracement_body < retracement_range * 0.3:
                            retracement_candles += 1
                    
                    # If we have at least 2 small retracement candles
                    if retracement_candles >= 2:
                        ob_type = 'bullish' if data['close'].iloc[i] > data['open'].iloc[i] else 'bearish'
                        order_blocks.append({
                            'type': ob_type,
                            'high': data['high'].iloc[i],
                            'low': data['low'].iloc[i],
                            'timestamp': i
                        })
            
            return order_blocks
        except Exception as e:
            print(f"Error in detect_order_blocks: {e}")
            return []
    
    def detect_fvg(self, data: pd.DataFrame, 
                   lookback_period: int = 50) -> List[Dict[str, Any]]:
        """Detect Fair Value Gaps (FVG)"""
        try:
            fvgs = []
            
            if len(data) < lookback_period + 2:
                return fvgs
            
            # Look for FVG patterns
            for i in range(lookback_period, len(data) - 2):
                # Bullish FVG: Low of candle i+2 > High of candle i
                if data['low'].iloc[i+2] > data['high'].iloc[i]:
                    fvgs.append({
                        'type': 'bullish',
                        'gap_top': data['low'].iloc[i+2],
                        'gap_bottom': data['high'].iloc[i],
                        'mitigated': False,
                        'timestamp': i
                    })
                
                # Bearish FVG: High of candle i+2 < Low of candle i
                elif data['high'].iloc[i+2] < data['low'].iloc[i]:
                    fvgs.append({
                        'type': 'bearish',
                        'gap_top': data['low'].iloc[i],
                        'gap_bottom': data['high'].iloc[i+2],
                        'mitigated': False,
                        'timestamp': i
                    })
            
            return fvgs
        except Exception as e:
            print(f"Error in detect_fvg: {e}")
            return []
    
    def detect_breaker_blocks(self, data: pd.DataFrame, 
                            lookback_period: int = 50) -> List[Dict[str, Any]]:
        """Detect breaker blocks that confirm order blocks"""
        try:
            breakers = []
            
            if len(data) < lookback_period + 3:
                return breakers
            
            # Look for breaker patterns
            for i in range(lookback_period, len(data) - 3):
                # Bullish breaker: Close above previous high with strong volume
                prev_high = data['high'].iloc[i-1]
                current_close = data['close'].iloc[i]
                
                if current_close > prev_high:
                    # Check volume confirmation
                    avg_volume = data['volume'].iloc[i-10:i].mean()
                    current_volume = data['volume'].iloc[i]
                    
                    if current_volume > avg_volume * 1.5:
                        breakers.append({
                            'type': 'bullish',
                            'level': prev_high,
                            'timestamp': i
                        })
                
                # Bearish breaker: Close below previous low with strong volume
                prev_low = data['low'].iloc[i-1]
                current_close = data['close'].iloc[i]
                
                if current_close < prev_low:
                    # Check volume confirmation
                    avg_volume = data['volume'].iloc[i-10:i].mean()
                    current_volume = data['volume'].iloc[i]
                    
                    if current_volume > avg_volume * 1.5:
                        breakers.append({
                            'type': 'bearish',
                            'level': prev_low,
                            'timestamp': i
                        })
            
            return breakers
        except Exception as e:
            print(f"Error in detect_breaker_blocks: {e}")
            return []
    
    def find_optimal_ob_retest(self, data: pd.DataFrame, 
                             order_blocks: List[Dict[str, Any]]) -> Optional[float]:
        """Find optimal order block retest level for entry"""
        try:
            if not order_blocks:
                return None
            
            # Get most recent order block
            latest_ob = order_blocks[-1]
            ob_type = latest_ob['type']
            
            if ob_type == 'bullish':
                # For bullish OB, look for retest near the high
                return latest_ob['high']
            else:
                # For bearish OB, look for retest near the low
                return latest_ob['low']
                
        except Exception as e:
            print(f"Error in find_optimal_ob_retest: {e}")
            return None
    
    def calculate_smc_targets(self, entry: float, atr: float, 
                            signal_type: str) -> Tuple[float, float, float, float]:
        """Calculate SL and TP levels for SMC strategy"""
        try:
            # SL: Beyond liquidity pool (2x ATR)
            sl_distance = atr * 2.0
            
            # TP levels: 2x imbalance
            tp1_distance = atr * 0.7
            tp2_distance = atr * 1.4
            tp3_distance = atr * 2.1
            
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
            print(f"Error in calculate_smc_targets: {e}")
            return 0, 0, 0, 0
    
    def validate_smc_setup(self, data: pd.DataFrame) -> Tuple[bool, Dict[str, bool]]:
        """Validate SMC setup with multiple confirmation layers"""
        try:
            indicators = {
                'order_block': False,
                'fvg': False,
                'breaker': False,
                'ema_confirmation': False,
                'volume_confirmation': False
            }
            
            # 1. Order block validation
            order_blocks = self.detect_order_blocks(data)
            indicators['order_block'] = len(order_blocks) > 0
            
            if not indicators['order_block']:
                return False, indicators
            
            # 2. FVG validation
            fvgs = self.detect_fvg(data)
            indicators['fvg'] = len(fvgs) > 0
            
            # 3. Breaker validation
            breakers = self.detect_breaker_blocks(data)
            indicators['breaker'] = len(breakers) > 0
            
            # 4. EMA confirmation
            if len(data) >= 50:
                ema_20 = data['ema_20'].iloc[-1]
                ema_50 = data['ema_50'].iloc[-1]
                prev_ema_20 = data['ema_20'].iloc[-2]
                prev_ema_50 = data['ema_50'].iloc[-2]
                
                # Golden cross or death cross confirmation
                indicators['ema_confirmation'] = (
                    (ema_20 > ema_50 and prev_ema_20 <= prev_ema_50) or  # Golden cross
                    (ema_20 < ema_50 and prev_ema_20 >= prev_ema_50)     # Death cross
                )
            
            # 5. Volume confirmation
            if len(data) >= 10:
                avg_volume = data['volume'].iloc[-10:-1].mean()
                current_volume = data['volume'].iloc[-1]
                indicators['volume_confirmation'] = current_volume > (avg_volume * 1.5)
            
            # At least 3 out of 5 confirmations required
            confirmations = sum(indicators.values())
            return confirmations >= 3, indicators
            
        except Exception as e:
            print(f"Error in validate_smc_setup: {e}")
            return False, {}
    
    def generate_signal(self, symbol: str, data: pd.DataFrame) -> Optional[SMCSignal]:
        """Generate SMC trading signal"""
        try:
            # Validate setup
            is_valid, indicators = self.validate_smc_setup(data)
            
            if not is_valid:
                return None
            
            # Determine signal type based on setup
            order_blocks = self.detect_order_blocks(data)
            if not order_blocks:
                return None
            
            latest_ob = order_blocks[-1]
            signal_type = 'LONG' if latest_ob['type'] == 'bullish' else 'SHORT'
            
            # Find optimal order block retest level
            entry = self.find_optimal_ob_retest(data, order_blocks)
            
            if not entry:
                return None
            
            # Calculate ATR for target calculation
            atr = data['atr'].iloc[-1] if len(data) > 0 else 0
            
            # Calculate SL and TP levels
            sl, tp1, tp2, tp3 = self.calculate_smc_targets(entry, atr, signal_type)
            
            # Calculate confidence based on confirmations
            confirmations = sum(indicators.values())
            confidence = min(5, confirmations)  # Max confidence is 5
            
            # Validate risk-reward ratio
            rr_ratio = abs(tp1 - entry) / abs(entry - sl) if sl != entry else 0
            if rr_ratio < 1.5:
                return None  # Skip signals with poor risk-reward
            
            # Create signal
            signal = SMCSignal(
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
                                  if len(data) >= 10 else 1,
                    'order_blocks_count': len(order_blocks)
                },
                timestamp=datetime.now()
            )
            
            return signal
            
        except Exception as e:
            print(f"Error in generate_smc_signal: {e}")
            return None
