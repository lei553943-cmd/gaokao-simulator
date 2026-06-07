"""Strategies for backtrader."""
import backtrader as bt
import numpy as np
from datetime import datetime


def _ts_to_str(ts):
    """Convert backtrader timestamp to date string."""
    if ts is None or ts == 0:
        return ""
    if isinstance(ts, (int, float)):
        return bt.num2date(ts).strftime("%Y-%m-%d")
    return ts.strftime("%Y-%m-%d")


class _TradeCollector:
    """Mixin: collects closed trades via notify_trade."""

    def __init__(self):
        self.trade_list = []

    def notify_trade(self, trade):
        if trade.isclosed:
            self.trade_list.append({
                "entry": _ts_to_str(trade.dtopen),
                "exit": _ts_to_str(trade.dtclose),
                "pnl": round(trade.pnlcomm, 2),
            })


class SmaCross(_TradeCollector, bt.Strategy):
    """双均线交叉：金叉买入，死叉卖出。"""
    params = dict(fast=5, slow=20)

    def __init__(self):
        _TradeCollector.__init__(self)
        self.fast_ma = bt.ind.SMA(period=self.p.fast)
        self.slow_ma = bt.ind.SMA(period=self.p.slow)
        self.crossover = bt.ind.CrossOver(self.fast_ma, self.slow_ma)

    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.order_target_percent(target=0.95)
        elif self.crossover < 0:
            self.order_target_percent(target=0)


class RsiMeanReversion(_TradeCollector, bt.Strategy):
    """RSI均值回归：超卖买入，超买卖出."""
    params = dict(rsi_period=14, oversold=30, overbought=70, rsi_exit=50)

    def __init__(self):
        _TradeCollector.__init__(self)
        self.rsi = bt.ind.RSI(period=self.p.rsi_period)

    def next(self):
        if not self.position:
            if self.rsi < self.p.oversold:
                self.order_target_percent(target=0.95)
        else:
            if self.rsi > self.p.overbought or self.rsi > self.p.rsi_exit:
                self.order_target_percent(target=0)


class MacdCross(_TradeCollector, bt.Strategy):
    """MACD金叉死叉."""
    params = dict(fast=12, slow=26, signal=9)

    def __init__(self):
        _TradeCollector.__init__(self)
        self.macd = bt.ind.MACD(period_me1=self.p.fast,
                                period_me2=self.p.slow,
                                period_signal=self.p.signal)
        self.crossover = bt.ind.CrossOver(self.macd.macd, self.macd.signal)

    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.order_target_percent(target=0.95)
        elif self.crossover < 0:
            self.order_target_percent(target=0)


class BollingerBreakout(_TradeCollector, bt.Strategy):
    """布林带突破：上穿上轨买入，下穿中轨卖出."""
    params = dict(period=20, devfactor=2.0)

    def __init__(self):
        _TradeCollector.__init__(self)
        self.bb = bt.ind.BollingerBands(period=self.p.period, devfactor=self.p.devfactor)
        self.signal = bt.ind.CrossOver(self.data.close, self.bb.top)

    def next(self):
        if not self.position:
            if self.signal > 0:
                self.order_target_percent(target=0.95)
        elif self.data.close < self.bb.mid:
            self.order_target_percent(target=0)


class TurtleTrading(_TradeCollector, bt.Strategy):
    """海龟交易法：20日突破买入，10日反向突破卖出."""
    params = dict(entry_period=20, exit_period=10)

    def __init__(self):
        _TradeCollector.__init__(self)
        self.high_entry = bt.ind.Highest(self.data.high, period=self.p.entry_period)
        self.low_exit = bt.ind.Lowest(self.data.low, period=self.p.exit_period)

    def next(self):
        if not self.position:
            if self.data.close > self.high_entry[-1]:
                self.order_target_percent(target=0.95)
        elif self.data.close < self.low_exit[-1]:
            self.order_target_percent(target=0)
