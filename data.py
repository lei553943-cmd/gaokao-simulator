"""A-share stock data via baostock."""
import baostock as bs
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

FREQ_MAP = {"daily": "d", "weekly": "w", "monthly": "m"}
# 1=后复权, 2=前复权, 3=不复权
ADJUST_MAP = {"qfq": "2", "hfq": "1", "": "3"}

# ── Session management ──────────────────────────────────────

def _login():
    lg = bs.login()
    if lg.error_code != "0":
        raise RuntimeError(f"baostock login failed: {lg.error_msg}")

def _logout():
    bs.logout()


# ── Symbol helpers ──────────────────────────────────────────

def _to_baostock(symbol: str) -> str:
    """'000001' -> 'sz.000001', '600519' -> 'sh.600519'."""
    symbol = str(symbol).zfill(6)
    if symbol.startswith(("60", "68", "900")):
        return f"sh.{symbol}"
    return f"sz.{symbol}"


# ── K-line data ─────────────────────────────────────────────

def _fetch_klines(symbol: str, freq: str, start: str, end: str, adjust: str) -> pd.DataFrame:
    bs_symbol = _to_baostock(symbol)
    bs_freq = FREQ_MAP.get(freq, "d")
    bs_adj = ADJUST_MAP.get(adjust, "2")

    _login()
    try:
        rs = bs.query_history_k_data_plus(
            bs_symbol,
            "date,open,high,low,close,volume,amount,pctChg,turn",
            start_date=start, end_date=end,
            frequency=bs_freq, adjustflag=bs_adj,
        )
        if rs.error_code != "0":
            raise RuntimeError(f"baostock query failed: {rs.error_msg}")

        rows = []
        while rs.next():
            rows.append(rs.get_row_data())

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows, columns=rs.fields)
        for col in ["open", "high", "low", "close", "volume", "amount", "pctChg", "turn"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["date"] = pd.to_datetime(df["date"])
        df = df.rename(columns={"pctChg": "pct_change", "turn": "turnover"})
        df = df.sort_values("date").reset_index(drop=True)
        return df
    finally:
        _logout()


def daily(symbol: str, start: str = "20150101", end: str = None, adjust: str = "qfq") -> pd.DataFrame:
    """日K线。symbol='000001', adjust='qfq'|'hfq'|''."""
    if end is None:
        end = datetime.now().strftime("%Y-%m-%d")
    else:
        end = _normalize_date(end)
    start = _normalize_date(start)
    return _fetch_klines(symbol, "daily", start, end, adjust)


def weekly(symbol: str, start: str = "20150101", end: str = None, adjust: str = "qfq") -> pd.DataFrame:
    """周K线."""
    if end is None:
        end = datetime.now().strftime("%Y-%m-%d")
    else:
        end = _normalize_date(end)
    start = _normalize_date(start)
    return _fetch_klines(symbol, "weekly", start, end, adjust)


def monthly(symbol: str, start: str = "20150101", end: str = None, adjust: str = "qfq") -> pd.DataFrame:
    """月K线."""
    if end is None:
        end = datetime.now().strftime("%Y-%m-%d")
    else:
        end = _normalize_date(end)
    start = _normalize_date(start)
    return _fetch_klines(symbol, "monthly", start, end, adjust)


# ── Stock lists ──────────────────────────────────────────────

def all_stocks() -> pd.DataFrame:
    """Return all A-share stocks [code, name]."""
    _login()
    try:
        rs = bs.query_stock_basic()
        rows = []
        while rs.next():
            rows.append(rs.get_row_data())
        if not rows:
            return pd.DataFrame(columns=["code", "name"])
        df = pd.DataFrame(rows, columns=rs.fields)
        df = df.rename(columns={"code": "code", "code_name": "name"})
        return df[["code", "name"]]
    finally:
        _logout()


def realtime(symbols: list = None) -> pd.DataFrame:
    """全市场实时行情（baostock 不支持实时，用日线最新一条代替）."""
    _login()
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        all_rows = []
        targets = symbols if symbols else all_stocks()["code"].tolist()[:100]
        for s in targets:
            bs_sym = _to_baostock(s)
            rs = bs.query_history_k_data_plus(
                bs_sym, "date,open,high,low,close,volume,amount,pctChg,turn",
                start_date=week_ago, end_date=today,
                frequency="d", adjustflag="2",
            )
            if rs.error_code == "0":
                last = None
                while rs.next():
                    last = rs.get_row_data()
                if last:
                    all_rows.append([s] + last)
        if not all_rows:
            return pd.DataFrame()
        cols = ["code", "date", "open", "high", "low", "close", "volume", "amount",
                "pct_change", "turnover"]
        df = pd.DataFrame(all_rows, columns=cols)
        for c in ["open", "high", "low", "close", "volume", "amount",
                   "pct_change", "turnover"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        return df
    finally:
        _logout()


# ── Index data ───────────────────────────────────────────────

def index_daily(symbol: str = "000300", start: str = "20150101", end: str = None) -> pd.DataFrame:
    """指数日线。000300=沪深300, 000905=中证500, 000001=上证."""
    if end is None:
        end = datetime.now().strftime("%Y-%m-%d")
    else:
        end = _normalize_date(end)
    start = _normalize_date(start)
    # Index codes in baostock
    index_map = {"000300": "sh.000300", "000905": "sh.000905", "000001": "sh.000001",
                 "399001": "sz.399001", "399006": "sz.399006"}
    bs_sym = index_map.get(str(symbol).zfill(6), f"sh.{symbol}")

    _login()
    try:
        rs = bs.query_history_k_data_plus(
            bs_sym, "date,open,high,low,close,volume,amount,pctChg,turn",
            start_date=start, end_date=end, frequency="d", adjustflag="3",
        )
        rows = []
        while rs.next():
            rows.append(rs.get_row_data())
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows, columns=rs.fields)
        for col in ["open", "high", "low", "close", "volume", "amount", "pctChg", "turn"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["date"] = pd.to_datetime(df["date"])
        return df.sort_values("date").reset_index(drop=True)
    finally:
        _logout()


# ── Utility ──────────────────────────────────────────────────

def _normalize_date(d: str) -> str:
    """'20250101' -> '2025-01-01'."""
    if len(d) == 8:
        return f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    return d


def add_market(symbol: str) -> str:
    """纯数字代码加交易所前缀。'600519' -> 'sh600519'."""
    symbol = str(symbol).zfill(6)
    if symbol.startswith(("60", "68", "900")):
        return f"sh{symbol}"
    if symbol.startswith(("00", "30", "002")):
        return f"sz{symbol}"
    if symbol.startswith(("4", "8")):
        return f"bj{symbol}"
    return f"sz{symbol}"


# ── Quick test ───────────────────────────────────────────────

if __name__ == "__main__":
    df = daily("000001", start="20260101")
    print(df.head())
    print(f"\nRows: {len(df)}, Columns: {list(df.columns)}")
