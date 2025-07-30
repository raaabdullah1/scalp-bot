"""
Scalping Strategy Module
Implements high-frequency scalping with VWAP and momentum filters
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import math

@dataclass
class ScalpSignal:
    symbol: str
    signal_type: str  # 'LONG' or 'SHORT'
    entry: float
    stop_loss: float
    take_profit: Tuple[float, float, float]  # TP1, TP2, TP3
    confidence: int  # 1-5
    indicators: Dict[str, bool]
    market_data: Dict[str, Any]
    timestamp: datetime

class ScalpingStrategy:
    def __init__(self):
        self.name = "Scalping Protocol"
        self.required_indicators = [
            'ema_9', 'ema_21', 'rsi', 'vwap', 'atr', 'volume'
        ]
    
    def calculate_vwap_slope(self, data: pd.DataFrame, period: int = 20) -> float:
        """Calculate VWAP slope in degrees"""
        try:
            if len(data) < period:
                return 0
            
            vwap_values = data['vwap'].iloc[-period:]
            time_points = list(range(len(vwap_values)))
            
            # Calculate linear regression slope
            slope = np.polyfit(time_points, vwap_values, 1)[0]
            
            # Convert slope to degrees (assuming price units per bar)
            # This is a simplified conversion - in practice you might want to normalize
            slope_degrees = math.degrees(math.atan(slope / data['close'].iloc[-1] * 100))
            
            return slope_degrees
        except Exception as e:
            print(f"Error in calculate_vwap_slope: {e}")
            return 0
    
    def detect_volume_spike(self, data: pd.DataFrame, 
                          multiplier: float = 1.5) -> bool:
        """Detect volume spike compared to average"""
        try:
            if len(data) < 10:
                return False
            
            avg_volume = data['volume'].iloc[-10:-1].mean()
            current_volume = data['volume'].iloc[-1]
            
            return current_volume > (avg_volume * multiplier)
        except Exception as e:
            print(f"Error in detect_volume_spike: {e}")
            return False
    
    def calculate_chandelier_exit(self, data: pd.DataFrame, 
                                atr_period: int = 14, 
                                multiplier: float = 0.3) -> float:
        """Calculate Chandelier Exit for stop loss"""
        try:
            if len(data) < atr_period:
                return 0
            
            # Get highest high over ATR period
            highest_high = data['high'].iloc[-atr_period:].max()
            
            # Get latest ATR
            atr = data['atr'].iloc[-1] if len(data) > 0 else 0
            
            # Calculate Chandelier Exit
            chandelier_exit = highest_high - (atr * multiplier)
            
            return chandelier_exit
        except Exception as e:
            print(f"Error in calculate_chandelier_exit: {e}")
            return 0
    
    def validate_scalping_setup(self, data: pd.DataFrame) -> Tuple[bool, Dict[str, bool]]:
        """Validate scalping setup with multiple confirmation layers"""
        try:
            indicators = {
                'vwap_slope': False,
                'volume_spike': False,
                'rsi_filter': False,
                'ema_confirmation': False,
                'momentum_filter': False
            }
            
            # 1. VWAP slope > 30 degrees
            vwap_slope = self.calculate_vwap_slope(data)
            indicators['vwap_slope'] = vwap_slope > 30
            
            # 2. Volume spike > 1.5x average
            indicators['volume_spike'] = self.detect_volume_spike(data, 1.5)
            
            # 3. RSI in optimal range (40-60)
            if len(data) > 0:
                rsi = data['rsi'].iloc[-1]
                indicators['rsi_filter'] = 40 <= rsi <= 60
            
            # 4. EMA confirmation
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
            
            # 5. Momentum filter (price change > 0.2% in last 3 bars)
            if len(data) >= 3:
                price_change = (data['close'].iloc[-1] - data['close'].iloc[-3]) / data['close'].iloc[-3] * 100
                indicators['momentum_filter'] = abs(price_change) > 0.2
            
            # At least 4 out of 5 confirmations required for scalping
            confirmations = sum(indicators.values())
            return confirmations >= 4, indicators
            
        except Exception as e:
            print(f"Error in validate_scalping_setup: {e}")
            return False, {}
    
    def calculate_scalp_targets(self, entry: float, atr: float, 
                              signal_type: str) -> Tuple[float, float, float, float]:
        """Calculate SL and TP levels for scalping strategy"""
        try:
            # SL: 0.3% Chandelier exit
            sl_distance = entry * 0.003
            
            # TP levels: 0.5-1% trailing targets
            tp1_distance = entry * 0.005  # 0.5%
            tp2_distance = entry * 0.01   # 1.0%
            tp3_distance = entry * 0.015  # 1.5%
            
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
            print(f"Error in calculate_scalp_targets: {e}")
            return 0, 0, 0, 0
    
    def generate_signal(self, symbol: str, data: pd.DataFrame) -> Optional[ScalpSignal]:
        """Generate scalping trading signal"""
        try:
            # Validate setup
            is_valid, indicators = self.validate_scalping_setup(data)
            
            if not is_valid:
                return None
            
            # Determine signal type based on VWAP slope and EMA
            vwap_slope = self.calculate_vwap_slope(data)
            signal_type = 'LONG' if vwap_slope > 0 else 'SHORT'
            
            # Entry at market price
            entry = data['close'].iloc[-1]
            
            # Calculate ATR for target calculation
            atr = data['atr'].iloc[-1] if len(data) > 0 else 0
            
            # Calculate SL and TP levels
            sl, tp1, tp2, tp3 = self.calculate_scalp_targets(entry, atr, signal_type)
            
            # Calculate confidence based on confirmations
            confirmations = sum(indicators.values())
            confidence = min(5, confirmations)  # Max confidence is 5
            
            # Validate risk-reward ratio
            rr_ratio = abs(tp1 - entry) / abs(entry - sl) if sl != entry else 0
            if rr_ratio < 1.5:
                return None  # Skip signals with poor risk-reward
            
            # Create signal
            signal = ScalpSignal(
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
                    'vwap_slope': vwap_slope
                },
                timestamp=datetime.now()
            )
            
            return signal
            
        except Exception as e:
            print(f"Error in generate_scalp_signal: {e}")
            return None
