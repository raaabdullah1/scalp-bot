"""
Technical Indicators Module
Uses free CCXT data for comprehensive technical analysis
"""

import math
import ccxt
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

class TechnicalIndicators:
    def __init__(self):
        # Initialize CCXT with public access (no auth required)
        self.exchange = ccxt.binance({
            'options': {'defaultType': 'future'},
            'enableRateLimit': True
        })
        
    def get_ohlcv_data(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> Optional[List]:
        """Get OHLCV data using CCXT (free)"""
        try:
            # Fetch OHLCV data
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            if ohlcv and len(ohlcv) > 0:
                return ohlcv
            else:
                return None
                
        except Exception as e:
            print(f"Error fetching OHLCV data for {symbol}: {e}")
            return None

    def calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return prices
        
        ema_values = []
        multiplier = 2 / (period + 1)
        
        # First EMA is SMA
        sma = sum(prices[:period]) / period
        ema_values.append(sma)
        
        for i in range(1, len(prices)):
            ema = (prices[i] * multiplier) + (ema_values[-1] * (1 - multiplier))
            ema_values.append(ema)
        
        return ema_values

    def calculate_sma(self, prices: List[float], period: int) -> List[float]:
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return prices
        
        sma_values = []
        for i in range(period - 1, len(prices)):
            sma = sum(prices[i - period + 1:i + 1]) / period
            sma_values.append(sma)
        
        return sma_values

    def calculate_macd(self, prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, List[float]]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        if len(prices) < slow:
            return {'macd': [], 'signal': [], 'histogram': []}
        
        ema_fast = self.calculate_ema(prices, fast)
        ema_slow = self.calculate_ema(prices, slow)
        
        # Calculate MACD line
        macd_line = []
        for i in range(len(ema_slow)):
            if i < len(ema_fast):
                macd_line.append(ema_fast[i] - ema_slow[i])
            else:
                macd_line.append(0)
        
        # Calculate signal line
        signal_line = self.calculate_ema(macd_line, signal)
        
        # Calculate histogram
        histogram = []
        for i in range(len(signal_line)):
            if i < len(macd_line):
                histogram.append(macd_line[i] - signal_line[i])
            else:
                histogram.append(0)
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }

    def calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return []
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        rsi_values = []
        for i in range(period, len(prices)):
            avg_gain = sum(gains[i-period:i]) / period
            avg_loss = sum(losses[i-period:i]) / period
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            rsi_values.append(rsi)
        
        return rsi_values

    def calculate_vwap(self, ohlcv_data: List[List[float]]) -> List[float]:
        """Calculate Volume Weighted Average Price"""
        if not ohlcv_data:
            return []
        
        vwap_values = []
        cumulative_tp_volume = 0
        cumulative_volume = 0
        
        for candle in ohlcv_data:
            high, low, close, volume = candle[2], candle[3], candle[4], candle[5]
            typical_price = (high + low + close) / 3
            tp_volume = typical_price * volume
            
            cumulative_tp_volume += tp_volume
            cumulative_volume += volume
            
            if cumulative_volume > 0:
                vwap = cumulative_tp_volume / cumulative_volume
                vwap_values.append(vwap)
            else:
                vwap_values.append(typical_price)
        
        return vwap_values

    def calculate_atr(self, ohlcv_data: List[List[float]], period: int = 14) -> List[float]:
        """Calculate Average True Range"""
        if len(ohlcv_data) < period + 1:
            return []
        
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
        
        atr_values = []
        for i in range(period - 1, len(true_ranges)):
            atr = sum(true_ranges[i-period+1:i+1]) / period
            atr_values.append(atr)
        
        return atr_values

    def calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: float = 2) -> Dict[str, List[float]]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            return {'upper': [], 'middle': [], 'lower': []}
        
        sma_values = self.calculate_sma(prices, period)
        upper_band = []
        lower_band = []
        
        for i in range(len(sma_values)):
            start_idx = i
            end_idx = min(i + period, len(prices))
            period_prices = prices[start_idx:end_idx]
            
            if len(period_prices) > 1:
                mean = sum(period_prices) / len(period_prices)
                variance = sum((p - mean) ** 2 for p in period_prices) / len(period_prices)
                std = math.sqrt(variance)
                
                upper_band.append(sma_values[i] + (std_dev * std))
                lower_band.append(sma_values[i] - (std_dev * std))
            else:
                upper_band.append(sma_values[i])
                lower_band.append(sma_values[i])
        
        return {
            'upper': upper_band,
            'middle': sma_values,
            'lower': lower_band
        }

    def calculate_stochastic(self, ohlcv_data: List[List[float]], k_period: int = 14, d_period: int = 3) -> Dict[str, List[float]]:
        """Calculate Stochastic Oscillator"""
        if len(ohlcv_data) < k_period:
            return {'k': [], 'd': []}
        
        k_values = []
        for i in range(k_period - 1, len(ohlcv_data)):
            high_prices = [ohlcv_data[j][2] for j in range(i - k_period + 1, i + 1)]
            low_prices = [ohlcv_data[j][3] for j in range(i - k_period + 1, i + 1)]
            close = ohlcv_data[i][4]
            
            highest_high = max(high_prices)
            lowest_low = min(low_prices)
            
            if highest_high == lowest_low:
                k = 50
            else:
                k = ((close - lowest_low) / (highest_high - lowest_low)) * 100
            
            k_values.append(k)
        
        # Calculate %D (SMA of %K)
        d_values = self.calculate_sma(k_values, d_period)
        
        return {
            'k': k_values,
            'd': d_values
        }

    def calculate_adx(self, ohlcv_data: List[List[float]], period: int = 14) -> List[float]:
        """Calculate Average Directional Index"""
        if len(ohlcv_data) < period + 1:
            return []
        
        # Calculate +DM and -DM
        plus_dm = []
        minus_dm = []
        true_ranges = []
        
        for i in range(1, len(ohlcv_data)):
            high = ohlcv_data[i][2]
            low = ohlcv_data[i][3]
            prev_high = ohlcv_data[i-1][2]
            prev_low = ohlcv_data[i-1][3]
            
            # True Range
            tr1 = high - low
            tr2 = abs(high - prev_high)
            tr3 = abs(low - prev_low)
            tr = max(tr1, tr2, tr3)
            true_ranges.append(tr)
            
            # Directional Movement
            up_move = high - prev_high
            down_move = prev_low - low
            
            if up_move > down_move and up_move > 0:
                plus_dm.append(up_move)
                minus_dm.append(0)
            elif down_move > up_move and down_move > 0:
                plus_dm.append(0)
                minus_dm.append(down_move)
            else:
                plus_dm.append(0)
                minus_dm.append(0)
        
        # Calculate smoothed values
        adx_values = []
        for i in range(period, len(true_ranges)):
            tr_sum = sum(true_ranges[i-period:i])
            plus_di = (sum(plus_dm[i-period:i]) / tr_sum) * 100
            minus_di = (sum(minus_dm[i-period:i]) / tr_sum) * 100
            
            dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100 if (plus_di + minus_di) > 0 else 0
            
            if i >= period * 2 - 1:
                # Calculate ADX
                dx_values = []
                for j in range(i - period + 1, i + 1):
                    tr_sum_j = sum(true_ranges[j-period:j])
                    plus_di_j = (sum(plus_dm[j-period:j]) / tr_sum_j) * 100
                    minus_di_j = (sum(minus_dm[j-period:j]) / tr_sum_j) * 100
                    dx_j = abs(plus_di_j - minus_di_j) / (plus_di_j + minus_di_j) * 100 if (plus_di_j + minus_di_j) > 0 else 0
                    dx_values.append(dx_j)
                
                adx = sum(dx_values) / len(dx_values)
                adx_values.append(adx)
        
        return adx_values

    def detect_ema_crossover(self, ema_fast: List[float], ema_slow: List[float]) -> Dict[str, Any]:
        """Detect EMA crossover signals"""
        if len(ema_fast) < 2 or len(ema_slow) < 2:
            return {'signal': 'none', 'strength': 0}
        
        current_fast = ema_fast[-1]
        current_slow = ema_slow[-1]
        prev_fast = ema_fast[-2]
        prev_slow = ema_slow[-2]
        
        # Check for crossover
        if prev_fast <= prev_slow and current_fast > current_slow:
            # Bullish crossover
            strength = (current_fast - current_slow) / current_slow * 100
            return {'signal': 'bullish', 'strength': strength}
        elif prev_fast >= prev_slow and current_fast < current_slow:
            # Bearish crossover
            strength = (current_slow - current_fast) / current_fast * 100
            return {'signal': 'bearish', 'strength': strength}
        else:
            return {'signal': 'none', 'strength': 0}

    def detect_macd_signal(self, macd_data: Dict[str, List[float]]) -> Dict[str, Any]:
        """Detect MACD signals"""
        if not macd_data or not macd_data.get('macd') or not macd_data.get('signal'):
            return {'signal': 'none', 'strength': 0}
        
        macd_line = macd_data['macd']
        signal_line = macd_data['signal']
        
        if len(macd_line) < 2 or len(signal_line) < 2:
            return {'signal': 'none', 'strength': 0}
        
        current_macd = macd_line[-1]
        current_signal = signal_line[-1]
        prev_macd = macd_line[-2]
        prev_signal = signal_line[-2]
        
        # Check for crossover
        if prev_macd <= prev_signal and current_macd > current_signal:
            # Bullish crossover
            strength = (current_macd - current_signal) / abs(current_signal) * 100 if current_signal != 0 else 0
            return {'signal': 'bullish', 'strength': strength}
        elif prev_macd >= prev_signal and current_macd < current_signal:
            # Bearish crossover
            strength = (current_signal - current_macd) / abs(current_macd) * 100 if current_macd != 0 else 0
            return {'signal': 'bearish', 'strength': strength}
        else:
            return {'signal': 'none', 'strength': 0}

    def detect_rsi_signal(self, rsi_values: List[float]) -> Dict[str, Any]:
        """Detect RSI signals"""
        if len(rsi_values) < 2:
            return {'signal': 'none', 'strength': 0}
        
        current_rsi = rsi_values[-1]
        prev_rsi = rsi_values[-2]
        
        # Overbought/oversold conditions
        if current_rsi > 70 and prev_rsi <= 70:
            return {'signal': 'bearish', 'strength': current_rsi - 70}
        elif current_rsi < 30 and prev_rsi >= 30:
            return {'signal': 'bullish', 'strength': 30 - current_rsi}
        else:
            return {'signal': 'none', 'strength': 0}

    def calculate_vwap_slope(self, vwap_values: List[float], period: int = 5) -> float:
        """Calculate VWAP slope to determine trend"""
        if len(vwap_values) < period:
            return 0
        
        recent_vwap = vwap_values[-period:]
        if len(recent_vwap) < 2:
            return 0
        
        # Calculate slope
        x_values = list(range(len(recent_vwap)))
        y_values = recent_vwap
        
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)
        
        if n * sum_x2 - sum_x * sum_x == 0:
            return 0
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        return slope 