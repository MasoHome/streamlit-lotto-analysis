import streamlit as st
from game_config import GAMES

st.title("🎯 Universal Lotto Engine")
st.markdown("### Welcome!")

st.markdown(
    """
This tool helps you explore different number-selection **strategies** for Australian lotto
games, generate filtered systems of combinations, and check how those systems would have
performed against historical draws.

Each strategy page builds a pool of numbers using a different approach (e.g. hottest/coldest
numbers, random quick picks), then lets you apply the **same set of reduction filters**
(consecutive numbers, last-digit variety, sum range) to narrow your system down before
exporting it.
"""
)

st.write("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# --- Game selection (stored in session state for all other pages) ---
st.markdown("### 🎲 Select Your Lottery Game")
st.caption("This selection will be remembered as you move between pages.")

if "selected_game" not in st.session_state:
    st.session_state.selected_game = list(GAMES.keys())[0]

selected_game = st.selectbox(
    "Select a game:",
    list(GAMES.keys()),
    index=list(GAMES.keys()).index(st.session_state.selected_game),
    label_visibility="collapsed",
)
st.session_state.selected_game = selected_game
game = GAMES[selected_game]

if game.get("bonus_ball"):
    game_desc = (
        f"You've selected **{selected_game}** — pick **{game['pick_size']}** numbers "
        f"from **1–{game['max_ball']}**, plus **1 Powerball** from **1–{game['bonus_ball']}**."
    )
else:
    game_desc = (
        f"You've selected **{selected_game}** — pick **{game['pick_size']}** numbers "
        f"from a pool of **1–{game['max_ball']}**."
    )
st.markdown(game_desc)

st.write("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

# --- Navigation guide ---
st.markdown("### 🧭 How to Navigate")
st.markdown(
    """
Use the sidebar on the left to move between pages:

- **🔥 Hot & Cold Singles** — build your number pool based on how often individual numbers
  have appeared (hottest or coldest), split into odd/even groups, then apply ratio and
  reduction filters to generate your system.
- **🍀 Quick Pick** — skip the strategy entirely and generate completely random combinations
  from the full pool, in whatever quantity you choose.

Every strategy page includes the same **reduction filters**, **system generator**,
**bell curve view**, **export options**, and **historical coverage / probability
analysis**, so you can compare strategies on equal footing.
"""
)
