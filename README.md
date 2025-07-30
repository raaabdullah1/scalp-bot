# 🤖 ScalpBot - Advanced Trading Signal Generator

> **Enhanced with Altcoin Support, News Monitoring, and Advanced Technical Analysis**

A sophisticated cryptocurrency trading signal generator that monitors multiple altcoins and provides real-time trading signals via Telegram, email, and local logging. Perfect for the upcoming altcoin season!

## 🚀 Key Features

### 📊 **Advanced Technical Analysis**
- **Multi-Indicator Confirmation**: EMA crossovers filtered by RSI, MACD, Bollinger Bands, and Stochastic
- **Volume Analysis**: Smart volume filtering to ensure signal quality
- **Signal Strength Scoring**: 3-tier confirmation system (2/3 indicators required)
- **ATR-Based Volatility Filtering**: Only signals with sufficient market movement

### 🎯 **Altcoin Season Ready**
- **20+ Altcoin Support**: BTC, ETH, SOL, ADA, DOT, AVAX, LINK, UNI, AAVE, SUSHI, AXS, SAND, MANA, ENJ, FET, GRT, DOGE, SHIB, PEPE, FLOKI
- **Altcoin Signal Limits**: Prevents signal spam with hourly limits
- **Trending Altcoin Scanner**: Identifies high-momentum altcoins
- **Category-Based Monitoring**: Layer 1s, DeFi, Gaming/Metaverse, AI/Web3, Meme coins

### 📰 **News Sentiment Analysis**
- **Real-time News Monitoring**: Tracks crypto news sources
- **Sentiment Analysis**: Uses TextBlob for market sentiment scoring
- **Signal Filtering**: Blocks signals during negative market sentiment
- **Keyword Detection**: Identifies positive/negative/altcoin-specific news

### 🔄 **Multiple Notification Channels**
- **Telegram Integration**: Primary notification method
- **Email Fallback**: Automatic email notifications when Telegram fails
- **Local Logging**: Signals saved to `signals.log` and `latest_signal.txt`
- **Proxy Support**: Works with VPNs, Tor, and MTProto proxies

### 📈 **Performance Monitoring**
- **Signal Tracking**: Monitors signal success rates
- **Performance Analytics**: Detailed P&L analysis
- **Backtesting**: Historical performance validation
- **Real-time Monitoring**: Live signal display

## 🛠️ Installation

1. **Clone and Setup**:
```bash
git clone <your-repo>
cd scalp-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Configure Environment**:
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Required Environment Variables**:
```env
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_secret
TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
EMAIL_ADDRESS=your_email@example.com
HTTP_PROXY=socks5://127.0.0.1:9050  # Optional: Tor proxy
```

## 🚀 Quick Start

### Start the Bot
```bash
# Simple start
python scalbot.py

# Or use the startup script
chmod +x start.sh
./start.sh
```

### Monitor Signals
```bash
# Real-time signal monitor
python signal_monitor.py

# Check latest signal
python check_signals.py

# Performance analysis
python performance_monitor.py
```

### Altcoin Scanner
```bash
# Scan for trending altcoins
python altcoin_scanner.py
```

## 📊 Signal Quality Features

### Multi-Confirmation System
Each signal requires at least **2 out of 3** confirmations:
1. **MACD**: Trend direction and momentum
2. **Bollinger Bands**: Price position relative to volatility
3. **Stochastic**: Overbought/oversold conditions

### Volume Filtering
- Minimum volume multiplier: 1.5x average
- Prevents signals on low-liquidity moves
- Ensures tradeable market conditions

### Signal Spam Prevention
- 5-minute minimum interval between signals
- Hourly limits for altcoin signals
- News sentiment filtering

## 🎯 Altcoin Categories

### Layer 1 Blockchains
- **SOL** (Solana): High-performance blockchain
- **ADA** (Cardano): Proof-of-stake platform
- **DOT** (Polkadot): Multi-chain network
- **AVAX** (Avalanche): Smart contract platform

### DeFi Tokens
- **UNI** (Uniswap): DEX protocol
- **AAVE** (Aave): Lending platform
- **SUSHI** (SushiSwap): DeFi aggregator

### Gaming/Metaverse
- **AXS** (Axie Infinity): Gaming platform
- **SAND** (Sandbox): Virtual world
- **MANA** (Decentraland): Metaverse platform
- **ENJ** (Enjin): Gaming ecosystem

### AI/Web3
- **FET** (Fetch.ai): AI platform
- **GRT** (Graph): Data indexing

### Meme Coins
- **DOGE** (Dogecoin): Original meme coin
- **SHIB** (Shiba Inu): Community-driven
- **PEPE** (Pepe): Viral meme coin
- **FLOKI** (Floki): Viking-themed

## 📰 News Monitoring

### Supported Sources
- Cointelegraph
- CoinDesk
- Bitcoin.com
- Decrypt
- The Block
- CryptoNews

### Sentiment Analysis
- **Positive Keywords**: bullish, surge, rally, adoption, partnership
- **Negative Keywords**: bearish, crash, dump, regulation, hack
- **Altcoin Keywords**: alt season, defi, nft, gaming, metaverse

### Signal Impact
- Blocks LONG signals during negative sentiment
- Blocks SHORT signals during positive sentiment
- Altcoin-specific sentiment filtering

## 🔧 Configuration

### Strategy Parameters
```yaml
strategy:
  ema_fast: 9
  ema_slow: 21
  rsi_len: 14
  macd_fast: 12
  macd_slow: 26
  bb_length: 20
  stoch_k: 14
  volume_filter: true
  min_signal_interval: 300
```

### Risk Management
```yaml
risk:
  leverage: 10
  stop_loss_pct: 0.02
  take_profits:
    - pct: 0.015  # 1.5%
    - pct: 0.03   # 3%
    - pct: 0.05   # 5%
```

## 📈 Performance Monitoring

### Signal Analytics
- Success rate tracking
- Average signal strength
- P&L per symbol
- Daily/weekly breakdowns

### Backtesting Results
- Historical performance validation
- Multi-timeframe analysis (1m & 4h)
- Signal quality assessment

## 🔒 Security & Privacy

- **Signals Only Mode**: No actual trading execution
- **Proxy Support**: Works with VPNs and Tor
- **Environment Variables**: Secure credential storage
- **Local Logging**: Private signal storage

## 🆘 Troubleshooting

### Telegram Issues
```bash
# Test Telegram connection
python test_tor_telegram.py

# Check status
python status_check.py
```

### Proxy Setup
```bash
# For Tor users
brew services start tor
export HTTP_PROXY=socks5://127.0.0.1:9050
export HTTPS_PROXY=socks5://127.0.0.1:9050
```

### Signal Monitoring
```bash
# Check if bot is running
ps aux | grep scalbot

# View latest signals
cat latest_signal.txt
tail -f signals.log
```

## 📝 File Structure

```
scalp-bot/
├── scalbot.py              # Main bot with all features
├── config.yaml             # Configuration file
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
├── news_monitor.py         # News sentiment analysis
├── altcoin_scanner.py      # Trending altcoin detection
├── performance_monitor.py  # Signal performance tracking
├── backtest.py            # Historical testing
├── signal_monitor.py      # Real-time monitoring
├── start.sh               # Startup script
├── signals.log            # Signal history
├── latest_signal.txt      # Most recent signal
└── README.md              # This file
```

## 🎯 Altcoin Season Strategy

### Why This Bot is Perfect for Alt Season
1. **Multi-Category Coverage**: Monitors all major altcoin categories
2. **News Integration**: Captures alt season sentiment
3. **Volume Filtering**: Ensures liquidity during pumps
4. **Signal Quality**: Multi-confirmation reduces false signals
5. **Real-time Monitoring**: Never miss a pump

### Expected Performance
- **Signal Frequency**: 5-15 signals per day across all symbols
- **Signal Quality**: 2.0-3.0/3.0 average strength
- **Altcoin Focus**: 70% altcoin signals during alt season
- **News Integration**: 20% signal filtering based on sentiment

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## ⚠️ Disclaimer

This bot generates trading signals only. It does not execute trades automatically. Always do your own research and trade responsibly. Past performance does not guarantee future results.

---

**Inspired by**: [Fluronix/buy-signal-crypto-bot](https://github.com/Fluronix/buy-signal-crypto-bot)

**Ready for Altcoin Season 2024! 🚀** 