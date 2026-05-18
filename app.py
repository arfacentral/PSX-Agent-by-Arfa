import html

import pandas as pd
import streamlit as st

from psx_agent.report import build_morning_report


st.set_page_config(page_title="PSX Agent by Arfa", layout="wide")

st.markdown(
    """
    <style>
    :root {
        --ink: #f7fbff;
        --muted: #9fb3c8;
        --panel: #101827;
        --panel-2: #0b1220;
        --line: #24415f;
        --green: #22f2a6;
        --green-soft: rgba(34, 242, 166, .16);
        --amber: #ffd166;
        --amber-soft: rgba(255, 209, 102, .17);
        --red: #ff4d6d;
        --red-soft: rgba(255, 77, 109, .17);
        --blue: #40c9ff;
        --blue-soft: rgba(64, 201, 255, .16);
        --violet: #b56cff;
    }
    .stApp {
        background:
            radial-gradient(circle at 15% 8%, rgba(64, 201, 255, .20), transparent 26%),
            radial-gradient(circle at 85% 0%, rgba(34, 242, 166, .17), transparent 28%),
            linear-gradient(180deg, #050814 0%, #08111f 45%, #050814 100%);
        color: var(--ink);
    }
    .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp label,
    .stApp span, .stApp div {
        letter-spacing: 0;
    }
    .stApp h1, .stApp h2, .stApp h3,
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stCaptionContainer"],
    [data-testid="stText"] {
        color: var(--ink) !important;
    }
    [data-testid="stSidebar"],
    [data-testid="collapsedControl"] {
        display: none;
    }
    [data-testid="stHeader"] {
        background: rgba(5, 8, 20, .76);
        backdrop-filter: blur(12px);
    }
    .hero {
        position: relative;
        overflow: hidden;
        background:
            linear-gradient(135deg, rgba(64, 201, 255, .18) 0%, rgba(181, 108, 255, .15) 46%, rgba(34, 242, 166, .20) 100%),
            #0a1322;
        border: 1px solid rgba(64, 201, 255, .42);
        border-radius: 14px;
        padding: 26px 28px;
        margin-bottom: 18px;
        color: white;
        box-shadow: 0 0 38px rgba(64, 201, 255, .16), inset 0 0 38px rgba(34, 242, 166, .08);
    }
    .hero:after {
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,.08) 50%, transparent 100%);
        opacity: .28;
        pointer-events: none;
    }
    .hero h1 {
        position: relative;
        margin: 0 0 6px 0;
        font-size: 34px;
        line-height: 1.12;
        letter-spacing: 0;
        color: #ffffff !important;
        text-shadow: 0 0 18px rgba(64, 201, 255, .55);
    }
    .hero p {
        position: relative;
        margin: 0;
        color: rgba(247,251,255,.88) !important;
        font-size: 16px;
    }
    .metric-card {
        background: var(--panel);
        border: 1px solid var(--line);
        border-left: 6px solid var(--blue);
        border-radius: 12px;
        padding: 16px 18px;
        min-height: 104px;
        box-shadow: 0 14px 34px rgba(0, 0, 0, .25), inset 0 0 24px rgba(64, 201, 255, .04);
    }
    .metric-card.green { border-left-color: var(--green); background: linear-gradient(180deg, rgba(34,242,166,.10) 0%, var(--panel) 100%); }
    .metric-card.amber { border-left-color: var(--amber); background: linear-gradient(180deg, rgba(255,209,102,.12) 0%, var(--panel) 100%); }
    .metric-card.red { border-left-color: var(--red); background: linear-gradient(180deg, rgba(255,77,109,.12) 0%, var(--panel) 100%); }
    .metric-card.blue { border-left-color: var(--blue); background: linear-gradient(180deg, rgba(64,201,255,.12) 0%, var(--panel) 100%); }
    .metric-label {
        color: var(--muted);
        font-size: 13px;
        margin-bottom: 8px;
    }
    .metric-value {
        color: var(--ink);
        font-size: 30px;
        font-weight: 760;
        line-height: 1;
    }
    .metric-note {
        color: var(--muted);
        font-size: 12px;
        margin-top: 8px;
    }
    .idea-card {
        background: linear-gradient(180deg, rgba(16,24,39,.96), rgba(11,18,32,.96));
        border: 1px solid var(--line);
        border-left: 7px solid var(--blue);
        border-radius: 12px;
        padding: 18px;
        margin: 12px 0 14px 0;
        box-shadow: 0 12px 32px rgba(0,0,0,.30);
    }
    .idea-card.buy { border-left-color: var(--green); }
    .idea-card.wait { border-left-color: var(--amber); }
    .idea-card.avoid { border-left-color: var(--red); }
    .idea-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 12px;
    }
    .symbol {
        font-size: 24px;
        font-weight: 780;
        color: var(--ink);
    }
    .badge {
        display: inline-block;
        border-radius: 999px;
        padding: 6px 10px;
        font-size: 12px;
        font-weight: 760;
        border: 1px solid transparent;
        white-space: nowrap;
    }
    .badge.buy { background: var(--green-soft); color: var(--green); border-color: rgba(34,242,166,.48); }
    .badge.wait { background: var(--amber-soft); color: var(--amber); border-color: rgba(255,209,102,.48); }
    .badge.avoid { background: var(--red-soft); color: var(--red); border-color: rgba(255,77,109,.48); }
    .price-grid {
        display: grid;
        grid-template-columns: repeat(5, minmax(104px, 1fr));
        gap: 10px;
        margin: 12px 0;
    }
    .price-cell {
        background: rgba(5, 8, 20, .72);
        border: 1px solid rgba(64, 201, 255, .22);
        border-radius: 10px;
        padding: 10px;
    }
    .price-label {
        color: var(--muted);
        font-size: 12px;
    }
    .price-value {
        color: var(--ink);
        font-size: 17px;
        font-weight: 760;
        margin-top: 2px;
    }
    .reason-list {
        margin: 8px 0 0 18px;
        color: #d8e5f2;
    }
    .small-note {
        color: var(--muted);
        font-size: 13px;
        margin-top: 8px;
    }
    [data-testid="stAlert"] {
        background: rgba(64, 201, 255, .13) !important;
        border: 1px solid rgba(64, 201, 255, .32) !important;
        color: var(--ink) !important;
        border-radius: 10px !important;
    }
    [data-testid="stAlert"] * {
        color: var(--ink) !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        border-bottom: 1px solid var(--line);
    }
    .stTabs [data-baseweb="tab"] {
        color: var(--muted) !important;
        background: transparent !important;
        font-weight: 650;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: var(--green) !important;
        border-bottom-color: var(--green) !important;
    }
    [data-testid="stSelectbox"] label,
    [data-testid="stSelectbox"] div {
        color: var(--ink) !important;
    }
    [data-baseweb="select"] > div {
        background: #0f1726 !important;
        border-color: rgba(64, 201, 255, .34) !important;
    }
    [data-testid="stDataFrame"] {
        background: var(--panel-2);
        border: 1px solid rgba(64, 201, 255, .20);
        border-radius: 10px;
    }
    .stButton button {
        background: linear-gradient(135deg, rgba(64,201,255,.20), rgba(34,242,166,.18)) !important;
        color: var(--ink) !important;
        border: 1px solid rgba(64,201,255,.55) !important;
        border-radius: 10px !important;
        box-shadow: 0 0 22px rgba(64,201,255,.14);
    }
    @media (max-width: 760px) {
        .hero h1 { font-size: 28px; }
        .price-grid { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
        .idea-top { align-items: flex-start; flex-direction: column; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>PSX Agent by Arfa</h1>
        <p>Fast pre-market screening from PSX Terminal data with clear price levels and risk notes.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

_, toolbar_right = st.columns([5, 1])
with toolbar_right:
    refresh = st.button("Refresh data", use_container_width=True)

if refresh:
    st.cache_data.clear()


@st.cache_data(ttl=15)
def load_local_report() -> dict:
    return build_morning_report().model_dump()


def quick_signal(open_price, high, low, close, volume, change_percent) -> str:
    if pd.isna(close):
        return "WAIT"
    if volume is None or pd.isna(volume) or volume <= 0:
        return "WAIT"
    if pd.isna(open_price):
        if not pd.isna(change_percent) and change_percent > 1:
            return "BUY WATCH"
        if not pd.isna(change_percent) and change_percent < 0:
            return "AVOID"
        return "WAIT"
    if close > open_price and not pd.isna(high) and high > low and close >= low + ((high - low) * 0.7):
        return "BUY WATCH"
    if close < open_price:
        return "AVOID"
    return "WAIT"


def action_class(action: str) -> str:
    normalized = action.strip().upper()
    if normalized == "BUY WATCH":
        return "buy"
    if normalized == "WAIT":
        return "wait"
    if normalized == "AVOID":
        return "avoid"
    return "wait"


def action_color(action: str) -> str:
    css_class = action_class(action)
    if css_class == "buy":
        return "#22f2a6"
    if css_class == "avoid":
        return "#ff4d6d"
    return "#ffd166"


def fmt_number(value, decimals: int = 2) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{float(value):,.{decimals}f}"


def fmt_volume(value) -> str:
    if value is None or pd.isna(value):
        return "-"
    number = float(value)
    if number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    if number >= 1_000:
        return f"{number / 1_000:.0f}K"
    return f"{number:.0f}"


def metric_card(label: str, value: str, note: str, tone: str = "blue") -> None:
    st.markdown(
        f"""
        <div class="metric-card {html.escape(tone)}">
            <div class="metric-label">{html.escape(label)}</div>
            <div class="metric-value">{html.escape(value)}</div>
            <div class="metric-note">{html.escape(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def color_action(value: str) -> str:
    if value == "BUY WATCH":
        return "background-color: rgba(34, 242, 166, .18); color: #063d2a; font-weight: 800;"
    if value == "WAIT":
        return "background-color: rgba(255, 209, 102, .24); color: #5c3d00; font-weight: 800;"
    if value == "AVOID":
        return "background-color: rgba(255, 77, 109, .22); color: #661326; font-weight: 800;"
    return ""


def color_change(value) -> str:
    if pd.isna(value):
        return ""
    if value > 0:
        return "background-color: rgba(34, 242, 166, .18); color: #063d2a; font-weight: 800;"
    if value < 0:
        return "background-color: rgba(255, 77, 109, .22); color: #661326; font-weight: 800;"
    return "background-color: rgba(255, 209, 102, .24); color: #5c3d00; font-weight: 800;"


def color_quick_signal(value: str) -> str:
    return color_action(value)


def render_idea_card(idea: dict) -> None:
    action = str(idea["action"])
    css_class = action_class(action)
    border_color = action_color(action)
    reasons = "".join(f"<li>{html.escape(reason)}</li>" for reason in idea.get("reasons", []))
    st.markdown(
        f"""
        <div class="idea-card {css_class}" style="border-left-color: {border_color};">
            <div class="idea-top">
                <div>
                    <div class="symbol">{html.escape(str(idea["symbol"]))}</div>
                    <div class="small-note">Score {fmt_number(idea["score"], 1)} · {html.escape(str(idea["confidence"]))}</div>
                </div>
                <span class="badge {css_class}">{html.escape(action)}</span>
            </div>
            <div class="price-grid">
                <div class="price-cell"><div class="price-label">Last</div><div class="price-value">{fmt_number(idea["last_close"])}</div></div>
                <div class="price-cell"><div class="price-label">Entry</div><div class="price-value">{fmt_number(idea["entry_low"])} - {fmt_number(idea["entry_high"])}</div></div>
                <div class="price-cell"><div class="price-label">Stop</div><div class="price-value">{fmt_number(idea["stop_loss"])}</div></div>
                <div class="price-cell"><div class="price-label">Target 1</div><div class="price-value">{fmt_number(idea["target_1"])}</div></div>
                <div class="price-cell"><div class="price-label">Target 2</div><div class="price-value">{fmt_number(idea["target_2"])}</div></div>
            </div>
            <ul class="reason-list">{reasons}</ul>
            <div class="small-note">{html.escape(str(idea["invalidation"]))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

report = load_local_report()

recommendations = report.get("recommendations", [])
quotes = report.get("quotes", [])
buy_count = sum(1 for item in recommendations if item.get("action") == "BUY WATCH")
wait_count = sum(1 for item in recommendations if item.get("action") == "WAIT")
avoid_count = sum(1 for item in recommendations if item.get("action") == "AVOID")
positive_count = sum(
    1
    for item in quotes
    if item.get("change_percent") is not None and not pd.isna(item.get("change_percent")) and item.get("change_percent") > 0
)

st.subheader(report["market_context"])
st.caption(f"As of {report['as_of']}")

summary_cols = st.columns(4)
with summary_cols[0]:
    metric_card("Watched stocks", str(len(quotes)), "Fast 20-symbol universe", "blue")
with summary_cols[1]:
    metric_card("Buy watch", str(buy_count), "Ideas needing broker confirmation", "green")
with summary_cols[2]:
    metric_card("Positive today", str(positive_count), "Green names in watchlist", "green")
with summary_cols[3]:
    metric_card("Risk flags", str(avoid_count), "Names to avoid or wait on", "red")

for note in report["notes"]:
    if "skipped" not in note.lower() and "could not be loaded" not in note.lower():
        st.info(note)

diagnostics = [
    note for note in report["notes"] if "skipped" in note.lower() or "could not be loaded" in note.lower()
]
if diagnostics:
    with st.expander("Diagnostics"):
        for note in diagnostics:
            st.write(note)

tab_recommendations, tab_all_stocks = st.tabs(["Recommendations", "All stocks"])

with tab_recommendations:
    if not recommendations:
        st.warning("No recommendations are available yet. Check that PSX Terminal is reachable and refresh.")
    else:
        rec_frame = pd.DataFrame(recommendations)
        action_filter = st.selectbox("Action", ["ALL", "BUY WATCH", "WAIT", "AVOID"], index=0)
        if action_filter != "ALL":
            rec_frame = rec_frame[rec_frame["action"] == action_filter]

        rec_display = rec_frame[
            [
                "symbol",
                "action",
                "score",
                "last_close",
                "entry_low",
                "entry_high",
                "stop_loss",
                "target_1",
                "target_2",
                "risk_reward",
                "confidence",
            ]
        ]
        st.dataframe(
            rec_display.style.map(color_action, subset=["action"]),
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("Top ranked detail")
    for idea in recommendations[:20]:
        render_idea_card(idea)

with tab_all_stocks:
    if not quotes:
        st.warning("No stock table is available yet. Check that PSX Terminal is reachable and refresh.")
    else:
        frame = pd.DataFrame(quotes)
        frame["quick_signal"] = frame.apply(
            lambda row: quick_signal(
                row.get("open"),
                row.get("high"),
                row.get("low"),
                row.get("close"),
                row.get("volume"),
                row.get("change_percent"),
            ),
            axis=1,
        )
        display_columns = [
            "symbol",
            "name",
            "quick_signal",
            "close",
            "change",
            "change_percent",
            "volume",
            "bid_price",
            "ask_price",
            "high",
            "low",
            "high52",
            "low52",
            "market_cap",
            "pe_ratio",
            "dividend_yield",
            "year_change",
            "listed_in",
            "non_compliant",
        ]
        visible_columns = [column for column in display_columns if column in frame.columns]
        styled_frame = frame[visible_columns].style
        if "change_percent" in visible_columns:
            styled_frame = styled_frame.map(color_change, subset=["change_percent"])
        if "quick_signal" in visible_columns:
            styled_frame = styled_frame.map(color_quick_signal, subset=["quick_signal"])

        st.dataframe(
            styled_frame,
            use_container_width=True,
            hide_index=True,
            column_config={
                "change_percent": st.column_config.NumberColumn("change %", format="%.2f%%"),
                "quick_signal": st.column_config.TextColumn("quick signal"),
            },
        )
