"""Dark theme CSS for the History Timeline Streamlit app."""

import streamlit as st

# 15-colour palette for dynamically assigning era colours (dark-theme friendly)
ERA_PALETTE = [
    "#5a8a9a", "#6a8a5a", "#c49a2a", "#b06040", "#7a5aaa",
    "#2aaa7a", "#c04040", "#707070", "#3a7abb", "#40a870",
    "#aa5a8a", "#8a6a3a", "#5a5aaa", "#aa8a2a", "#3a8a8a",
]

CATEGORY_COLORS = {
    "Military": "#e05555",
    "Political": "#5588dd",
    "Economic": "#44bb77",
    "Indigenous": "#cc8844",
    "Aboriginal": "#cc8844",  # legacy alias
    "Foreign Relations": "#9966cc",
    "Cultural": "#dd6699",
    "Social": "#55aacc",
    "Scientific": "#88bb55",
    "Religious": "#cc7744",
}

# --- Runtime era colour/name lookups (populated from DB data) ---

_era_color_map: dict[str, str] = {}
_era_short_map: dict[str, str] = {}


def set_era_config(eras_config: list[dict]):
    """Load era colours and short names from DB-provided eras config."""
    global _era_color_map, _era_short_map
    _era_color_map = {e["name"]: e.get("color", "#666666") for e in eras_config}
    _era_short_map = {e["name"]: e.get("short_name", e["name"]) for e in eras_config}


def assign_era_colors(n_eras: int) -> list[str]:
    """Return a list of n distinct colours from the palette."""
    return [ERA_PALETTE[i % len(ERA_PALETTE)] for i in range(n_eras)]


def get_era_color(era_name: str) -> str:
    """Look up era colour from runtime config."""
    if _era_color_map:
        if era_name in _era_color_map:
            return _era_color_map[era_name]
        # Fuzzy fallback
        era_lower = era_name.lower()
        for key, color in _era_color_map.items():
            if key.lower() in era_lower or era_lower in key.lower():
                return color
    return "#666666"


def get_era_short(era_name: str) -> str:
    """Look up short era name from runtime config."""
    if _era_short_map:
        if era_name in _era_short_map:
            return _era_short_map[era_name]
        era_lower = era_name.lower()
        for key, short in _era_short_map.items():
            if key.lower() in era_lower or era_lower in key.lower():
                return short
    return era_name


# Design tokens. Cyan accent is shared with the timeline + map JS, so keep it in
# sync if it ever changes there.
DARK_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --bg: #0c0f16;
        --surface: #141a26;
        --surface-2: #121826;
        --border: #222b3b;
        --border-strong: #2d384c;
        --text: #e7eaf1;
        --muted: #8b95a7;
        --faint: #586473;
        --accent: #4fc3f7;
        --accent-soft: rgba(79, 195, 247, 0.10);
        --accent-line: rgba(79, 195, 247, 0.30);
    }

    /* Base */
    .stApp {
        background:
            radial-gradient(1200px 600px at 15% -10%, rgba(79,195,247,0.06), transparent 60%),
            radial-gradient(1000px 500px at 100% 0%, rgba(122,90,170,0.05), transparent 55%),
            var(--bg);
        color: var(--text);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    .stApp, .stApp p, .stApp span, .stApp div, .stApp label {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    /* Tighten the default top padding so the header sits higher */
    .block-container { padding-top: 2.4rem !important; max-width: 1500px; }

    section[data-testid="stSidebar"] { background-color: #0f131c; }

    /* Headers */
    h1, h2, h3 { color: var(--text) !important; font-weight: 700 !important; }
    h1 { font-size: 2rem !important; letter-spacing: -0.8px; }

    /* ---- Filter inputs ---- */
    .stTextInput > div > div > input {
        background: var(--surface) !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        font-size: 0.88rem !important;
        transition: border-color 0.15s, box-shadow 0.15s;
    }
    .stTextInput > div > div > input::placeholder { color: var(--faint) !important; }
    .stTextInput > div > div > input:focus {
        border-color: var(--accent-line) !important;
        box-shadow: 0 0 0 3px var(--accent-soft) !important;
    }
    .stSelectbox div[data-baseweb="select"] > div,
    .stMultiSelect div[data-baseweb="select"] > div {
        background: var(--surface) !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        min-height: 40px;
    }
    div[data-baseweb="popover"] { border-radius: 10px !important; }
    /* Multiselect chosen tags */
    .stMultiSelect span[data-baseweb="tag"] {
        background: var(--accent-soft) !important;
        color: var(--accent) !important;
        border-radius: 6px !important;
    }

    /* Toggle accent */
    .stCheckbox [data-baseweb="checkbox"] [aria-checked="true"] { background: var(--accent) !important; }

    /* ---- Country picker chips (scoped) ---- */
    .st-key-country-picker .stButton button {
        border-radius: 999px !important;
        padding: 5px 18px !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        min-height: 0 !important;
        height: auto !important;
        line-height: 1.5 !important;
        white-space: nowrap !important;
        box-shadow: none !important;
        transition: background 0.15s, border-color 0.15s, color 0.15s !important;
    }
    .st-key-country-picker .stButton button[kind="tertiary"] {
        background: rgba(255,255,255,0.02) !important;
        color: #c2cad6 !important;
        border: 1px solid var(--border-strong) !important;
    }
    .st-key-country-picker .stButton button[kind="tertiary"]:hover {
        border-color: var(--accent) !important;
        color: #fff !important;
        background: var(--accent-soft) !important;
    }
    .st-key-country-picker .stButton button[kind="primary"] {
        background: var(--accent) !important;
        color: #08131a !important;
        border: 1px solid var(--accent) !important;
        font-weight: 600 !important;
    }
    .st-key-country-picker .stButton button[kind="primary"]:hover { background: #6dcef0 !important; }

    /* ---- Event list: each row is a clickable card button (scoped) ---- */
    .st-key-eventlist .stButton { margin-bottom: 7px; }
    .st-key-eventlist .stButton button {
        background: var(--surface-2) !important;
        border: 1px solid var(--border) !important;
        border-left: 3px solid var(--border) !important;
        border-radius: 10px !important;
        padding: 10px 14px !important;
        min-height: 0 !important;
        height: auto !important;
        justify-content: flex-start !important;
        text-align: left !important;
        box-shadow: none !important;
        transition: border-color 0.15s, background 0.15s, transform 0.05s !important;
    }
    .st-key-eventlist .stButton button div[data-testid="stMarkdownContainer"] {
        text-align: left !important;
        width: 100% !important;
    }
    .st-key-eventlist .stButton button p {
        text-align: left !important;
        line-height: 1.3 !important;
        white-space: normal !important;
        margin: 0 !important;
    }
    /* date line (first paragraph of the label) */
    .st-key-eventlist .stButton button p:first-child {
        font-size: 0.72rem !important;
        font-weight: 500 !important;
        color: var(--muted) !important;
        margin-bottom: 3px !important;
        letter-spacing: 0.2px;
    }
    /* title line (second paragraph) */
    .st-key-eventlist .stButton button p:last-child {
        font-size: 0.86rem !important;
        font-weight: 600 !important;
        color: var(--text) !important;
    }
    .st-key-eventlist .stButton button:hover {
        border-color: var(--accent-line) !important;
        background: #161d2c !important;
    }
    .st-key-eventlist .stButton button:active { transform: translateY(1px); }
    /* Selected row */
    .st-key-eventlist .stButton button[kind="primary"] {
        background: #14202f !important;
        border-color: var(--accent) !important;
    }
    .st-key-eventlist .stButton button[kind="primary"] p { color: #fff !important; }

    /* Scroll container for the list */
    .st-key-eventlist [data-testid="stVerticalBlockBorderWrapper"] { border: none; }

    /* ---- Tags / badges ---- */
    .tags-row { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 6px; align-items: center; }
    .era-tag {
        display: inline-block; font-size: 0.65rem; padding: 2px 9px;
        border-radius: 999px; color: #fff; white-space: nowrap; line-height: 1.5;
        font-weight: 500;
    }
    .major-badge {
        display: inline-block; font-size: 0.6rem; padding: 2px 8px; border-radius: 999px;
        background: var(--accent); color: #08131a; font-weight: 700; white-space: nowrap;
        line-height: 1.5; letter-spacing: 0.4px; vertical-align: middle;
    }
    .cat-tag {
        display: inline-block; font-size: 0.6rem; padding: 2px 8px; border-radius: 999px;
        white-space: nowrap; line-height: 1.5; font-weight: 500;
    }

    /* ---- Detail panel ---- */
    .detail-panel {
        background: linear-gradient(180deg, var(--surface) 0%, var(--surface-2) 100%);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 22px 26px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.25);
    }
    .detail-panel h2 { margin-top: 0; font-size: 1.35rem !important; line-height: 1.3; letter-spacing: -0.3px; }
    .detail-panel .detail-date { font-size: 0.95rem; color: var(--accent); font-weight: 500; margin-bottom: 6px; }
    .detail-panel .detail-body { font-size: 0.95rem; line-height: 1.7; color: #cdd4e0; margin-top: 18px; }
    .detail-panel .tags-row { margin-top: 12px; gap: 6px; }
    .detail-panel .era-tag { font-size: 0.7rem; padding: 3px 11px; }
    .detail-panel .cat-tag { font-size: 0.65rem; padding: 3px 9px; }
    .detail-panel .major-badge { font-size: 0.65rem; padding: 3px 10px; }

    /* ---- Misc buttons (Clear / Retry) ---- */
    .stButton button[kind="tertiary"] { color: var(--muted) !important; }
    .stButton button[kind="tertiary"]:hover { color: var(--accent) !important; }

    /* Hide Streamlit chrome */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}
    [data-testid="stStatusWidget"] {display: none !important;}

    /* Scrollbars */
    ::-webkit-scrollbar { width: 7px; height: 7px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #2a3344; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #3a4658; }
</style>
"""


def inject_styles():
    """Inject the dark theme CSS into the Streamlit app."""
    st.markdown(DARK_CSS, unsafe_allow_html=True)
