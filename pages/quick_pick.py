import streamlit as st
import pandas as pd
import random
import io
from game_config import GAMES
from analyzer import get_filtered_pools
from lotto_utils import get_data, build_heatmap

st.title("🍀 Quick Pick Generator")

# --- Game selection (shared from Welcome page) ---
if "selected_game" not in st.session_state:
    st.info("ℹ️ Tip: visit the **Welcome** page first to set your game — using default for now.")
    st.session_state.selected_game = list(GAMES.keys())[0]

selected_game = st.session_state.selected_game
game = GAMES[selected_game]

st.write("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

st.markdown(f"**Game:** {selected_game}  ·  **Pick {game['pick_size']} numbers from 1–{game['max_ball']}**")

st.write("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# ------------------------------------------------------------------ #
#  Hot / Cold Pool (optional)
# ------------------------------------------------------------------ #
use_hot_cold = st.checkbox("🔥 Use Hot/Cold pool instead of full pool", value=False)

if st.session_state.get("qp_prev_hot_cold") != use_hot_cold:
    st.session_state.df_quick_pick = None
st.session_state.qp_prev_hot_cold = use_hot_cold

if use_hot_cold:
    df = get_data(game)

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
            key="qp_draw_window",
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
            o_type = st.radio("Odd Type", ["Hot", "Cold"], horizontal=True, key="qp_o_type")
            o_size = st.slider("Size of Odd Pool", 5, 20, 10, key="qp_o_size")
        with col2:
            e_type = st.radio("Even Type", ["Hot", "Cold"], horizontal=True, key="qp_e_type")
            e_size = st.slider("Size of Even Pool", 5, 20, 10, key="qp_e_size")

        odds_pool, evens_pool = get_filtered_pools(df, game, o_size, e_size, o_type, e_type, last_n)
        pool = sorted(odds_pool + evens_pool)

        st.markdown(f"**Pool:** `{pool}`")
        st.write("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    else:
        st.error("⚠️ Could not load data for this game.")
        pool = list(range(1, game["max_ball"] + 1))
else:
    pool = list(range(1, game["max_ball"] + 1))

# ------------------------------------------------------------------ #
#  Generate
# ------------------------------------------------------------------ #
st.write("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

num_combinations = st.number_input(
    "How many combinations would you like to generate?",
    min_value=1,
    max_value=1000,
    value=5,
    step=1,
)

ensure_unique = st.checkbox(
    "Ensure all generated combinations are unique (no duplicates)",
    value=True,
)

pick_size = game["pick_size"]

if st.button("🎲 Generate Quick Picks"):
    if len(pool) < pick_size:
        st.error(f"⚠️ Pool has only {len(pool)} numbers — need at least {pick_size} to generate a combination.")
    else:
        generated = set() if ensure_unique else []
        combos = []

        max_attempts = num_combinations * 50
        attempts = 0

        while len(combos) < num_combinations and attempts < max_attempts:
            combo = tuple(sorted(random.sample(pool, pick_size)))
            attempts += 1
            if ensure_unique:
                if combo in generated:
                    continue
                generated.add(combo)
            combos.append(combo)

        if len(combos) < num_combinations:
            st.warning(
                f"⚠️ Could only generate {len(combos)} unique combinations "
                f"(requested {num_combinations}). The pool may be too small for that many unique sets."
            )

        df_quick = pd.DataFrame(combos, columns=[f"N{i}" for i in range(1, pick_size + 1)])
        df_quick.insert(0, "Combination #", range(1, len(df_quick) + 1))
        st.session_state.df_quick_pick = df_quick

# ------------------------------------------------------------------ #
#  Display + export
# ------------------------------------------------------------------ #
if "df_quick_pick" in st.session_state and st.session_state.df_quick_pick is not None:
    df_quick = st.session_state.df_quick_pick

    st.markdown("### 🎟️ Your Quick Pick Combinations")
    st.dataframe(df_quick, use_container_width=True, hide_index=True)

    csv = df_quick.to_csv(index=False).encode("utf-8")

    xlsx_buffer = io.BytesIO()
    df_quick.to_excel(xlsx_buffer, index=False, engine="openpyxl")
    xlsx_buffer.seek(0)

    json_data = df_quick.to_json(orient="records", indent=2).encode("utf-8")

    dl_col1, dl_col2, dl_col3 = st.columns(3)
    with dl_col1:
        st.download_button(
            "📥 Download as CSV",
            data=csv,
            file_name="quick_pick.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with dl_col2:
        st.download_button(
            "📥 Download as XLSX",
            data=xlsx_buffer,
            file_name="quick_pick.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with dl_col3:
        st.download_button(
            "📥 Download as JSON",
            data=json_data,
            file_name="quick_pick.json",
            mime="application/json",
            use_container_width=True,
        )
