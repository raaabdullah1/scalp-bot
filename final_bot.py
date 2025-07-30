#!/usr/bin/env python3
"""
Enhanced ScalpBot - Professional Trading Signal Generator
Integrates modular signal engine with working Telegram delivery
"""

import os
import threading
import asyncio
import requests
from flask import Flask, jsonify, render_template
from dotenv import load_dotenv
from datetime import datetime
import time

# Import core modules
from core.signal_engine import SignalEngine
from core.logger import SignalLogger
from core.notifier import SignalNotifier

# Load environment variables and config
load_dotenv()
try:
    from config import (
        TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_PROFIT_CHAT_ID,
        BINANCE_API_KEY, BINANCE_SECRET_KEY, GMAIL_APP_PASSWORD,
        ACCOUNT_BALANCE, RISK_PERCENTAGE, MAX_DAILY_SIGNALS, COOLDOWN_MINUTES
    )
except ImportError:
    print("Warning: config.py not found, using environment variables only")
    TELEGRAM_BOT_TOKEN = TELEGRAM_CHAT_ID = TELEGRAM_PROFIT_CHAT_ID = None
    BINANCE_API_KEY = BINANCE_SECRET_KEY = GMAIL_APP_PASSWORD = None
    ACCOUNT_BALANCE = RISK_PERCENTAGE = MAX_DAILY_SIGNALS = COOLDOWN_MINUTES = None

app = Flask(__name__)

class EnhancedScalpBot:
    def __init__(self):
        # Telegram settings (KEEPING WORKING DELIVERY)
        self.telegram_token = TELEGRAM_BOT_TOKEN or os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('TELEGRAM_TOKEN')
        self.telegram_chat_id = TELEGRAM_CHAT_ID or os.getenv('TELEGRAM_CHAT_ID')
        self.profit_chat_id = TELEGRAM_PROFIT_CHAT_ID or os.getenv('TELEGRAM_PROFIT_CHAT_ID') or self.telegram_chat_id
        
        # Core components
        self.signal_engine = SignalEngine()
        self.logger = SignalLogger()
        self.notifier = SignalNotifier()
        
        # Bot status
        self.running = False
        self.status = {
            'running': False,
            'start_time': None,
            'signals_sent': 0,
            'last_signal': None,
            'current_scan': None,
            'last_scan_time': None,
            'market_count': 0
        }
        
        # Signal tracking
        self.last_signals = []
        self.market_data = []

    def send_telegram_message(self, message, chat_id=None):
        """Send message to Telegram (KEEPING WORKING DELIVERY)"""
        if not self.telegram_token:
            print("Telegram token not configured")
            return False
        
        target_chat = chat_id or self.telegram_chat_id
        if not target_chat:
            print("Telegram chat ID not configured")
            return False

        # Check for test mode
        if os.getenv('TEST_MODE') == 'true':
            print(f"TEST MODE: Would send Telegram message: {message[:100]}...")
            return True

        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                'chat_id': target_chat,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, data=data, timeout=30)
            return response.status_code == 200
        except requests.exceptions.ConnectTimeout:
            print("Telegram connection timeout (test-safe)")
            return False
        except Exception as e:
            print(f"Telegram error: {e}")
            return False

    def scan_and_generate_signals(self):
        """Scan markets and generate signals"""
        try:
            print("🔍 Starting market scan...")
            self.status['current_scan'] = "Scanning markets..."
            
            # Scan markets first
            markets = self.signal_engine.scan_markets()
            self.status['market_count'] = len(markets)
            
            # Process markets and generate signals
            signals = self.signal_engine.process_markets(markets)
            
            if signals:
                print(f"✅ Generated {len(signals)} signals")
                
                # Send each signal
                for signal in signals:
                    try:
                        # Format signal message
                        message = self.notifier.format_signal_message(signal)
                        
                        # Send to main channel
                        if self.send_telegram_message(message):
                            print(f"✅ Signal sent for {signal['symbol']}")
                            self.status['signals_sent'] += 1
                            self.status['last_signal'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            
                            # Store in recent signals
                            self.last_signals.append(signal)
                            if len(self.last_signals) > 10:
                                self.last_signals.pop(0)
                        else:
                            print(f"❌ Failed to send signal for {signal['symbol']}")
                    
                    except Exception as e:
                        print(f"❌ Error sending signal: {e}")
                        continue
            else:
                print("📊 No signals generated in this scan")
            
            # Update status
            self.status['current_scan'] = "Scan complete"
            self.status['last_scan_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
        except Exception as e:
            print(f"❌ Error in scan_and_generate_signals: {e}")
            self.status['current_scan'] = f"Error: {str(e)}"

    def main_loop(self):
        """Main bot loop"""
        print("🚀 Enhanced ScalpBot starting...")
        self.running = True
        self.status['running'] = True
        self.status['start_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Send startup message
        startup_message = self.notifier.format_test_message()
        self.send_telegram_message(startup_message)
        
        while self.running:
            try:
                # Scan and generate signals
                self.scan_and_generate_signals()
                
                # Wait before next scan (5 minutes)
                print("⏰ Waiting 5 minutes before next scan...")
                for _ in range(300):  # 5 minutes
                    if not self.running:
                        break
                    time.sleep(1)
                
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                time.sleep(60)  # Wait 1 minute on error
        
        print("🛑 Bot stopped.")

    def start(self):
        """Start the bot"""
        if not self.running:
            print("🚀 Starting Enhanced ScalpBot...")
            
            # Start main loop in background thread
            thread = threading.Thread(target=self.main_loop)
            thread.daemon = True
            thread.start()

    def stop(self):
        """Stop the bot"""
        print("🛑 Stopping Enhanced ScalpBot...")
        self.running = False
        self.status['running'] = False

# Create bot instance
bot = EnhancedScalpBot()

# Flask routes
@app.route('/')
def home():
    return render_template('dashboard.html', bot_status=bot.status)

@app.route('/health')
def health():
    return jsonify({
        'status': 'enhanced_scalbot_ready',
        'bot_running': bot.status['running'],
        'version': '2.0.0'
    })

@app.route('/api/status')
def api_status():
    return jsonify(bot.status)

@app.route('/api/start')
def api_start():
    if not bot.running:
        bot.start()
        return jsonify({'status': 'Bot starting', 'running': True})
    return jsonify({'status': 'Bot already running', 'running': True})

@app.route('/api/stop')
def api_stop():
    if bot.running:
        bot.stop()
        return jsonify({'status': 'Bot stopping', 'running': False})
    return jsonify({'status': 'Bot already stopped', 'running': False})

@app.route('/api/test-signal')
def test_signal():
    """Send a test signal"""
    try:
        test_message = bot.notifier.format_test_message()
        success = bot.send_telegram_message(test_message)
        
        return jsonify({
            'success': success,
            'message': 'Test signal sent - Enhanced ScalpBot Ready' if success else 'Failed to send test signal'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

@app.route('/api/signals')
def api_signals():
    """Get recent signals"""
    try:
        return jsonify({
            'signals': bot.last_signals,
            'count': len(bot.last_signals)
        })
    except Exception as e:
        return jsonify({
            'signals': [],
            'count': 0,
            'error': str(e)
        })

@app.route('/api/statistics')
def api_statistics():
    """Get signal statistics and portfolio data"""
    try:
        stats = bot.logger.get_signal_statistics()
        
        # Add portfolio monitoring data
        portfolio_summary = bot.signal_engine.risk_manager.get_portfolio_summary()
        stats['portfolio'] = portfolio_summary
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({
            'error': str(e),
            'total_signals': 0,
            'today_signals': 0,
            'avg_confidence': 0,
            'top_symbols': [],
            'portfolio': {}
        })

@app.route('/api/scan-now')
def api_scan_now():
    """Trigger immediate market scan"""
    try:
        if bot.running:
            # Start scan in background
            thread = threading.Thread(target=bot.scan_and_generate_signals)
            thread.daemon = True
            thread.start()
            
            return jsonify({
                'success': True,
                'message': 'Market scan initiated'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Bot not running'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

@app.route('/api/portfolio')
def api_portfolio():
    """Get portfolio monitoring data"""
    try:
        portfolio_data = bot.signal_engine.risk_manager.get_portfolio_summary()
        active_trades = bot.signal_engine.risk_manager.active_trades
        
        return jsonify({
            'portfolio': portfolio_data,
            'active_trades': active_trades,
            'success': True
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'portfolio': {},
            'active_trades': {}
        })

@app.route('/api/market-regime')
def api_market_regime():
    """Get market regime analysis"""
    try:
        # Get recent market data for analysis
        markets = bot.signal_engine.scanner.get_top_markets(limit=10)
        regime_summary = bot.signal_engine.market_regime_detector.get_regime_summary(markets)
        
        return jsonify({
            'regime_summary': regime_summary,
            'success': True
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'regime_summary': {}
        })

@app.route('/api/sentiment')
def api_sentiment():
    """Get market sentiment analysis"""
    try:
        # Get top symbols for sentiment analysis
        symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT']
        sentiment_summary = bot.signal_engine.sentiment_analyzer.get_market_sentiment_summary(symbols)
        
        return jsonify({
            'sentiment_summary': sentiment_summary,
            'success': True
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'sentiment_summary': {}
        })

if __name__ == '__main__':
    # Start Flask server
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Enhanced ScalpBot v2.0.0 starting...")
    print(f"📡 Flask server starting on port {port}")
    print(f"🔧 Modular architecture with signal engine")
    print(f"📊 Multi-strategy system (Trap, SMC, Scalping)")
    print(f"✅ Telegram delivery system ready")
    
    app.run(host='0.0.0.0', port=port, debug=False) 