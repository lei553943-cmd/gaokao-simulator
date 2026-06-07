"""Backtesting engine wrapping backtrader."""
import backtrader as bt
import backtrader.analyzers as btanalyzers
import numpy as np
import pandas as pd
from datetime import datetime
import io
import sys


def run(data: pd.DataFrame, strategy_cls, **strategy_kwargs) -> dict:
    """
    Run a backtest and return metrics dict.

    Args:
        data: DataFrame from data.py (must have date/open/high/low/close/volume).
        strategy_cls: backtrader.Strategy subclass.
        **strategy_kwargs: passed to strategy as params.

    Returns dict with keys: total_return, cagr, sharpe, max_drawdown,
      win_rate, annual_volatility, equity_curve (DataFrame), trades (list).
    """
    cerebro = bt.Cerebro()

    # ── Data ─────────────────────────────────────────────
    df = data.copy()
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")
    # Ensure backtrader-compatible column names
    rename = {"open": "Open", "high": "High", "low": "Low",
              "close": "Close", "volume": "Volume"}
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col not in df.columns:
            df[col] = 0

    feed = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(feed)

    # ── Strategy ─────────────────────────────────────────
    cerebro.addstrategy(strategy_cls, **strategy_kwargs)

    # ── Capital / Commission ─────────────────────────────
    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.0003)  # 万三佣金 + 印花税
    cerebro.addsizer(bt.sizers.PercentSizer, percents=95)

    # ── Analyzers ────────────────────────────────────────
    cerebro.addanalyzer(btanalyzers.SharpeRatio, _name="sharpe",
                        riskfreerate=0.03, annualize=True)
    cerebro.addanalyzer(btanalyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(btanalyzers.TradeAnalyzer, _name="trades")
    cerebro.addanalyzer(btanalyzers.TimeReturn, _name="timereturn")
    cerebro.addanalyzer(btanalyzers.AnnualReturn, _name="annual")

    # ── Run ──────────────────────────────────────────────
    start_value = cerebro.broker.getvalue()
    results = cerebro.run()
    strat = results[0]
    end_value = cerebro.broker.getvalue()

    # ── Extract metrics ──────────────────────────────────
    total_return = (end_value / start_value - 1) * 100

    # CAGR
    years = len(df) / 252
    cagr = ((end_value / start_value) ** (1 / years) - 1) * 100 if years > 0 else 0

    # Sharpe
    sharpe = strat.analyzers.sharpe.get_analysis()
    sharpe_ratio = sharpe.get("sharperatio", 0) or 0

    # Max drawdown
    dd = strat.analyzers.drawdown.get_analysis()
    max_dd = dd.get("max", {}).get("drawdown", 0) or 0

    # Win rate
    ta = strat.analyzers.trades.get_analysis()
    total_trades = ta.get("total", {}).get("total", 0)
    won = ta.get("won", {}).get("total", 0)
    win_rate = (won / total_trades * 100) if total_trades > 0 else 0

    # Equity curve
    tr = strat.analyzers.timereturn.get_analysis()
    equity_df = pd.DataFrame(
        {"date": list(tr.keys()), "return": list(tr.values())}
    )
    equity_df["equity"] = start_value * (1 + equity_df["return"]).cumprod()

    # Annual volatility
    if len(tr) > 1:
        rets = pd.Series(list(tr.values()))
        annual_vol = rets.std() * np.sqrt(252) * 100
    else:
        annual_vol = 0

    # Trades list
    trades = getattr(strat, "trade_list", [])

    return {
        "total_return": round(total_return, 2),
        "cagr": round(cagr, 2),
        "sharpe": round(sharpe_ratio, 2),
        "max_drawdown": round(max_dd, 2),
        "win_rate": round(win_rate, 2),
        "annual_volatility": round(annual_vol, 2),
        "total_trades": total_trades,
        "start_value": start_value,
        "end_value": round(end_value, 2),
        "equity_curve": equity_df,
        "trades": trades,
    }


def run_strategy_name(data: pd.DataFrame, name: str, **kwargs):
    """Run a strategy by name. Names: sma_cross, rsi, macd, bollinger, turtle."""
    from strategy import SmaCross, RsiMeanReversion, MacdCross, BollingerBreakout, TurtleTrading
    mapping = {
        "sma_cross": SmaCross,
        "rsi": RsiMeanReversion,
        "macd": MacdCross,
        "bollinger": BollingerBreakout,
        "turtle": TurtleTrading,
    }
    cls = mapping.get(name)
    if cls is None:
        raise ValueError(f"Unknown strategy: {name}. Options: {list(mapping.keys())}")
    return run(data, cls, **kwargs)
