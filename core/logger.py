"""
Signal Logging and Confidence Scoring System
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

class SignalLogger:
    def __init__(self, log_file_path: str = "logs/signals_log.json"):
        self.log_file_path = log_file_path
        self.ensure_log_file_exists()
        
    def ensure_log_file_exists(self):
        """Ensure the log file exists with proper structure"""
        if not os.path.exists(self.log_file_path):
            os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)
            with open(self.log_file_path, 'w') as f:
                json.dump([], f)
    
    def log_signal(self, signal_data: Dict[str, Any]) -> bool:
        """Log a signal with all metadata"""
        try:
            # Add timestamp if not present
            if 'timestamp' not in signal_data:
                signal_data['timestamp'] = datetime.now().isoformat()
            
            # Add log_id for tracking
            signal_data['log_id'] = f"signal_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Read existing logs
            with open(self.log_file_path, 'r') as f:
                logs = json.load(f)
            
            # Add new signal
            logs.append(signal_data)
            
            # Keep only last 1000 signals to prevent file bloat
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            # Write back to file
            with open(self.log_file_path, 'w') as f:
                json.dump(logs, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error logging signal: {e}")
            return False
    
    def get_recent_signals(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent signals from log"""
        try:
            with open(self.log_file_path, 'r') as f:
                logs = json.load(f)
            return logs[-limit:] if logs else []
        except Exception as e:
            print(f"Error reading signals: {e}")
            return []
    
    def get_signals_by_symbol(self, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get signals for a specific symbol"""
        try:
            with open(self.log_file_path, 'r') as f:
                logs = json.load(f)
            
            symbol_signals = [s for s in logs if s.get('symbol') == symbol]
            return symbol_signals[-limit:] if symbol_signals else []
        except Exception as e:
            print(f"Error reading signals for {symbol}: {e}")
            return []
    
    def get_last_signal_time(self, symbol: str) -> float:
        """Get timestamp of last signal for a symbol"""
        signals = self.get_signals_by_symbol(symbol, limit=1)
        if signals:
            try:
                timestamp_str = signals[0].get('timestamp', '')
                if timestamp_str:
                    dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    return dt.timestamp()
            except:
                pass
        return 0.0
    
    def get_daily_signal_count(self, date: Optional[str] = None) -> int:
        """Get number of signals sent today"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        if date is None:  # This line is redundant but satisfies type checker
            date = ''
        
        try:
            with open(self.log_file_path, 'r') as f:
                logs = [json.loads(line) for line in f if line.strip()]
            return len([log for log in logs if log.get('timestamp', '').startswith(date)])
        except FileNotFoundError:
            return 0
        except Exception as e:
            print(f"Error reading signal count: {e}")
            return 0
    
    def calculate_confidence_score(self, validation_results: Dict[str, bool]) -> int:
        """Calculate confidence score based on validation results"""
        passed_checks = sum(validation_results.values())
        total_checks = len(validation_results)
        
        if total_checks == 0:
            return 0
        
        # Convert to 5-point scale
        confidence = int((passed_checks / total_checks) * 5)
        return min(confidence, 5)  # Cap at 5
    
    def validate_signal_targets(self, signal_data: Dict[str, Any]) -> bool:
        """Validate signal targets (entry, SL, TP levels)"""
        try:
            entry = float(signal_data.get('entry', 0))
            stop_loss = float(signal_data.get('stop_loss', 0))
            tp1 = float(signal_data.get('tp1', 0))
            tp2 = float(signal_data.get('tp2', 0))
            tp3 = float(signal_data.get('tp3', 0))
            signal_type = signal_data.get('signal_type', '').upper()
            
            if entry <= 0 or stop_loss <= 0 or tp1 <= 0 or tp2 <= 0 or tp3 <= 0:
                return False
            
            if signal_type == 'LONG':
                # For LONG: Entry < TP1 < TP2 < TP3, SL < Entry
                if not (stop_loss < entry < tp1 < tp2 < tp3):
                    return False
            elif signal_type == 'SHORT':
                # For SHORT: Entry > TP1 > TP2 > TP3, SL > Entry
                if not (stop_loss > entry > tp1 > tp2 > tp3):
                    return False
            else:
                return False
            
            # Validate risk-reward ratio
            risk = abs(entry - stop_loss)
            reward = abs(tp1 - entry)
            if risk > 0:
                rr_ratio = reward / risk
                if rr_ratio < 1.5:
                    return False
            
            return True
        except Exception as e:
            print(f"Error validating signal targets: {e}")
            return False
    
    def check_signal_conflicts(self, symbol: str, signal_type: str, cooldown_seconds: int = 1800) -> bool:
        """Check if signal conflicts with recent signals for same symbol"""
        try:
            current_time = datetime.now().timestamp()
            last_signal_time = self.get_last_signal_time(symbol)
            
            # Check cooldown
            if current_time - last_signal_time < cooldown_seconds:
                return True  # Conflict detected
            
            # Check for conflicting signal types
            recent_signals = self.get_signals_by_symbol(symbol, limit=5)
            for signal in recent_signals:
                if signal.get('signal_type', '').upper() != signal_type.upper():
                    # Different signal type - check if within cooldown
                    try:
                        signal_time = datetime.fromisoformat(signal.get('timestamp', '')).timestamp()
                        if current_time - signal_time < cooldown_seconds:
                            return True  # Conflict detected
                    except:
                        pass
            
            return False  # No conflicts
        except Exception as e:
            print(f"Error checking signal conflicts: {e}")
            return True  # Assume conflict on error
    
    def get_signal_statistics(self) -> Dict[str, Any]:
        """Get signal statistics for dashboard"""
        try:
            with open(self.log_file_path, 'r') as f:
                logs = json.load(f)
            
            if not logs:
                return {
                    'total_signals': 0,
                    'today_signals': 0,
                    'success_rate': 0,
                    'avg_confidence': 0,
                    'top_symbols': []
                }
            
            total_signals = len(logs)
            today_signals = self.get_daily_signal_count()
            
            # Calculate average confidence
            confidences = [s.get('confidence', 0) for s in logs if s.get('confidence')]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Get top symbols
            symbol_counts = {}
            for signal in logs:
                symbol = signal.get('symbol', '')
                if symbol:
                    symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
            
            top_symbols = sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                'total_signals': total_signals,
                'today_signals': today_signals,
                'avg_confidence': round(avg_confidence, 2),
                'top_symbols': top_symbols
            }
        except Exception as e:
            print(f"Error getting signal statistics: {e}")
            return {
                'total_signals': 0,
                'today_signals': 0,
                'avg_confidence': 0,
                'top_symbols': []
            } 