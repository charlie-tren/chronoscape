"""Chronoscape - interactive multi-country history timeline."""

import html as html_lib
import subprocess
import streamlit as st
from pathlib import Path

from data_parser import filter_events
from db import list_countries, load_country_data
from timeline_component import render_timeline
from map_component import render_map
from styles import inject_styles, get_era_color, get_era_short, set_era_config, CATEGORY_COLORS


def _get_version() -> str:
    """Derive version from git commit count (auto-increments on each push)."""
    try:
        count = subprocess.check_output(
            ["git", "rev-list", "--count", "HEAD"],
            stderr=subprocess.DEVNULL,
            cwd=Path(__file__).parent,
        ).decode().strip()
        return f"v2.{count}"
    except Exception:
        return "v2.0"


# --- Page config ---
st.set_page_config(
    page_title="Chronoscape",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_styles()

# --- Session state ---
if "selected_id" not in st.session_state:
    st.session_state.selected_id = None
if "country_name" not in st.session_state:
    st.session_state.country_name = ""


def select_event(eid: int):
    st.session_state.selected_id = eid


# --- Country Selection (chip-only, no free-text input until Phase 4 generation is live) ---
def _select_country(name: str):
    st.session_state.selected_id = None
    st.session_state.country_name = name


# Title + tagline on the left, hub back-link on the right. Label and behaviour
# match the "Other projects" nav link on the sibling sites (DCF Studio et al).
st.markdown(
    '<div style="display:flex;align-items:flex-start;justify-content:space-between;'
    'gap:16px;flex-wrap:wrap;margin:0 0 22px 0;">'
    '<div>'
    '<h1 style="margin:0;font-size:1.9rem;color:#f0f0f0;line-height:1.15;">Chronoscape</h1>'
    '<div style="color:#5a6a7a;font-size:0.85rem;margin-top:2px;">'
    'Interactive timelines of world history'
    '</div>'
    '</div>'
    '<a class="hub-link" href="https://charlie-tren.github.io/" '
    'target="_blank" rel="noopener noreferrer">'
    'Charlie Trenorden<span class="hub-arrow">↗</span>'
    '</a>'
    '</div>',
    unsafe_allow_html=True,
)

# Country picker - one chip per JSON file in countries/
_existing = list_countries()

if _existing:
    with st.container(key="country-picker"):
        # Small uppercase label sits above the chip row instead of inline next to it
        st.markdown(
            '<div style="color:#586473;font-size:0.7rem;letter-spacing:0.10em;'
            'text-transform:uppercase;margin-bottom:8px;">Select country</div>',
            unsafe_allow_html=True,
        )
        # Give each chip a wide-enough column so the label never wraps, with a
        # trailing spacer column to keep the chips left-packed.
        n = len(_existing)
        chip_cols = st.columns([2] * n + [max(2, 12 - 2 * n)])
        for i, c in enumerate(_existing):
            with chip_cols[i]:
                is_active = st.session_state.country_name.lower() == c["name_lower"]
                st.button(
                    c["name"],
                    key=f"chip_{c['name_lower']}",
                    on_click=_select_country,
                    args=(c["name"],),
                    type="primary" if is_active else "tertiary",
                )

country_name = st.session_state.country_name.strip()

# --- Load data for selected country ---
all_events = []
eras_config = []
country_config = None

if country_name:
    events, eras_cfg, country_cfg = load_country_data(country_name)
    if events is not None:
        all_events = events
        eras_config = eras_cfg
        country_config = country_cfg
        set_era_config(eras_config)
    else:
        # Stale session_state pointing at a country no longer on disk
        st.warning(f"No timeline for **{country_name}**. Pick a country from the chips above.")
        st.session_state.country_name = ""
else:
    # No country selected - show welcome (left-aligned to match the chip row above,
    # tight padding so it sits just under the chips rather than floating mid-viewport)
    st.markdown(
        '<div style="margin:40px 0 24px 0;max-width:540px;padding:30px 32px;'
        'background:linear-gradient(180deg,#141a26 0%,#121826 100%);'
        'border:1px solid #222b3b;border-radius:16px;'
        'box-shadow:0 8px 30px rgba(0,0,0,0.25);">'
        '<div style="font-size:2rem;margin-bottom:14px;line-height:1;">🏛️</div>'
        '<h2 style="color:#e7eaf1 !important;margin:0 0 8px 0;font-size:1.4rem;letter-spacing:-0.3px;">'
        'Explore history'
        '</h2>'
        '<p style="color:#8b95a7;font-size:0.92rem;margin:0;line-height:1.6;">'
        'Pick a country above to open its interactive timeline - eras, key events, '
        'and a map you can click through.'
        '</p></div>',
        unsafe_allow_html=True,
    )

# --- Only render timeline UI if we have data ---
if all_events and eras_config:
    # Subtitle
    date_range = ""
    if eras_config:
        first_label = eras_config[0].get("date_label", "")
        last_era = eras_config[-1]
        date_range = f"{first_label} - present"

    display_name = country_config["name"] if country_config else country_name
    st.markdown(
        f'<span style="color:#5a6a7a;font-size:0.85rem;">'
        f'{display_name} &nbsp;|&nbsp; {date_range} &nbsp;|&nbsp; {len(all_events)} events'
        f'</span>',
        unsafe_allow_html=True,
    )

    # --- Filters ---
    eras_list = ["All"] + [ec["name"] for ec in eras_config]
    all_categories = sorted(list(set(c for e in all_events for c in e.categories)))

    col_search, col_era, col_cats, col_key = st.columns([3, 2, 3, 1.5])

    with col_search:
        search_query = st.text_input(
            "Search events",
            placeholder="Search by keyword...",
            label_visibility="collapsed",
        )

    with col_era:
        selected_era = st.selectbox("Era", eras_list, label_visibility="collapsed")

    with col_cats:
        selected_cats = st.multiselect(
            "Categories",
            all_categories,
            placeholder="Filter by category...",
            label_visibility="collapsed",
        )

    with col_key:
        key_only = st.toggle("Key events", value=False)

    # Apply filters
    filtered = filter_events(all_events, search_query, selected_era, selected_cats)
    if key_only:
        filtered = [e for e in filtered if e.is_major]

    # --- Timeline ---
    timeline_clicked = render_timeline(filtered, st.session_state.selected_id, height=160, eras_config=eras_config)
    if timeline_clicked is not None and timeline_clicked != st.session_state.selected_id:
        st.session_state.selected_id = timeline_clicked
        st.rerun()

    # --- Colour Key ---
    legend_items = ""
    for ec in eras_config:
        short = html_lib.escape(ec.get("short_name", ec["name"]))
        color = ec.get("color", "#666")
        legend_items += (
            f'<span style="display:inline-flex;align-items:center;gap:5px;margin-right:14px;">'
            f'<span style="width:10px;height:10px;border-radius:50%;background:{color};display:inline-block;"></span>'
            f'<span style="color:#8899aa;font-size:0.75rem;">{short}</span>'
            f'</span>'
        )
    legend_items += (
        '<span style="display:inline-flex;align-items:center;gap:5px;margin-right:14px;">'
        '<span style="width:12px;height:12px;border-radius:50%;background:#4fc3f7;display:inline-block;"></span>'
        '<span style="color:#8899aa;font-size:0.75rem;">Key event</span>'
        '</span>'
    )

    st.markdown(
        f'<div style="display:flex;flex-wrap:wrap;align-items:center;padding:4px 0 8px;gap:2px;">{legend_items}</div>',
        unsafe_allow_html=True,
    )

    # --- Main content: Map + Event List + Detail Panel ---
    col_map, col_list, col_detail = st.columns([3, 3, 4])

    # --- Map ---
    with col_map:
        clicked_event_id = render_map(filtered, st.session_state.selected_id, height=500, country_config=country_config)
        if clicked_event_id is not None and clicked_event_id != st.session_state.selected_id:
            st.session_state.selected_id = clicked_event_id
            st.rerun()

    # --- Event List ---
    with col_list:
        st.markdown(
            f'<p style="color:#5a6a7a;font-size:0.8rem;margin:0 0 4px;">'
            f'{len(filtered)} event{"s" if len(filtered) != 1 else ""}</p>',
            unsafe_allow_html=True,
        )

        # Colour each row's left edge with its era colour. Streamlit tags every
        # keyed widget's wrapper with a `st-key-<key>` class, so each event
        # button can be targeted individually.
        stripe_css = "".join(
            f".st-key-evt_{evt.id} button{{border-left-color:{get_era_color(evt.era)} !important;}}"
            for evt in filtered
        )
        if stripe_css:
            st.markdown(f"<style>{stripe_css}</style>", unsafe_allow_html=True)

        list_container = st.container(height=470, key="eventlist")
        with list_container:
            for evt in filtered:
                is_selected = st.session_state.selected_id == evt.id
                # The whole row is the button - clicking anywhere selects the
                # event (no separate "select" button). A star marks key events.
                star = "★ " if evt.is_major else ""
                label = f"{star}{evt.display_date}\n\n**{evt.title}**"
                st.button(
                    label,
                    key=f"evt_{evt.id}",
                    on_click=select_event,
                    args=(evt.id,),
                    use_container_width=True,
                    type="primary" if is_selected else "secondary",
                )

    # --- Detail Panel ---
    with col_detail:
        if st.session_state.selected_id is not None:
            selected_evt = None
            for e in all_events:
                if e.id == st.session_state.selected_id:
                    selected_evt = e
                    break

            if selected_evt:
                era_color = get_era_color(selected_evt.era)
                era_short = html_lib.escape(get_era_short(selected_evt.era))
                safe_title = html_lib.escape(selected_evt.title)
                safe_desc = html_lib.escape(selected_evt.description)
                safe_date = html_lib.escape(selected_evt.display_date)

                major_html = '<span class="major-badge">PIVOTAL EVENT</span>' if selected_evt.is_major else ""

                cat_html = ""
                for c in selected_evt.categories:
                    c_color = CATEGORY_COLORS.get(c, "#666")
                    cat_html += f'<span class="cat-tag" style="background:{c_color}30;color:{c_color};">{html_lib.escape(c)}</span>'

                st.markdown(
                    f'<div class="detail-panel">'
                    f'<div class="detail-date">{safe_date}</div>'
                    f'<h2>{safe_title}</h2>'
                    f'<div class="tags-row">'
                    f'<span class="era-tag" style="background:{era_color}35;color:{era_color};">{era_short}</span>'
                    f'{cat_html}'
                    f'{major_html}'
                    f'</div>'
                    f'<div class="detail-body">{safe_desc}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                if st.button("Clear selection", type="tertiary"):
                    st.session_state.selected_id = None
                    st.rerun()
            else:
                st.session_state.selected_id = None
                st.rerun()
        else:
            st.markdown(
                '<div class="detail-panel" style="text-align:center;padding:80px 24px;">'
                '<div style="font-size:2.5rem;margin-bottom:12px;">🏛️</div>'
                '<h2 style="color:#5a6a7a !important;">Select an event</h2>'
                '<p style="color:#4a5a6a;font-size:0.9rem;">'
                'Click an event in the list, a dot on the timeline, or a marker on the map.'
                '</p></div>',
                unsafe_allow_html=True,
            )

# --- Version footer ---
st.markdown(
    f'<div style="color:#3a4a5a;font-size:0.65rem;'
    f'font-family:monospace;opacity:0.7;padding:24px 0 8px 4px;">{_get_version()}</div>',
    unsafe_allow_html=True,
)
