"""
Signal Notifier Module
Formats and sends signals to Telegram channels
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

class SignalNotifier:
    def __init__(self):
        pass
    
    def format_signal_message(self, signal_data: Dict[str, Any], signal_id: Optional[str] = None) -> str:
        """Format professional signal message for main channel with advanced features"""
        try:
            # Extract signal data
            signal_id = signal_id or signal_data.get('signal_id', 'N/A')
            symbol = signal_data.get('symbol', 'N/A')
            signal_type = signal_data.get('signal_type', 'N/A')
            entry = signal_data.get('entry', 0)
            stop_loss = signal_data.get('stop_loss', 0)
            tp1 = signal_data.get('tp1', 0)
            tp2 = signal_data.get('tp2', 0)
            tp3 = signal_data.get('tp3', 0)
            risk_reward = signal_data.get('risk_reward', 0)
            confidence = signal_data.get('confidence', 0)
            strategy = signal_data.get('strategy', 'N/A')
            passed_layers = signal_data.get('passed_layers', [])
            atr = signal_data.get('atr', 0)
            volume_ratio = signal_data.get('volume_ratio', 0)
            timestamp = signal_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            # Advanced features
            market_regime = signal_data.get('market_regime', 'unknown')
            liquidation_risk = signal_data.get('liquidation_risk', 0)
            sentiment_score = signal_data.get('sentiment_score', 0)
            volatility_score = signal_data.get('volatility_score', 0)
            dark_pool_anomaly = signal_data.get('dark_pool_anomaly', 'low')
            position_size = signal_data.get('position_size', 0)
            leverage = signal_data.get('leverage', 5)
            leverage_reason = signal_data.get('leverage_reason', 'Default')
            
            # Format confidence score
            confidence_int = int(confidence) if isinstance(confidence, (int, float)) else 0
            confidence_dots = '🔵' * confidence_int + '⚪' * (5 - confidence_int)
            
            # Format passed layers
            layer_indicators = []
            layer_map = {
                'EMA_CROSSOVER': 'EMA',
                'MACD_CONFIRMATION': 'MACD',
                'RSI_REVERSAL': 'RSI',
                'VWAP_SLOPE': 'VWAP',
                'VOLUME_SPIKE': 'Volume',
                'TRADINGVIEW_CONSENSUS': 'TV',
                'COINGLASS_DATA': 'CG'
            }
            
            for layer in passed_layers:
                if layer in layer_map:
                    layer_indicators.append(f"{layer_map[layer]} ✅")
            
            layers_text = ' | '.join(layer_indicators) if layer_indicators else 'None'
            
            # Format sentiment
            sentiment_score_float = float(sentiment_score) if isinstance(sentiment_score, (int, float, str)) else 0.0
            sentiment_emoji = '🟢' if sentiment_score_float > 0.3 else '🔴' if sentiment_score_float < -0.3 else '🟡'
            
            # Format market regime
            regime_emoji = {
                'strong_uptrend': '📈',
                'strong_downtrend': '📉',
                'moderate_uptrend': '↗️',
                'moderate_downtrend': '↘️',
                'high_volatility_sideways': '📊',
                'low_volatility_sideways': '➡️',
                'sideways': '➡️'
            }.get(market_regime, '❓')
            
            # Create message
            message = f"""
🚨 <b>PROFESSIONAL SCALP SIGNAL #{signal_id}</b>

📊 <b>Symbol:</b> {symbol}
📈 <b>Signal:</b> {signal_type}
🎯 <b>Strategy:</b> {strategy}
⭐ <b>Confidence:</b> {confidence_dots} ({confidence}/5)
📊 <b>Risk-Reward:</b> {risk_reward:.2f}

💰 <b>Entry:</b> ${entry:.4f}
🛑 <b>Stop Loss:</b> ${stop_loss:.4f}
🎯 <b>Take Profit 1:</b> ${tp1:.4f}
🎯 <b>Take Profit 2:</b> ${tp2:.4f}
🎯 <b>Take Profit 3:</b> ${tp3:.4f}

📈 <b>Indicators:</b> {layers_text}

📊 <b>Market Data:</b>
• ATR: {atr:.4f}
• Volume Ratio: {volume_ratio:.2f}

🎛️ <b>Advanced Features:</b>
• Market Regime: {regime_emoji} {market_regime.replace('_', ' ').title()}
• Liquidation Risk: {liquidation_risk:.2f}
• Sentiment: {sentiment_emoji} {sentiment_score:.2f}
• Volatility: {volatility_score:.2f}
• Dark Pool: {dark_pool_anomaly.title()}
• Position Size: {position_size:.4f}
• Leverage: {leverage}x ({leverage_reason})

⏰ <b>Time:</b> {timestamp}
            """.strip()
            
            return message
            
        except Exception as e:
            print(f"Error formatting signal message: {e}")
            return f"Error formatting signal: {str(e)}"
    
    def format_profit_update(self, signal_data: Dict[str, Any], hit_type: str, current_price: float, signal_id: Optional[str] = None) -> str:
        """Format profit monitoring update for second channel"""
        try:
            symbol = signal_data.get('symbol', 'N/A')
            signal_type = signal_data.get('signal_type', 'N/A')
            entry = signal_data.get('entry', 0)
            
            if hit_type == 'TP1':
                target = signal_data.get('tp1', 0)
                target_name = 'TP1'
            elif hit_type == 'TP2':
                target = signal_data.get('tp2', 0)
                target_name = 'TP2'
            elif hit_type == 'TP3':
                target = signal_data.get('tp3', 0)
                target_name = 'TP3'
            elif hit_type == 'SL':
                target = signal_data.get('stop_loss', 0)
                target_name = 'Stop Loss'
            else:
                return f"Unknown hit type: {hit_type}"
            
            # Calculate percentage gain/loss
            if signal_type.upper() == 'LONG':
                if hit_type == 'SL':
                    pnl_percent = ((current_price - entry) / entry) * 100
                else:
                    pnl_percent = ((target - entry) / entry) * 100
            else:  # SHORT
                if hit_type == 'SL':
                    pnl_percent = ((entry - current_price) / entry) * 100
                else:
                    pnl_percent = ((entry - target) / entry) * 100
            
            # Format message
            if hit_type == 'SL':
                emoji = "🛑"
                status = "STOP LOSS HIT"
            else:
                emoji = "🎯"
                status = f"{target_name} HIT"
            
            message = f"""
{emoji} <b>{status} – {symbol}</b>

📊 <b>Signal:</b> {signal_type}
💰 <b>Entry:</b> ${entry:.4f} → <b>{target_name}:</b> ${target:.4f}
📈 <b>Unrealized PnL:</b> {pnl_percent:+.2f}%

⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()
            
            return message
            
        except Exception as e:
            print(f"Error formatting profit update: {e}")
            return f"Error formatting profit update: {str(e)}"
    
    def format_market_summary(self, market_data: Dict[str, Any]) -> str:
        """Format market summary for dashboard"""
        try:
            total_markets = market_data.get('total_markets', 0)
            avg_volume = market_data.get('avg_volume', 0)
            avg_funding_rate = market_data.get('avg_funding_rate', 0)
            avg_spread = market_data.get('avg_spread', 0)
            top_symbols = market_data.get('top_symbols', [])
            
            # Format top symbols
            symbols_text = ""
            for i, (symbol, score) in enumerate(top_symbols[:5], 1):
                symbols_text += f"{i}. {symbol} ({score:.1f})\n"
            
            message = f"""
📊 <b>MARKET SCAN SUMMARY</b>

🔍 <b>Scanned Markets:</b> {total_markets}
💰 <b>Avg Volume:</b> ${avg_volume:,.0f}
📈 <b>Avg Funding Rate:</b> {avg_funding_rate:.4f}%
📊 <b>Avg Spread:</b> {avg_spread:.4f}%

🏆 <b>Top Ranked Symbols:</b>
{symbols_text.strip()}

⏰ <b>Last Updated:</b> {datetime.now().strftime('%H:%M:%S')}
            """.strip()
            
            return message
            
        except Exception as e:
            print(f"Error formatting market summary: {e}")
            return f"Error formatting market summary: {str(e)}"
    
    def format_error_message(self, error_type: str, details: str) -> str:
        """Format error messages for notifications"""
        try:
            message = f"""
⚠️ <b>BOT ERROR ALERT</b>

🚨 <b>Error Type:</b> {error_type}
📝 <b>Details:</b> {details}

⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()
            
            return message
            
        except Exception as e:
            print(f"Error formatting error message: {e}")
            return f"Error formatting error message: {str(e)}"
    
    def format_signal_statistics(self, stats: Dict[str, Any]) -> str:
        """Format signal statistics for dashboard"""
        try:
            total_signals = stats.get('total_signals', 0)
            today_signals = stats.get('today_signals', 0)
            avg_confidence = stats.get('avg_confidence', 0)
            top_symbols = stats.get('top_symbols', [])
            
            # Format top symbols
            symbols_text = ""
            for i, (symbol, count) in enumerate(top_symbols[:5], 1):
                symbols_text += f"{i}. {symbol} ({count} signals)\n"
            
            message = f"""
📊 <b>SIGNAL STATISTICS</b>

📈 <b>Total Signals:</b> {total_signals}
📅 <b>Today's Signals:</b> {today_signals}
⭐ <b>Avg Confidence:</b> {avg_confidence:.1f}/5

🏆 <b>Top Signal Symbols:</b>
{symbols_text.strip()}

⏰ <b>Last Updated:</b> {datetime.now().strftime('%H:%M:%S')}
            """.strip()
            
            return message
            
        except Exception as e:
            print(f"Error formatting signal statistics: {e}")
            return f"Error formatting signal statistics: {str(e)}"
    
    def format_test_message(self) -> str:
        """Format test message for verification"""
        try:
            message = f"""
🧪 <b>BOT TEST MESSAGE</b>

✅ <b>Status:</b> All systems operational
📡 <b>Telegram:</b> Connected
🔍 <b>Scanner:</b> Ready
📊 <b>Indicators:</b> Loaded
📈 <b>Strategies:</b> Active

⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()
            
            return message
            
        except Exception as e:
            print(f"Error formatting test message: {e}")
            return f"Error formatting test message: {str(e)}"
    
    def validate_signal_format(self, signal_data: Dict[str, Any]) -> bool:
        """Validate signal data before formatting"""
        try:
            required_fields = [
                'signal_id', 'symbol', 'signal_type', 'entry', 
                'stop_loss', 'tp1', 'tp2', 'tp3', 'confidence'
            ]
            
            for field in required_fields:
                if field not in signal_data:
                    print(f"Missing required field: {field}")
                    return False
            
            # Validate signal type
            signal_type = signal_data['signal_type'].upper()
            if signal_type not in ['LONG', 'SHORT']:
                print(f"Invalid signal type: {signal_type}")
                return False
            
            # Validate confidence score
            confidence = signal_data['confidence']
            if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 5:
                print(f"Invalid confidence score: {confidence}")
                return False
            
            # Validate prices
            prices = [
                signal_data['entry'],
                signal_data['stop_loss'],
                signal_data['tp1'],
                signal_data['tp2'],
                signal_data['tp3']
            ]
            
            for price in prices:
                if not isinstance(price, (int, float)) or price <= 0:
                    print(f"Invalid price: {price}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"Error validating signal format: {e}")
            return False 