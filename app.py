import html

import requests
import pandas as pd
import streamlit as st

from psx_agent.report import build_morning_report


st.set_page_config(page_title="PSX Agent by Arfa", layout="wide")

st.markdown(
    """
    <style>
    :root {
        --ink: #17212b;
        --muted: #667085;
        --panel: #ffffff;
        --line: #d9dee8;
        --green: #0f8f62;
        --green-soft: #e8f6f0;
        --amber: #b7791f;
        --amber-soft: #fff7e6;
        --red: #c2410c;
        --red-soft: #fff0e8;
        --blue: #2563eb;
        --blue-soft: #eef4ff;
    }
    .stApp {
        background: linear-gradient(180deg, #f7f9fc 0%, #eef3f8 45%, #f8fafc 100%);
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
        color: var(--ink);
    }
    [data-testid="stSidebar"] {
        background: #111827;
    }
    [data-testid="stSidebar"] * {
        color: #f9fafb !important;
    }
    .hero {
        background: linear-gradient(135deg, #102033 0%, #1d4f66 52%, #366b47 100%);
        border: 1px solid rgba(255,255,255,.16);
        border-radius: 14px;
        padding: 26px 28px;
        margin-bottom: 18px;
        color: white;
        box-shadow: 0 18px 50px rgba(16, 32, 51, .20);
    }
    .hero h1 {
        margin: 0 0 6px 0;
        font-size: 34px;
        line-height: 1.12;
        letter-spacing: 0;
        color: #ffffff !important;
    }
    .hero p {
        margin: 0;
        color: rgba(255,255,255,.86) !important;
        font-size: 16px;
    }
    .metric-card {
        background: var(--panel);
        border: 1px solid var(--line);
        border-left: 6px solid var(--blue);
        border-radius: 12px;
        padding: 16px 18px;
        min-height: 104px;
        box-shadow: 0 10px 28px rgba(17, 24, 39, .06);
    }
    .metric-card.green { border-left-color: var(--green); background: linear-gradient(180deg, #ffffff 0%, #f3fbf7 100%); }
    .metric-card.amber { border-left-color: var(--amber); background: linear-gradient(180deg, #ffffff 0%, #fffaf0 100%); }
    .metric-card.red { border-left-color: var(--red); background: linear-gradient(180deg, #ffffff 0%, #fff5f0 100%); }
    .metric-card.blue { border-left-color: var(--blue); background: linear-gradient(180deg, #ffffff 0%, #f2f7ff 100%); }
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
        background: var(--panel);
        border: 1px solid var(--line);
        border-left: 7px solid var(--blue);
        border-radius: 12px;
        padding: 18px;
        margin: 12px 0 14px 0;
        box-shadow: 0 10px 26px rgba(17, 24, 39, .06);
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
    .badge.buy { background: var(--green-soft); color: var(--green); border-color: #b8e3d2; }
    .badge.wait { background: var(--amber-soft); color: var(--amber); border-color: #f4d9a5; }
    .badge.avoid { background: var(--red-soft); color: var(--red); border-color: #ffc9b7; }
    .price-grid {
        display: grid;
        grid-template-columns: repeat(5, minmax(104px, 1fr));
        gap: 10px;
        margin: 12px 0;
    }
    .price-cell {
        background: #f8fafc;
        border: 1px solid #e5e7eb;
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
        color: #344054;
    }
    .small-note {
        color: var(--muted);
        font-size: 13px;
        margin-top: 8px;
    }
    [data-testid="stAlert"] {
        background: #e9f4ff !important;
        border: 1px solid #b7d8f7 !important;
        color: #1f344a !important;
        border-radius: 10px !important;
    }
    [data-testid="stAlert"] * {
        color: #1f344a !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        border-bottom: 1px solid #d9dee8;
    }
    .stTabs [data-baseweb="tab"] {
        color: #344054 !important;
        background: transparent !important;
        font-weight: 650;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #0f8f62 !important;
        border-bottom-color: #0f8f62 !important;
    }
    [data-testid="stSelectbox"] label,
    [data-testid="stSelectbox"] div {
        color: #17212b !important;
    }
    [data-testid="stDataFrame"] {
        background: #ffffff;
        border-radius: 10px;
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

source = st.sidebar.radio("Data source", ["Local engine", "FastAPI backend"])
api_url = st.sidebar.text_input("Backend URL", "http://localhost:8000/report")
refresh = st.sidebar.button("Refresh now")

if refresh:
    st.cache_data.clear()


@st.cache_data(ttl=15)
def load_backend_report(url: str) -> dict:
    response = requests.get(url, timeout=300)
    response.raise_for_status()
    return response.json()


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
        return "#0f8f62"
    if css_class == "avoid":
        return "#c2410c"
    return "#b7791f"


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
        return "background-color: #e8f6f0; color: #0f8f62; font-weight: 700;"
    if value == "WAIT":
        return "background-color: #fff7e6; color: #b7791f; font-weight: 700;"
    if value == "AVOID":
        return "background-color: #fff0e8; color: #c2410c; font-weight: 700;"
    return ""


def color_change(value) -> str:
    if pd.isna(value):
        return ""
    if value > 0:
        return "background-color: #e8f6f0; color: #0f8f62; font-weight: 700;"
    if value < 0:
        return "background-color: #fff0e8; color: #c2410c; font-weight: 700;"
    return "background-color: #fff7e6; color: #b7791f; font-weight: 700;"


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

if source == "FastAPI backend":
    report = load_backend_report(api_url)
else:
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
        st.warning("No recommendations are available yet. Check that the data source is reachable and refresh.")
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
