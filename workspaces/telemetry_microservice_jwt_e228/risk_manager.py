"""Institutional Quantitative Risk Management Engine."""
from typing import Dict, Any

class RiskManager:
    def __init__(self, max_drawdown_pct: float = 5.0, initial_equity: float = 100000.0):
        self.max_drawdown_pct = max_drawdown_pct
        self.initial_equity = initial_equity
        self.peak_equity = initial_equity
        self.is_circuit_breaker_active = False

    def check_portfolio_risk(self, current_equity: float) -> Dict[str, Any]:
        """Calculates current drawdown and triggers circuit breaker if limit exceeded."""
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
        drawdown_pct = ((self.peak_equity - current_equity) / max(1.0, self.peak_equity)) * 100.0
        if drawdown_pct >= self.max_drawdown_pct:
            self.is_circuit_breaker_active = True
        return {
            "current_equity": round(current_equity, 2),
            "drawdown_pct": round(drawdown_pct, 2),
            "circuit_breaker_active": self.is_circuit_breaker_active,
            "trade_allowed": not self.is_circuit_breaker_active
        }

    def calculate_position_size(self, current_equity: float, win_rate: float = 0.55, win_loss_ratio: float = 1.8) -> float:
        """Kelly criterion position sizing (fractional Kelly 0.25 for safety)."""
        if self.is_circuit_breaker_active:
            return 0.0
        q = 1.0 - win_rate
        kelly_fraction = (win_rate * win_loss_ratio - q) / max(0.01, win_loss_ratio)
        safe_kelly = max(0.01, min(0.20, kelly_fraction * 0.25))
        return round(current_equity * safe_kelly, 2)
