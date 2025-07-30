#!/usr/bin/env python3
"""
Enhanced ScalpBot - Professional Trading Signal Generator
Integrates modular signal engine with working Telegram delivery
"""

import os
import threading
import requests
from flask import Flask, jsonify, render_template
from dotenv import load_dotenv
from datetime import datetime
import time

# --- EARLY LOGGING ---
print('[BOOT] Loading environment...')

# Load environment variables and config
load_dotenv()
try:
    from config import (
        TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_PROFIT_CHAT_ID,
        BINANCE_API_KEY, BINANCE_SECRET_KEY, GMAIL_APP_PASSWORD,
        ACCOUNT_BALANCE, RISK_PERCENTAGE, MAX_DAILY_SIGNALS, COOLDOWN_MINUTES
    )
    print('[BOOT] Loaded config.py')
except ImportError:
    print('[BOOT] config.py not found, using environment variables only')
    TELEGRAM_BOT_TOKEN = TELEGRAM_CHAT_ID = TELEGRAM_PROFIT_CHAT_ID = None
    BINANCE_API_KEY = BINANCE_SECRET_KEY = GMAIL_APP_PASSWORD = None
    ACCOUNT_BALANCE = RISK_PERCENTAGE = MAX_DAILY_SIGNALS = COOLDOWN_MINUTES = None

# --- CATCH IMPORT ERRORS FOR CORE MODULES ---
try:
    from core.signal_engine import SignalEngine
    print('[BOOT] Imported core.signal_engine.SignalEngine')
except Exception as e:
    print(f'[IMPORT ERROR] core.signal_engine: {e}')
    raise
try:
    from core.logger import SignalLogger
    print('[BOOT] Imported core.logger.SignalLogger')
except Exception as e:
    print(f'[IMPORT ERROR] core.logger: {e}')
    raise
try:
    from core.notifier import SignalNotifier
    print('[BOOT] Imported core.notifier.SignalNotifier')
except Exception as e:
    print(f'[IMPORT ERROR] core.notifier: {e}')
    raise

app = Flask(__name__)

# --- GLOBAL BOT STATE ---
bot = None
bot_init_error = None
bot_init_time = None

# --- BOT CLASS (UNCHANGED LOGIC) ---
class EnhancedScalpBot:
    def __init__(self):
        print('[INIT] Starting EnhancedScalpBot.__init__')
        # Telegram settings
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
        if not self.telegram_token:
            print("Telegram token not configured")
            return False
        target_chat = chat_id or self.telegram_chat_id
        if not target_chat:
            print("Telegram chat ID not configured")
            return False
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
        try:
            print("🔍 Starting market scan...")
            self.status['current_scan'] = "Scanning markets..."
            markets = self.signal_engine.scan_markets()
            self.status['market_count'] = len(markets)
            signals = self.signal_engine.process_markets(markets)
            if signals:
                print(f"✅ Generated {len(signals)} signals")
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

# Global bot instance (initialized later)
bot = None

# Flask routes
@app.route('/')
def home():
    if bot is None:
        return render_template('dashboard.html', bot_status={'running': False, 'status': 'Initializing...'})
    return render_template('dashboard.html', bot_status=bot.status)

@app.route('/health')
def health():
    # Simple health check that responds immediately
    return jsonify({
        'status': 'ok',
        'service': 'scalpbot',
        'version': '2.0.0'
    })

@app.route('/status')
def get_status():
    if bot is None:
        return jsonify({'error': 'Bot not initialized yet'}), 503
    return jsonify(bot.status)

@app.route('/start', methods=['POST'])
def start_bot():
    if bot is None:
        return jsonify({'error': 'Bot not initialized yet'}), 503
    if not bot.running:
        bot.start()
        return jsonify({'status': 'started'})
    return jsonify({'status': 'already_running'}), 200

@app.route('/stop', methods=['POST'])
def stop_bot():
    if bot is None:
        return jsonify({'error': 'Bot not initialized yet'}), 503
    if bot.running:
        bot.stop()
        return jsonify({'status': 'stopped'})
    return jsonify({'status': 'not_running'}), 200

@app.route('/test_telegram', methods=['POST'])
def test_telegram():
    if bot is None:
        return jsonify({'error': 'Bot not initialized yet'}), 503
    try:
        test_message = bot.notifier.format_test_message()
        success = bot.send_telegram_message(test_message)
        return jsonify({
            'success': success,
            'message': 'Test message sent' if success else 'Failed to send test message'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/signals')
def get_signals():
    if bot is None:
        return jsonify({'error': 'Bot not initialized yet'}), 503
    return jsonify({
        'signals': bot.last_signals,
        'count': len(bot.last_signals)
    })

@app.route('/statistics')
def get_statistics():
    if bot is None:
        return jsonify({'error': 'Bot not initialized yet'}), 503
    stats = bot.logger.get_signal_statistics()
    return jsonify(stats)

@app.route('/portfolio')
def get_portfolio():
    if bot is None:
        return jsonify({'error': 'Bot not initialized yet'}), 503
    portfolio_summary = bot.signal_engine.risk_manager.get_portfolio_summary()
    return jsonify(portfolio_summary)

@app.route('/scan', methods=['POST'])
def manual_scan():
    if bot is None:
        return jsonify({'error': 'Bot not initialized yet'}), 503
    if bot.running:
        # Run scan in background thread to avoid blocking
        thread = threading.Thread(target=bot.scan_and_generate_signals)
        thread.daemon = True
        thread.start()
        return jsonify({'status': 'scan_started'})
    else:
        return jsonify({'status': 'bot_not_running'}), 400

@app.route('/api/sentiment')
def api_sentiment():
    """Get market sentiment analysis"""
    if bot is None:
        return jsonify({'error': 'Bot not initialized yet'}), 503
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
    
    # Import here to avoid circular imports
    from core.signal_engine import SignalEngine
    from core.logger import SignalLogger
    from core.notifier import SignalNotifier
    
    # Initialize bot after Flask server starts
    def init_bot():
        global bot
        bot = EnhancedScalpBot()
        print("🤖 Bot initialized and ready!")
    
    # Start bot initialization in background thread
    import threading
    init_thread = threading.Thread(target=init_bot)
    init_thread.daemon = True
    init_thread.start()
    
    # Start Flask server immediately
    app.run(host='0.0.0.0', port=port, debug=False) 