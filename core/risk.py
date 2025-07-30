"""
Risk Management Module
ATR-based SL/TP, position sizing, portfolio monitoring, correlation analysis
"""

import math
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import os

class RiskManager:
    def __init__(self):
        # Risk parameters
        self.account_balance = float(os.getenv('ACCOUNT_BALANCE', 10000))
        self.risk_percentage = float(os.getenv('RISK_PERCENTAGE', 2.0)) / 100
        self.max_leverage = 10  # Maximum leverage allowed
        self.max_portfolio_risk = 0.15  # 15% max portfolio risk
        self.max_correlation = 0.7  # Max correlation between positions
        self.max_beta = 1.2  # Max portfolio beta
        
        # Active trades tracking
        self.active_trades = {}
        self.portfolio_exposure = {}
        self.correlation_matrix = {}
        
        # Risk limits
        self.max_daily_loss = self.account_balance * 0.05  # 5% daily loss limit
        self.max_position_size = self.account_balance * 0.1  # 10% max position
        
    def calculate_atr_based_sl_tp(self, entry_price: float, atr: float, signal_type: str, 
                                 volatility_multiplier: float = 1.0) -> Dict[str, float]:
        """Calculate ATR-based stop loss and take profit levels"""
        try:
            # Base ATR multiplier
            base_atr = atr * volatility_multiplier
            
            # Stop loss: 1.5x ATR
            sl_distance = base_atr * 1.5
            
            # Take profit levels: 0.5x, 1x, 1.5x ATR
            tp1_distance = base_atr * 0.5
            tp2_distance = base_atr * 1.0
            tp3_distance = base_atr * 1.5
            
            if signal_type == 'LONG':
                stop_loss = entry_price - sl_distance
                tp1 = entry_price + tp1_distance
                tp2 = entry_price + tp2_distance
                tp3 = entry_price + tp3_distance
            else:  # SHORT
                stop_loss = entry_price + sl_distance
                tp1 = entry_price - tp1_distance
                tp2 = entry_price - tp2_distance
                tp3 = entry_price - tp3_distance
            
            return {
                'stop_loss': round(stop_loss, 6),
                'tp1': round(tp1, 6),
                'tp2': round(tp2, 6),
                'tp3': round(tp3, 6),
                'atr_distance': base_atr
            }
        except Exception as e:
            print(f"Error calculating ATR-based SL/TP: {e}")
            return {}
    
    def calculate_position_size(self, entry_price: float, stop_loss: float, 
                               symbol: str, volatility_factor: float = 1.0) -> Dict[str, Any]:
        """Calculate optimal position size based on risk management rules"""
        try:
            # Risk amount per trade
            risk_amount = self.account_balance * self.risk_percentage
            
            # Price difference for risk calculation
            price_diff = abs(entry_price - stop_loss)
            if price_diff == 0:
                return {'position_size': 0, 'risk_amount': 0, 'leverage': 1}
            
            # Base position size
            base_position_size = risk_amount / price_diff
            
            # Apply volatility adjustment
            adjusted_position_size = base_position_size / volatility_factor
            
            # Check position size limits
            max_position_value = self.account_balance * self.max_position_size
            position_value = adjusted_position_size * entry_price
            
            if position_value > max_position_value:
                adjusted_position_size = max_position_value / entry_price
            
            # Calculate leverage (using max_leverage attribute)
            leverage = min(self.max_leverage, self.account_balance / (adjusted_position_size * entry_price * 0.1))
            
            return {
                'position_size': round(adjusted_position_size, 6),
                'risk_amount': round(risk_amount, 2),
                'leverage': round(leverage, 2),
                'position_value': round(position_value, 2)
            }
        except Exception as e:
            print(f"Error calculating position size: {e}")
            return {'position_size': 0, 'risk_amount': 0, 'leverage': 1}
    
    def validate_risk_reward(self, entry: float, stop_loss: float, tp1: float, 
                           tp2: float, tp3: float, signal_type: str) -> bool:
        """Validate risk-reward ratios and target positioning"""
        try:
            # Calculate distances
            sl_distance = abs(entry - stop_loss)
            tp1_distance = abs(entry - tp1)
            tp2_distance = abs(entry - tp2)
            tp3_distance = abs(entry - tp3)
            
            # Calculate RR ratios
            rr1 = tp1_distance / sl_distance if sl_distance > 0 else 0
            rr2 = tp2_distance / sl_distance if sl_distance > 0 else 0
            rr3 = tp3_distance / sl_distance if sl_distance > 0 else 0
            
            # Validate target positioning
            if signal_type == 'LONG':
                valid_targets = (entry < tp1 < tp2 < tp3) and (stop_loss < entry)
            else:  # SHORT
                valid_targets = (entry > tp1 > tp2 > tp3) and (stop_loss > entry)
            
            # Check minimum RR requirement
            min_rr = 1.5
            meets_rr_requirement = rr1 >= min_rr
            
            return valid_targets and meets_rr_requirement
        except Exception as e:
            print(f"Error validating risk-reward: {e}")
            return False
    
    def add_active_trade(self, trade_data: Dict[str, Any]) -> bool:
        """Add a new active trade to portfolio monitoring"""
        try:
            symbol = trade_data.get('symbol', '')
            side = trade_data.get('side', '')
            amount = trade_data.get('amount', 0)
            entry_price = trade_data.get('entry_price', 0)
            trade_id = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            self.active_trades[trade_id] = {
                'symbol': symbol,
                'signal_type': trade_data.get('signal_type', ''),
                'entry_price': trade_data.get('entry', 0),
                'stop_loss': trade_data.get('stop_loss', 0),
                'tp1': trade_data.get('tp1', 0),
                'tp2': trade_data.get('tp2', 0),
                'tp3': trade_data.get('tp3', 0),
                'position_size': trade_data.get('position_size', 0),
                'leverage': trade_data.get('leverage', 1),
                'entry_time': datetime.now().isoformat(),
                'status': 'ACTIVE',
                'unrealized_pnl': 0.0,
                'current_price': trade_data.get('entry', 0)
            }
            
            # Update portfolio exposure
            self.update_portfolio_exposure()
            
            return True
        except Exception as e:
            print(f"Error adding active trade: {e}")
            return False
    
    def update_portfolio_exposure(self):
        """Stub implementation to fix attribute error"""
        pass
    
    def update_trade_status(self, symbol: str, current_price: float, hit_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Update trade status and calculate unrealized PnL"""
        try:
            updates = []
            
            for trade_id, trade in self.active_trades.items():
                if trade['symbol'] == symbol:
                    # Update current price
                    trade['current_price'] = current_price
                    
                    # Calculate unrealized PnL
                    entry_price = trade['entry_price']
                    position_size = trade['position_size']
                    
                    if trade['signal_type'] == 'LONG':
                        pnl_percent = ((current_price - entry_price) / entry_price) * 100
                    else:  # SHORT
                        pnl_percent = ((entry_price - current_price) / entry_price) * 100
                    
                    trade['unrealized_pnl'] = round(pnl_percent, 2)
                    
                    # Check for TP/SL hits
                    if hit_type:
                        if hit_type == 'TP1' and self.check_tp_hit(trade, current_price, 'tp1'):
                            trade['status'] = 'TP1_HIT'
                        elif hit_type == 'TP2' and self.check_tp_hit(trade, current_price, 'tp2'):
                            trade['status'] = 'TP2_HIT'
                        elif hit_type == 'TP3' and self.check_tp_hit(trade, current_price, 'tp3'):
                            trade['status'] = 'TP3_HIT'
                        elif hit_type == 'SL' and self.check_sl_hit(trade, current_price):
                            trade['status'] = 'SL_HIT'
                    
                    updates.append({
                        'trade_id': trade_id,
                        'symbol': symbol,
                        'status': trade['status'],
                        'unrealized_pnl': trade['unrealized_pnl'],
                        'hit_type': hit_type
                    })
            
            return updates
        except Exception as e:
            print(f"Error updating trade status: {e}")
            return []
    
    def check_tp_hit(self, trade: Dict[str, Any], current_price: float, tp_level: str) -> bool:
        """Check if take profit level was hit"""
        try:
            tp_price = trade.get(tp_level, 0)
            signal_type = trade.get('signal_type')
            
            if signal_type == 'LONG':
                return current_price >= tp_price
            else:  # SHORT
                return current_price <= tp_price
        except Exception as e:
            print(f"Error checking TP hit: {e}")
            return False
    
    def check_sl_hit(self, trade: Dict[str, Any], current_price: float) -> bool:
        """Check if stop loss was hit"""
        try:
            sl_price = trade.get('stop_loss', 0)
            signal_type = trade.get('signal_type')
            
            if signal_type == 'LONG':
                return current_price <= sl_price
            else:  # SHORT
                return current_price >= sl_price
        except Exception as e:
            print(f"Error checking SL hit: {e}")
            return False
    
    def calculate_portfolio_beta(self) -> float:
        """Calculate portfolio beta relative to BTC"""
        try:
            if not self.active_trades:
                return 0.0
            
            total_beta = 0.0
            total_exposure = 0.0
            
            # Simplified beta calculation (in production, use actual market data)
            for trade in self.active_trades.values():
                position_value = trade.get('position_size', 0) * trade.get('current_price', 0)
                # Assume beta of 1.0 for crypto (simplified)
                trade_beta = 1.0
                
                total_beta += position_value * trade_beta
                total_exposure += position_value
            
            return total_beta / total_exposure if total_exposure > 0 else 0.0
        except Exception as e:
            print(f"Error calculating portfolio beta: {e}")
            return 0.0
    
    def calculate_correlation_matrix(self) -> Dict[str, Dict[str, float]]:
        """Calculate correlation matrix between active positions"""
        try:
            symbols = list(set([trade['symbol'] for trade in self.active_trades.values()]))
            correlation_matrix = {}
            
            for i, symbol1 in enumerate(symbols):
                correlation_matrix[symbol1] = {}
                for j, symbol2 in enumerate(symbols):
                    if i == j:
                        correlation_matrix[symbol1][symbol2] = 1.0
                    else:
                        # Simplified correlation (in production, use actual price data)
                        correlation_matrix[symbol1][symbol2] = 0.3  # Assume 0.3 correlation
            
            return correlation_matrix
        except Exception as e:
            print(f"Error calculating correlation matrix: {e}")
            return {}
    
    def check_portfolio_risk_limits(self) -> Dict[str, Any]:
        """Check if portfolio is within risk limits"""
        try:
            total_exposure = sum([
                trade.get('position_size', 0) * trade.get('current_price', 0)
                for trade in self.active_trades.values()
            ])
            
            exposure_ratio = total_exposure / self.account_balance
            portfolio_beta = self.calculate_portfolio_beta()
            
            # Check correlation limits
            high_correlation_pairs = []
            correlation_matrix = self.calculate_correlation_matrix()
            
            for symbol1 in correlation_matrix:
                for symbol2 in correlation_matrix[symbol1]:
                    if symbol1 != symbol2 and correlation_matrix[symbol1][symbol2] > self.max_correlation:
                        high_correlation_pairs.append((symbol1, symbol2))
            
            risk_status = {
                'within_limits': True,
                'exposure_ratio': round(exposure_ratio, 3),
                'portfolio_beta': round(portfolio_beta, 3),
                'high_correlation_pairs': high_correlation_pairs,
                'warnings': []
            }
            
            # Check limits
            if exposure_ratio > self.max_portfolio_risk:
                risk_status['within_limits'] = False
                risk_status['warnings'].append(f"Portfolio exposure {exposure_ratio:.1%} exceeds limit {self.max_portfolio_risk:.1%}")
            
            if portfolio_beta > self.max_beta:
                risk_status['within_limits'] = False
                risk_status['warnings'].append(f"Portfolio beta {portfolio_beta:.2f} exceeds limit {self.max_beta}")
            
            if high_correlation_pairs:
                risk_status['warnings'].append(f"High correlation detected in {len(high_correlation_pairs)} pairs")
            
            return risk_status
        except Exception as e:
            print(f"Error checking portfolio risk limits: {e}")
            return {'within_limits': False, 'warnings': [f"Error: {str(e)}"]}
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive portfolio summary"""
        try:
            active_trades = len(self.active_trades)
            total_exposure = sum([
                trade.get('position_size', 0) * trade.get('current_price', 0)
                for trade in self.active_trades.values()
            ])
            
            total_unrealized_pnl = sum([
                trade.get('unrealized_pnl', 0)
                for trade in self.active_trades.values()
            ])
            
            risk_status = self.check_portfolio_risk_limits()
            
            return {
                'active_trades': active_trades,
                'total_exposure': round(total_exposure, 2),
                'exposure_ratio': round(total_exposure / self.account_balance, 3),
                'total_unrealized_pnl': round(total_unrealized_pnl, 2),
                'portfolio_beta': round(self.calculate_portfolio_beta(), 3),
                'risk_status': risk_status,
                'account_balance': self.account_balance,
                'risk_percentage': self.risk_percentage * 100
            }
        except Exception as e:
            print(f"Error getting portfolio summary: {e}")
            return {} 