import plotly.graph_objects as go
from typing import Optional

from .force_indicators import SIGNAL_COLOR
from .gemini_analyst import Judgment

ACTION_EMOJI = {"BUY": "🟢 BUY", "SELL": "🔴 SELL", "NEUTRAL": "🟡 NEUTRAL"}
CONF_LABEL   = {"HIGH": "⬆ HIGH", "MEDIUM": "➡ MED", "LOW": "⬇ LOW"}


def _panel_html(j: Optional[Judgment]) -> str:
    if j is None:
        return ""
    c  = j.color()
    a  = ACTION_EMOJI.get(j.action, j.action)
    cf = CONF_LABEL.get(j.confidence, j.confidence)
    rr = f"  RR {j.rr_ratio}" if j.rr_ratio else ""
    return (
        f"<b style='color:{c};font-size:16px'>{a}</b>"
        f"  <span style='color:#aaa'>{cf}{rr}</span><br>"
        f"<table style='color:#ddd;font-size:12px;margin-top:4px'>"
        f"<tr><td>ENTRY</td><td style='padding-left:10px;color:#fff'><b>{j.entry}</b></td></tr>"
        f"<tr><td>STOP LOSS</td><td style='padding-left:10px;color:#ef5350'><b>{j.sl}</b></td></tr>"
        f"<tr><td>TP1</td><td style='padding-left:10px;color:#26a69a'><b>{j.tp1}</b></td></tr>"
        f"<tr><td>TP2</td><td style='padding-left:10px;color:#00e676'><b>{j.tp2}</b></td></tr>"
        f"</table>"
        f"<div style='color:#bbb;font-size:11px;margin-top:6px;font-style:italic'>{j.reason}</div>"
    )


def _annotations(j: Optional[Judgment]) -> list[dict]:
    if j is None:
        return []
    return [dict(
        text      = _panel_html(j),
        x=0.01, y=1.12, xref="paper", yref="paper",
        showarrow = False,
        align     = "left",
        bgcolor   = "rgba(20,20,30,0.85)",
        bordercolor = j.color(),
        borderwidth = 1,
        borderpad = 8,
        font      = dict(size=12),
    )]


def build_dashboard(
    charts:    dict[str, go.Figure],
    signals:   dict[str, str],
    judgments: dict[str, Optional[Judgment]] = None,
) -> str:
    symbols = list(charts.keys())
    if not symbols:
        return "<html><body style='background:#111;color:#eee'>No data yet.</body></html>"

    judgments = judgments or {}
    fig       = go.Figure()
    buttons   = []
    trace_idx = 0
    vis_map:  dict[str, list[int]] = {}

    for sym in symbols:
        indices = []
        for trace in charts[sym].data:
            trace.visible = (sym == symbols[0])
            fig.add_trace(trace)
            indices.append(trace_idx)
            trace_idx += 1
        vis_map[sym] = indices

    total = trace_idx

    for sym in symbols:
        visible = [False] * total
        for i in vis_map[sym]:
            visible[i] = True

        sig   = signals.get(sym, "")
        j     = judgments.get(sym)
        color = SIGNAL_COLOR.get(sig, "#888")
        badge = f"  {ACTION_EMOJI.get(j.action,'')}" if j else ""

        buttons.append(dict(
            label  = f"{sym}{badge}",
            method = "update",
            args   = [
                {"visible": visible},
                {
                    "title.text":       f"{sym}  |  {sig}",
                    "title.font.color": color,
                    "annotations":      _annotations(j),
                }
            ],
        ))

    first_sig   = signals.get(symbols[0], "")
    first_color = SIGNAL_COLOR.get(first_sig, "#888")
    first_j     = judgments.get(symbols[0])

    fig.update_layout(
        template         = "plotly_dark",
        title_text       = f"{symbols[0]}  |  {first_sig}",
        title_font_color = first_color,
        height           = 720,
        xaxis_rangeslider_visible = False,
        showlegend       = False,
        annotations      = _annotations(first_j),
        updatemenus=[dict(
            type="dropdown", direction="down",
            x=0.0, y=1.22, showactive=True,
            buttons=buttons,
        )],
    )

    return fig.to_html(full_html=True, include_plotlyjs=True)
