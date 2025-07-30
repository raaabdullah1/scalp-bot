# API Keys for local/Cursor testing
# Note: For production, these should be moved to .env file

# Binance API (REPLACE WITH YOUR OWN CREDENTIALS)
BINANCE_API_KEY = "your_binance_api_key_here"
BINANCE_SECRET_KEY = "your_binance_secret_key_here"

# Telegram Configuration (REPLACE WITH YOUR OWN CREDENTIALS)
TELEGRAM_BOT_TOKEN = "your_telegram_bot_token_here"
TELEGRAM_CHAT_ID = "your_telegram_chat_id_here"
TELEGRAM_PROFIT_CHAT_ID = "your_telegram_chat_id_here"  # Same as main for now, can be changed later

# Gmail Configuration (REPLACE WITH YOUR OWN CREDENTIALS)
GMAIL_APP_PASSWORD = "your_gmail_app_password_here"

# Bot Configuration (CAN BE ADJUSTED AS NEEDED)
ACCOUNT_BALANCE = 10000  # Default account balance in USDT
RISK_PERCENTAGE = 2.0    # Risk per trade percentage
MAX_DAILY_SIGNALS = 30   # Maximum signals per day
COOLDOWN_MINUTES = 15    # Cooldown between signals for same symbol

# ============================================================================
# EXTERNAL API KEYS (OPTIONAL - CURRENTLY USING FREE ALTERNATIVES)
# ============================================================================
# 
# The bot currently uses free, no-key data sources for all functionality:
# - TradingView data via tvDatafeed (free)
# - CryptoPanic RSS feed via feedparser (free) 
# - Liquidation analysis via CCXT order book analysis (free)
# - Dark pool detection via CCXT order book anomalies (free)
#
# If you want to use paid APIs for enhanced data, follow these steps:
#
# 1. COINGLASS API (Optional - for enhanced liquidation data)
#    • Go to https://coinglass.com/api
#    • Sign up for an account and create an API key
#    • Replace "your_coinglass_api_key_here" below with your actual key
# COINGLASS_API_KEY = "your_coinglass_api_key_here"
#
# 2. TRADINGVIEW API (Optional - for enhanced technical analysis)
#    • Visit https://www.tradingview.com/rest-api-spec/
#    • Follow "Get API Token" instructions
#    • Replace "your_tradingview_api_key_here" below with your actual token
# TRADINGVIEW_API_KEY = "your_tradingview_api_key_here"
#
# 3. CRYPTOPANIC API (Optional - for enhanced news sentiment)
#    • Go to https://cryptopanic.com/developers/api/
#    • Sign up and create a new API app
#    • Replace "your_cryptopanic_api_key_here" below with your public key
# CRYPTOPANIC_API_KEY = "your_cryptopanic_api_key_here"
#
# Note: The bot works perfectly with free data sources. Paid APIs are optional
# and only provide enhanced features like more detailed liquidation data,
# advanced technical indicators, or more comprehensive news sentiment analysis. 