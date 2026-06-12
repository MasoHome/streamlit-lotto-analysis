import streamlit as st

from game_config import GAMES
from analyzer import get_filtered_pools
from lotto_utils import get_data, build_heatmap
from shared_ui import render_strategy_workflow

st.title("🔥 Hot & Cold Single Numbers")

st.markdown(
    "This strategy builds your number pool based on how often **individual numbers** "
    "have appeared in past draws — pick the hottest (most frequent) or coldest "
    "(least frequent) numbers, separately for odds and evens."
)

# --- Game selection (shared from Welcome page) ---
if "selected_game" not in st.session_state:
    st.info("ℹ️ Tip: visit the **Welcome** page first to set your game — using default for now.")
    st.session_state.selected_game = list(GAMES.keys())[0]

selected_game = st.session_state.selected_game
game = GAMES[selected_game]
if game.get("bonus_ball"):
    st.caption(f"Game: **{selected_game}**  ·  Pick {game['pick_size']} from 1–{game['max_ball']}  ·  + 1 Powerball from 1–{game['bonus_ball']}")
else:
    st.caption(f"Game: **{selected_game}**  ·  Pick {game['pick_size']} from 1–{game['max_ball']}")

df = get_data(game)

if df is not None:
    # ------------------------------------------------------------------ #
    #  Draw Window Selector
    # ------------------------------------------------------------------ #
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
        key="singles_draw_window",
    )
    last_n = draw_options[draw_labels.index(selected_label)]

    # ------------------------------------------------------------------ #
    #  Heatmap
    # ------------------------------------------------------------------ #
    with st.expander("🔥 Ball Frequency Ranking", expanded=False):
        fig_heatmap = build_heatmap(df, game, last_n)
        st.plotly_chart(fig_heatmap, use_container_width=True)
        st.caption(
            "🔴 Crimson = hottest  ·  🟠 Orange = warm  ·  🟡 Amber = neutral  ·  🔵 Blue = coldest  ·  "
            "Ordered hot → cold left to right, top to bottom  ·  Hover a square for full details."
        )

    st.write("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

    # ------------------------------------------------------------------ #
    #  Strategy Filters (Pool Selection)
    # ------------------------------------------------------------------ #
    st.subheader("🛡️ Strategy Filters")
    col1, col2 = st.columns(2)
    with col1:
        o_type = st.radio("Odd Type", ["Hot", "Cold"], horizontal=True, key="singles_o_type")
        o_size = st.slider("Size of Odd Pool", 5, 20, 10, key="singles_o_size")
    with col2:
        e_type = st.radio("Even Type", ["Hot", "Cold"], horizontal=True, key="singles_e_type")
        e_size = st.slider("Size of Even Pool", 5, 20, 10, key="singles_e_size")

    odds_pool, evens_pool = get_filtered_pools(df, game, o_size, e_size, o_type, e_type, last_n)

    st.write("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

    # ------------------------------------------------------------------ #
    #  Shared workflow (ratio, reduction filters, generate, export, etc.)
    # ------------------------------------------------------------------ #
    render_strategy_workflow(df, game, odds_pool, evens_pool, page_key="singles")

else:
    st.error("⚠️ Could not load data for this game. Please check your data source.")
