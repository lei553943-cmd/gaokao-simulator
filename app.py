"""Streamlit dashboard for stock quant."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

from data import daily, all_stocks, weekly, monthly
from backtest import run_strategy_name

st.set_page_config(page_title="股票量化系统", layout="wide")

STRATEGIES = {
    "双均线交叉": ("sma_cross", {"fast": 5, "slow": 20}),
    "RSI均值回归": ("rsi", {"rsi_period": 14, "oversold": 30, "overbought": 70}),
    "MACD金叉": ("macd", {"fast": 12, "slow": 26, "signal": 9}),
    "布林带突破": ("bollinger", {"period": 20, "devfactor": 2.0}),
    "海龟交易": ("turtle", {"entry_period": 20, "exit_period": 10}),
}


# ── Sidebar ──────────────────────────────────────────────
st.sidebar.title("参数配置")

symbol = st.sidebar.text_input("股票代码", value="000001", help="纯数字，如 000001(平安银行)、600519(茅台)")

strat_name = st.sidebar.selectbox("策略", list(STRATEGIES.keys()))

col1, col2 = st.sidebar.columns(2)
start_date = col1.date_input("开始日期", value=datetime(2020, 1, 1))
end_date = col2.date_input("结束日期", value=datetime.now())

period = st.sidebar.selectbox("K线周期", ["日线", "周线", "月线"])

# Strategy-specific params
st.sidebar.subheader("策略参数")
strat_key, default_params = STRATEGIES[strat_name]
params = {}
for k, v in default_params.items():
    params[k] = st.sidebar.number_input(k, value=v, step=1)

run_btn = st.sidebar.button("运行回测", type="primary", use_container_width=True)

# ── Main ─────────────────────────────────────────────────
st.title(f"股票量化回测系统")

if run_btn:
    with st.spinner("获取数据并回测中..."):
        s = start_date.strftime("%Y%m%d")
        e = end_date.strftime("%Y%m%d")

        if period == "周线":
            df = weekly(symbol, start=s, end=e)
        elif period == "月线":
            df = monthly(symbol, start=s, end=e)
        else:
            df = daily(symbol, start=s, end=e)

        if df is None or df.empty:
            st.error(f"未找到 {symbol} 的数据，请检查代码是否正确")
        else:
            result = run_strategy_name(df, strat_key, **params)

            # ── Metrics ───────────────────────────────────
            m1, m2, m3, m4, m5, m6 = st.columns(6)
            m1.metric("累计收益 %", f"{result['total_return']:.2f}%")
            m2.metric("年化收益 %", f"{result['cagr']:.2f}%")
            m3.metric("夏普比率", f"{result['sharpe']:.2f}")
            m4.metric("最大回撤 %", f"{result['max_drawdown']:.2f}%")
            m5.metric("胜率 %", f"{result['win_rate']:.2f}%")
            m6.metric("年化波动 %", f"{result['annual_volatility']:.2f}%")

            st.metric("交易次数", result['total_trades'])

            # ── Charts ────────────────────────────────────
            col_left, col_right = st.columns([2, 1])

            with col_left:
                # K-line + equity curve
                st.subheader("价格走势 & 净值曲线")
                fig = make_subplots(
                    rows=2, cols=1, shared_xaxes=True,
                    row_heights=[0.6, 0.4],
                    vertical_spacing=0.05,
                )

                # K-line
                fig.add_trace(
                    go.Candlestick(
                        x=df["date"],
                        open=df["open"],
                        high=df["high"],
                        low=df["low"],
                        close=df["close"],
                        name="K线",
                    ),
                    row=1, col=1,
                )

                # Equity
                eq = result["equity_curve"]
                fig.add_trace(
                    go.Scatter(
                        x=eq["date"],
                        y=eq["equity"],
                        name="净值",
                        line=dict(color="blue", width=2),
                    ),
                    row=2, col=1,
                )

                fig.update_layout(
                    height=600,
                    xaxis_rangeslider_visible=False,
                    template="plotly_dark",
                    margin=dict(l=0, r=0, t=0, b=0),
                )
                fig.update_yaxes(title_text="价格", row=1, col=1)
                fig.update_yaxes(title_text="净值", row=2, col=1)
                st.plotly_chart(fig, use_container_width=True)

            with col_right:
                # Trade list
                st.subheader("交易明细")
                if result["trades"]:
                    trades_df = pd.DataFrame(result["trades"])
                    st.dataframe(trades_df, height=530, use_container_width=True,
                                 hide_index=True)
                else:
                    st.write("无交易记录")

            # ── Raw data ───────────────────────────────────
            with st.expander("原始数据"):
                st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("输入股票代码和参数，点击「运行回测」开始。")

    # Quick stock search
    st.subheader("股票列表速查")
    search = st.text_input("搜索股票", placeholder="输入名称或代码...")
    if search:
        try:
            all_s = all_stocks()
            if not all_s.empty:
                # baostock returns codes like 'sh.600519', strip prefix for display
                all_s["code_clean"] = all_s["code"].str.replace(r"^(sh|sz|bj)\.", "", regex=True)
                mask = all_s["code_clean"].str.contains(search) | all_s["name"].str.contains(search)
                display = all_s[mask].head(30)[["code_clean", "name"]]
                display.columns = ["代码", "名称"]
                st.dataframe(display, use_container_width=True, hide_index=True)
        except Exception as e:
            st.warning(f"获取股票列表失败: {e}")
