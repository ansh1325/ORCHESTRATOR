"""Algorithmic Quantitative Trading Strategy Engine."""
from typing import List, Dict, Any

class MomentumStrategy:
    def __init__(self, short_window: int = 3, long_window: int = 5):
        self.short_window = short_window
        self.long_window = long_window

    def generate_signal(self, prices: List[float]) -> str:
        """Computes moving average crossover: returns 'BUY', 'SELL', or 'HOLD'."""
        if len(prices) < self.long_window:
            return "HOLD"
        short_ma = sum(prices[-self.short_window:]) / self.short_window
        long_ma = sum(prices[-self.long_window:]) / self.long_window
        if short_ma > long_ma * 1.001:
            return "BUY"
        elif short_ma < long_ma * 0.999:
            return "SELL"
        return "HOLD"

class VolatilityBreakoutStrategy:
    def __init__(self, multiplier: float = 1.5):
        self.multiplier = multiplier

    def evaluate_breakout(self, current_price: float, high: float, low: float) -> str:
        range_val = high - low
        if range_val <= 0:
            return "HOLD"
        if current_price > high:
            return "BUY"
        elif current_price < low:
            return "SELL"
        return "HOLD"
