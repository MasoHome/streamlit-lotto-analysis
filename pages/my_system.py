import math
import streamlit as st
from game_config import GAMES
from analyzer import get_filtered_pools
from lotto_utils import get_data, build_heatmap
from shared_ui import render_strategy_workflow

st.title("🎯 My System")
st.markdown(
    "Select your own numbers manually or pre-fill from Hot/Cold analysis, then generate "
    "every combination of your chosen size — e.g. 6-of-8, 6-of-10, 7-of-12."
)

# --- Game selection ---
if "selected_game" not in st.session_state:
    st.session_state.selected_game = list(GAMES.keys())[0]

selected_game = st.session_state.selected_game
game = GAMES[selected_game]

if game.get("bonus_ball"):
    st.caption(
        f"Game: **{selected_game}**  ·  Pick {game['pick_size']} from 1–{game['max_ball']}"
        f"  ·  + 1 Powerball from 1–{game['bonus_ball']}"
    )
else:
    st.caption(f"Game: **{selected_game}**  ·  Pick {game['pick_size']} from 1–{game['max_ball']}")

st.write("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

df = get_data(game)

# ------------------------------------------------------------------ #
#  CSS — square ball buttons
# ------------------------------------------------------------------ #
st.markdown("""
<style>
div[data-testid="stHorizontalBlock"] {
    gap: 2px !important;
}
div[data-testid="stHorizontalBlock"] div[data-testid="column"] {
    padding: 0 !important;
    min-width: 0 !important;
    flex: 0 0 auto !important;
}
/* Scope size constraints only to regular buttons inside the grid rows */
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button {
    width: 44px !important;
    height: 44px !important;
    min-width: 44px !important;
    max-width: 44px !important;
    padding: 0 !important;
    margin: 0 !important;
    border-radius: 8px !important;
    font-weight: bold !important;
    font-size: 14px !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-sizing: border-box !important;
}
/* Green for selected balls */
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button[data-testid="baseButton-primary"],
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button[kind="primary"] {
    background-color: #2e7d32 !important;
    border-color: #1b5e20 !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------ #
#  Selected numbers state
# ------------------------------------------------------------------ #
if "mysys_selected" not in st.session_state:
    st.session_state.mysys_selected = set()
selected_set = set(st.session_state.mysys_selected)

# ------------------------------------------------------------------ #
#  Hot / Cold pre-fill (optional)
# ------------------------------------------------------------------ #
mode = st.radio(
    "How would you like to select your numbers?",
    ["Manual selection", "Pre-fill from Hot/Cold"],
    horizontal=True,
    key="mysys_mode",
)

if mode == "Pre-fill from Hot/Cold":
    if df is not None:
        total_draws = len(df)
        draw_options = [50, 100, 200, 500, total_draws]
        draw_options = sorted(set(min(o, total_draws) for o in draw_options))
        draw_labels = [f"Last {n} draws" if n < total_draws else f"All {n} draws" for n in draw_options]

        st.markdown("### 📅 Analysis Draw Window")
        st.caption("Controls both the frequency heatmap and the Hot/Cold number pools below.")
        selected_label = st.select_slider(
            "Draw window:",
            options=draw_labels,
            value=draw_labels[min(1, len(draw_labels) - 1)],
            label_visibility="collapsed",
            key="mysys_draw_window",
        )
        last_n = draw_options[draw_labels.index(selected_label)]

        with st.expander("🔥 Ball Frequency Ranking", expanded=False):
            fig_heatmap = build_heatmap(df, game, last_n)
            st.plotly_chart(fig_heatmap, use_container_width=True)
            st.caption(
                "🔴 Crimson = hottest  ·  🟠 Orange = warm  ·  🟡 Amber = neutral  ·  🔵 Blue = coldest  ·  "
                "Ordered hot → cold left to right, top to bottom  ·  Hover a square for full details."
            )

        st.write("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

        st.markdown("### 🛡️ Pool Selection")
        col1, col2 = st.columns(2)
        with col1:
            o_type = st.radio("Odd Type", ["Hot", "Cold"], horizontal=True, key="mysys_o_type")
            o_size = st.slider("Size of Odd Pool", 1, 20, 5, key="mysys_o_size")
        with col2:
            e_type = st.radio("Even Type", ["Hot", "Cold"], horizontal=True, key="mysys_e_type")
            e_size = st.slider("Size of Even Pool", 1, 20, 5, key="mysys_e_size")

        hc_odds, hc_evens = get_filtered_pools(df, game, o_size, e_size, o_type, e_type, last_n)
        prefill_pool = sorted(hc_odds + hc_evens)

        st.markdown(f"**Pool Odds:** `{hc_odds}`  &nbsp;&nbsp;  **Pool Evens:** `{hc_evens}`", unsafe_allow_html=True)
        st.write("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

        if st.button("⬇️ Pre-fill my numbers from this pool"):
            st.session_state.mysys_selected = set(prefill_pool)
            selected_set = set(prefill_pool)
            st.rerun()
    else:
        st.error("⚠️ Could not load data for this game.")

# ------------------------------------------------------------------ #
#  Number grid
# ------------------------------------------------------------------ #
st.write("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
st.markdown("### 🔢 Select Your Numbers")
st.markdown(
    f"Click to select/deselect  ·  "
    f"<span style='color:#1976d2'>Need at least <b>{game['pick_size']}</b> numbers</span>  ·  "
    f"<span style='color:#2e7d32'><b>Green = selected</b></span>",
    unsafe_allow_html=True,
)

per_row = 9
clicked_num = None

for row_start in range(0, game["max_ball"], per_row):
    row_nums = list(range(row_start + 1, min(row_start + per_row + 1, game["max_ball"] + 1)))
    cols = st.columns(per_row)
    for i, num in enumerate(row_nums):
        is_selected = num in selected_set
        with cols[i]:
            if st.button(
                str(num),
                key=f"ball_{num}",
                type="primary" if is_selected else "secondary",
            ):
                clicked_num = num

if clicked_num is not None:
    if clicked_num in selected_set:
        selected_set.discard(clicked_num)
    else:
        selected_set.add(clicked_num)
    st.session_state.mysys_selected = selected_set
    st.rerun()

# Clear all button
if selected_set:
    if st.button("Clear"):
        st.session_state.mysys_selected = set()
        st.rerun()

# ------------------------------------------------------------------ #
#  Pool breakdown + combination count + workflow
# ------------------------------------------------------------------ #
st.write("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

selected_numbers = sorted(selected_set)

if len(selected_numbers) >= game["pick_size"]:
    odds_pool = sorted(n for n in selected_numbers if n % 2 != 0)
    evens_pool = sorted(n for n in selected_numbers if n % 2 == 0)
    total_combos = math.comb(len(selected_numbers), game["pick_size"])
    st.info(
        f"**{len(selected_numbers)} numbers selected** → "
        f"**{total_combos:,} combinations** ({game['pick_size']}-of-{len(selected_numbers)}) before any filters."
    )

    st.write("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    if df is not None:
        render_strategy_workflow(df, game, odds_pool, evens_pool, page_key="mysystem",
                                 show_pool_breakdown=False)
    else:
        st.error("⚠️ Could not load historical data for this game.")
