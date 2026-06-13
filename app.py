import streamlit as st

st.set_page_config(page_title="Universal Lotto Engine", layout="centered")

# Loading overlay CSS (shared across all pages)
st.markdown("""
    <style>
    .loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.5);
        z-index: 9999;
        display: flex;
        justify-content: center;
        align-items: center;
        color: white;
        font-size: 24px;
    }
    </style>
""", unsafe_allow_html=True)

welcome   = st.Page("home.py", title="Welcome", default=True)
singles   = st.Page("pages/hot_cold_singles.py", title="Hot Cold Singles")
quick     = st.Page("pages/quick_pick.py", title="Quick Pick")
my_system = st.Page("pages/my_system.py", title="My System")

pg = st.navigation([welcome, singles, quick, my_system])
pg.run()
