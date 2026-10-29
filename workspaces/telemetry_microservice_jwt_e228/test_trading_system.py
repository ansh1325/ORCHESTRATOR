"""Comprehensive Pytest Verification Suite for Quantitative Trading Engine."""
import pytest
from trading_strategy import MomentumStrategy, VolatilityBreakoutStrategy
from risk_manager import RiskManager
from backtest_engine import BacktestEngine
from paper_execution_loop import PaperExecutionEngine

def test_momentum_and_volatility_signals():
    strat = MomentumStrategy(short_window=3, long_window=5)
    prices_up = [100.0, 101.0, 102.0, 104.0, 106.0, 108.0]
    signal = strat.generate_signal(prices_up)
    assert signal == "BUY"
    vol_strat = VolatilityBreakoutStrategy()
    breakout = vol_strat.evaluate_breakout(current_price=110.0, high=105.0, low=95.0)
    assert breakout == "BUY"

def test_risk_manager_circuit_breaker():
    rm = RiskManager(max_drawdown_pct=5.0, initial_equity=100000.0)
    normal = rm.check_portfolio_risk(98000.0)
    assert normal["circuit_breaker_active"] is False
    assert normal["trade_allowed"] is True
    breach = rm.check_portfolio_risk(93000.0)
    assert breach["circuit_breaker_active"] is True
    assert breach["trade_allowed"] is False
    pos_size = rm.calculate_position_size(93000.0)
    assert pos_size == 0.0

def test_backtest_engine_metrics():
    bt = BacktestEngine(initial_capital=100000.0)
    returns = [0.01, 0.005, -0.002, 0.015, -0.001, 0.02, 0.008]
    metrics = bt.run_backtest(returns)
    assert metrics["sharpe_ratio"] >= 2.0
    assert metrics["total_trades"] == 7
    assert metrics["max_drawdown_pct"] < 5.0

def test_paper_execution_order_flow():
    engine = PaperExecutionEngine(starting_balance=50000.0)
    order = engine.execute_paper_order("BTC/USDT", "BUY", 0.5, 60000.0)
    assert order["status"] == "FILLED"
    assert engine.positions["BTC/USDT"] == 0.5
    assert engine.balance == 20000.0
