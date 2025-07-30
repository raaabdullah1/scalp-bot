"""
Signal Engine Module
Orchestrates market scanning, signal generation, and validation using multiple strategies
"""

import time
import threading
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import asdict

from .scanner import MarketScanner
from .indicators import TechnicalIndicators
from .sentiment import SentimentAnalyzer
from .liquidation import LiquidationAnalyzer
from .dark_pool import DarkPoolDetector
from .market_regime import MarketRegimeDetector
from .risk import RiskManager
from .logger import SignalLogger
from .notifier import SignalNotifier
# Import strategy modules
from .strategy_trap import TrapTradingStrategy, TrapSignal
from .strategy_smc import SMCStrategy, SMCSignal
from .strategy_scalp import ScalpingStrategy, ScalpSignal

class SignalEngine:
    def __init__(self):
        self.scanner = MarketScanner()
        self.indicators = TechnicalIndicators()
        self.sentiment = SentimentAnalyzer()
        self.liquidation = LiquidationAnalyzer()
        self.dark_pool = DarkPoolDetector()
        self.regime = MarketRegimeDetector()
        self.risk = RiskManager()
        self.logger = SignalLogger()
        self.notifier = SignalNotifier()
        
        # Strategy modules
        self.trap_strategy = TrapTradingStrategy()
        self.smc_strategy = SMCStrategy()
        self.scalp_strategy = ScalpingStrategy()
        
        # Signal generation settings
        self.min_confidence = 4  # Minimum confidence score (out of 5)
        self.max_daily_signals = 30
        self.cooldown_minutes = 15
        
        # Signal tracking
        self.daily_signals = 0
        self.last_signal_time = {}
        self.signal_history = []
    
    @property
    def risk_manager(self):
        return self.risk
    
    @property
    def market_regime_detector(self):
        return self.regime
    
    @property
    def sentiment_analyzer(self):
        return self.sentiment
        
    def scan_markets(self) -> List[Dict[str, Any]]:
        """Scan and filter markets"""
        try:
            print("🔍 Scanning markets...")
            markets = self.scanner.scan_and_filter_markets()
            
            if not markets:
                print("⚠ No markets found")
                return []
            
            # Select top markets for trading
            top_markets = sorted(markets, key=lambda x: x.get('technical_score', 0), reverse=True)[:6]
            
            print(f"✅ Found {len(top_markets)} top markets")
            for i, market in enumerate(top_markets, 1):
                symbol = market['symbol']
                score = market.get('technical_score', 0)
                print(f"{i}. {symbol} - Score: {score:.2f}")
            
            return top_markets
            
        except Exception as e:
            print(f"❌ Error scanning markets: {e}")
            return []
    
    def prepare_market_data(self, symbol: str, market_data: Dict[str, Any]) -> pd.DataFrame:
        """Prepare market data for strategy analysis"""
        try:
            # Normalize symbol for OHLCV fetch (remove :... suffix)
            normalized_symbol = symbol.split(':')[0] if ':' in symbol else symbol
            
            # Get OHLCV data
            ohlcv = self.indicators.get_ohlcv_data(normalized_symbol, '1h', 100)
            if not ohlcv:
                print(f"⚠ No OHLCV data for {symbol}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['symbol'] = symbol  # Add symbol to DataFrame
            
            # Get close prices as list
            close_prices = df['close'].tolist()
            
            # Calculate technical indicators with proper padding
            # EMA indicators
            ema_9_values = self.indicators.calculate_ema(close_prices, 9)
            ema_21_values = self.indicators.calculate_ema(close_prices, 21)
            ema_20_values = self.indicators.calculate_ema(close_prices, 20)
            ema_50_values = self.indicators.calculate_ema(close_prices, 50)
            
            # Pad EMA values to match DataFrame length
            df['ema_9'] = [0] * (len(df) - len(ema_9_values)) + ema_9_values
            df['ema_21'] = [0] * (len(df) - len(ema_21_values)) + ema_21_values
            df['ema_20'] = [0] * (len(df) - len(ema_20_values)) + ema_20_values
            df['ema_50'] = [0] * (len(df) - len(ema_50_values)) + ema_50_values
            
            # MACD
            macd_data = self.indicators.calculate_macd(close_prices)
            if macd_data and macd_data['macd'] and macd_data['signal']:
                # Pad MACD values to match DataFrame length
                df['macd'] = [0] * (len(df) - len(macd_data['macd'])) + macd_data['macd']
                df['macd_signal'] = [0] * (len(df) - len(macd_data['signal'])) + macd_data['signal']
            else:
                df['macd'] = [0] * len(df)
                df['macd_signal'] = [0] * len(df)
            
            # RSI
            rsi_values = self.indicators.calculate_rsi(close_prices)
            # Pad RSI values to match DataFrame length
            df['rsi'] = [0] * (len(df) - len(rsi_values)) + rsi_values
            
            # VWAP
            vwap_values = self.indicators.calculate_vwap(ohlcv)
            # Pad VWAP values to match DataFrame length
            df['vwap'] = [0] * (len(df) - len(vwap_values)) + vwap_values
            
            # ATR
            atr_values = self.indicators.calculate_atr(ohlcv)
            # Pad ATR values to match DataFrame length
            df['atr'] = [0] * (len(df) - len(atr_values)) + atr_values
            
            # ADX
            adx_values = self.indicators.calculate_adx(ohlcv)
            # Pad ADX values to match DataFrame length
            df['adx'] = [0] * (len(df) - len(adx_values)) + adx_values
            
            return df
            
        except Exception as e:
            print(f"❌ Error preparing market data for {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def get_strategy_weights(self, market_regime: Dict[str, Any]) -> Dict[str, float]:
        """Calculate strategy weights based on market regime"""
        try:
            adx_value = market_regime.get('adx_value', 20)
            volatility_rank = market_regime.get('volatility_rank', 50)
            
            if adx_value > 25 and volatility_rank > 80:
                # Strong trending, high volatility market - favor SMC
                return {'SMC': 0.6, 'Trap': 0.3, 'Scalp': 0.1}
            elif adx_value < 20:
                # Weak trending market - favor Scalping
                return {'Scalp': 0.7, 'Trap': 0.3, 'SMC': 0.0}
            else:
                # Moderate market - balanced approach
                return {'SMC': 0.4, 'Trap': 0.3, 'Scalp': 0.3}
                
        except Exception as e:
            print(f"Error calculating strategy weights: {e}")
            return {'SMC': 0.4, 'Trap': 0.3, 'Scalp': 0.3}
    
    def generate_signal_for_strategy(self, strategy_name: str, symbol: str, 
                                   data: pd.DataFrame, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate signal using a specific strategy"""
        try:
            signal = None
            
            if strategy_name == 'Trap':
                # Get liquidation and order flow data
                liquidation_data = self.liquidation.get_liquidation_clusters(symbol)
                order_flow_data = self.dark_pool.get_dark_pool_analysis(symbol)
                signal_obj = self.trap_strategy.generate_signal(symbol, data, liquidation_data, order_flow_data)
                if signal_obj:
                    signal = asdict(signal_obj)
                    
            elif strategy_name == 'SMC':
                signal_obj = self.smc_strategy.generate_signal(symbol, data)
                if signal_obj:
                    signal = asdict(signal_obj)
                    
            elif strategy_name == 'Scalp':
                signal_obj = self.scalp_strategy.generate_signal(symbol, data)
                if signal_obj:
                    signal = asdict(signal_obj)
            
            # Convert signal to standard format if generated
            if signal:
                # Add market data
                signal['current_price'] = market_data['price']
                signal['symbol'] = symbol
                signal['strategy'] = strategy_name
                
                # Validate signal
                if self.validate_signal(signal):
                    return signal
            
            return None
            
        except Exception as e:
            print(f"Error generating {strategy_name} signal for {symbol}: {e}")
            return None
    
    def validate_signal(self, signal: Dict[str, Any]) -> bool:
        """Validate signal parameters"""
        try:
            entry = signal['entry']
            stop_loss = signal['stop_loss']
            tp1, tp2, tp3 = signal['take_profit']
            signal_type = signal['signal_type']
            confidence = signal['confidence']
            
            # Validate confidence
            if confidence < self.min_confidence:
                return False
            
            # Validate TP/SL positioning
            if signal_type == 'LONG':
                if not (entry < tp1 < tp2 < tp3):
                    return False
                if not (stop_loss < entry):
                    return False
            else:  # SHORT
                if not (entry > tp1 > tp2 > tp3):
                    return False
                if not (stop_loss > entry):
                    return False
            
            # Validate risk-reward ratio
            rr_ratio = abs(tp1 - entry) / abs(entry - stop_loss) if stop_loss != entry else 0
            if rr_ratio < 1.5:
                return False
            
            return True
            
        except Exception as e:
            print(f"Error validating signal: {e}")
            return False
    
    def select_best_signal(self, signals: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Select the best signal from multiple candidates"""
        try:
            if not signals:
                return None
            
            # Sort by confidence
            sorted_signals = sorted(signals, key=lambda x: x['confidence'], reverse=True)
            return sorted_signals[0]
            
        except Exception as e:
            print(f"Error selecting best signal: {e}")
            return None
    
    def generate_signal(self, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate trading signal for a market using multi-strategy approach"""
        try:
            symbol = market_data['symbol']
            current_price = market_data['price']
            
            print(f"Testing signal generation for {symbol}...")
            
            # Check cooldown
            last_signal_time = self.last_signal_time.get(symbol)
            if last_signal_time:
                time_since_last = datetime.now() - last_signal_time
                if time_since_last < timedelta(minutes=self.cooldown_minutes):
                    print(f"⚠ Cooldown period for {symbol} not expired")
                    return None
            
            # Check daily limit
            if self.daily_signals >= self.max_daily_signals:
                print(f"⚠ Daily signal limit reached")
                return None
            
            # Prepare market data
            data = self.prepare_market_data(symbol, market_data)
            if data.empty:
                return None
            
            # Get market regime
            regime_data = self.regime.detect_market_regime(data)
            
            # Get strategy weights based on market regime
            strategy_weights = self.get_strategy_weights(regime_data)
            
            # Generate signals from each strategy
            candidate_signals = []
            
            for strategy_name, weight in strategy_weights.items():
                # Only use strategies with significant weight
                if weight > 0.1:
                    signal = self.generate_signal_for_strategy(strategy_name, symbol, data, market_data)
                    if signal:
                        # Apply weight to confidence
                        weighted_confidence = int(signal['confidence'] * weight)
                        signal['weighted_confidence'] = weighted_confidence
                        candidate_signals.append(signal)
            
            # Select best signal
            best_signal = self.select_best_signal(candidate_signals)
            
            if best_signal:
                # Add additional metadata
                best_signal['market_regime'] = regime_data
                best_signal['strategy_weights'] = strategy_weights
                best_signal['timestamp'] = datetime.now().isoformat()
                
                # Update tracking
                self.last_signal_time[symbol] = datetime.now()
                self.daily_signals += 1
                self.signal_history.append(best_signal)
                
                # Log signal
                self.logger.log_signal(best_signal)
                
                print(f"✅ Signal generated for {symbol}: {best_signal['signal_type']} @ {best_signal['entry']:.2f}")
                return best_signal
            
            return None
            
        except Exception as e:
            print(f"❌ Error generating signal for {symbol}: {e}")
            return None
    
    def process_markets(self, markets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process markets and generate signals"""
        signals = []
        
        for market in markets:
            try:
                signal = self.generate_signal(market)
                if signal:
                    signals.append(signal)
                    
                    # Send signal via Telegram
                    print(f"[STUB] Would send signal: {signal}")
                    
                    # Rate limiting
                    time.sleep(1)
                    
            except Exception as e:
                print(f"❌ Error processing {market['symbol']}: {e}")
                continue
        
        return signals
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get signal generation statistics"""
        try:
            today = datetime.now().date()
            today_signals = [s for s in self.signal_history if datetime.fromisoformat(s['timestamp']).date() == today]
            
            return {
                'total_signals_today': len(today_signals),
                'max_daily_signals': self.max_daily_signals,
                'signals_remaining': max(0, self.max_daily_signals - len(today_signals)),
                'cooldown_minutes': self.cooldown_minutes,
                'min_confidence': self.min_confidence,
                'last_signals': self.signal_history[-5:] if self.signal_history else []
            }
        except Exception as e:
            print(f"❌ Error getting statistics: {e}")
            return {}
    
    def get_signal_statistics(self) -> Dict[str, Any]:
        """Get signal statistics (alias for get_statistics for test compatibility)"""
        return self.get_statistics()
    
    def get_market_summary(self, markets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get summary of scanned markets"""
        try:
            summary = []
            for market in markets:
                summary.append({
                    'symbol': market['symbol'],
                    'price': market['price'],
                    'volume_24h': market.get('volume_24h', 0),
                    'technical_score': market.get('technical_score', 0),
                    'liquidation_density': market.get('liquidation_density', 0),
                    'funding_rate': market.get('funding_rate', 0)
                })
            return summary
        except Exception as e:
            print(f"❌ Error getting market summary: {e}")
            return []
    
    def reset_daily_counters(self):
        """Reset daily signal counters"""
        self.daily_signals = 0
        self.last_signal_time = {} 