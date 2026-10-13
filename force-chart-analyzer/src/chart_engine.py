import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional

from .force_indicators import SIGNAL_COLOR, elder_force_index, rsi, macd, bollinger


def build_chart(
    symbol: str,
    df:     pd.DataFrame,
    force:  pd.Series,
    sig:    str,
    judgment=None,          # Optional[Judgment]
) -> go.Figure:

    rsi_s              = rsi(df)
    macd_l, macd_s, macd_h = macd(df)
    bb_u, bb_m, bb_l   = bollinger(df)

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.55, 0.25, 0.20],
        subplot_titles=(
            f"{symbol} Price + BB",
            f"Force Index — {sig}  |  RSI: {round(float(rsi_s.iloc[-1]), 1) if len(rsi_s) else '?'}",
            "MACD",
        ),
        vertical_spacing=0.04,
    )

    # ── candlestick ───────────────────────────────────────────────────────────
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["open"], high=df["high"],
        low=df["low"], close=df["close"], name="Price",
    ), row=1, col=1)

    # ── bollinger bands ───────────────────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=bb_u.index, y=bb_u.values, line=dict(color="rgba(100,149,237,0.4)", width=1),
        name="BB Upper", showlegend=False,
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=bb_m.index, y=bb_m.values, line=dict(color="rgba(100,149,237,0.6)", width=1, dash="dot"),
        name="BB Mid", showlegend=False,
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=bb_l.index, y=bb_l.values, line=dict(color="rgba(100,149,237,0.4)", width=1),
        fill="tonexty", fillcolor="rgba(100,149,237,0.05)",
        name="BB Lower", showlegend=False,
    ), row=1, col=1)

    # ── judgment levels on price chart ────────────────────────────────────────
    if judgment and judgment.action != "NEUTRAL":
        price_range = df.index

        def hline(price: float, color: str, dash: str, label: str):
            fig.add_hline(
                y=price, line_color=color, line_dash=dash, line_width=1.2,
                annotation_text=f"{label}: {price}",
                annotation_position="right",
                annotation_font_color=color,
                row=1, col=1,
            )

        hline(judgment.entry, "#ffffff",  "solid",  "ENTRY")
        hline(judgment.sl,    "#ef5350",  "dash",   "SL")
        hline(judgment.tp1,   "#26a69a",  "dot",    "TP1")
        hline(judgment.tp2,   "#00e676",  "dot",    "TP2")

    # ── force index ───────────────────────────────────────────────────────────
    bar_colors = ["#ef5350" if v < 0 else "#26a69a" for v in force]
    fig.add_trace(go.Bar(
        x=force.index, y=force.values,
        marker_color=bar_colors, name="Force",
    ), row=2, col=1)
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)

    # ── RSI overlay on force subplot ──────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=rsi_s.index, y=rsi_s.values,
        line=dict(color="#ce93d8", width=1.2),
        name="RSI", yaxis="y4",
    ), row=2, col=1)
    fig.add_hline(y=70, line_dash="dot", line_color="rgba(239,83,80,0.4)",   row=2, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="rgba(38,166,154,0.4)",  row=2, col=1)

    # ── MACD ──────────────────────────────────────────────────────────────────
    hist_colors = ["#ef5350" if v < 0 else "#26a69a" for v in macd_h]
    fig.add_trace(go.Bar(
        x=macd_h.index, y=macd_h.values,
        marker_color=hist_colors, name="MACD Hist",
    ), row=3, col=1)
    fig.add_trace(go.Scatter(
        x=macd_l.index, y=macd_l.values,
        line=dict(color="#42a5f5", width=1.2), name="MACD",
    ), row=3, col=1)
    fig.add_trace(go.Scatter(
        x=macd_s.index, y=macd_s.values,
        line=dict(color="#ff7043", width=1.2), name="Signal",
    ), row=3, col=1)

    sig_color = SIGNAL_COLOR.get(sig, "#888")
    fig.update_layout(
        template    = "plotly_dark",
        showlegend  = False,
        xaxis_rangeslider_visible = False,
        title_text  = f"{symbol}  |  {sig}",
        title_font_color = sig_color,
        height = 700,
    )
    return fig
