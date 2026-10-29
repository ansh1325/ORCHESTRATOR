"""Sub-millisecond Paper Trading Execution & Order Lifecycle Simulator."""
from typing import Dict, Any, List
import time

class PaperExecutionEngine:
    def __init__(self, starting_balance: float = 100000.0):
        self.balance = starting_balance
        self.positions: Dict[str, float] = {}
        self.order_history: List[Dict[str, Any]] = []

    def execute_paper_order(self, symbol: str, side: str, quantity: float, price: float) -> Dict[str, Any]:
        cost = quantity * price
        order = {
            "order_id": f"ORD_{len(self.order_history) + 1}",
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "fill_price": price,
            "timestamp": time.time(),
            "status": "FILLED"
        }
        if side.upper() == "BUY":
            self.balance -= cost
            self.positions[symbol] = self.positions.get(symbol, 0.0) + quantity
        elif side.upper() == "SELL":
            self.balance += cost
            self.positions[symbol] = max(0.0, self.positions.get(symbol, 0.0) - quantity)
        self.order_history.append(order)
        return order
