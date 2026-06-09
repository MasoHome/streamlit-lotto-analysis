import streamlit as st
import pandas as pd
import itertools
import requests
import io
import os
import time
import plotly.graph_objects as go
import numpy as np
from analyzer import get_filtered_pools, calculate_ratio_frequency, get_winning_columns

# python app starting point
# Custom CSS to create a gray overlay
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

# Initialize state
if 'is_loading' not in st.session_state:
    st.session_state.is_loading = False

# Function to toggle loading state
def set_loading(): 
    st.session_state.is_loading = True

# The Overlay rendering (appears instantly when is_loading is True)
if st.session_state.is_loading:
    st.markdown('<div class="loading-overlay">Processing... Please wait</div>', unsafe_allow_html=True)


# --- Game Configuration ---
GAMES = {
    "Saturday Lotto": {"source": "https://www.lotterywest.wa.gov.au/api/games/5127/results-csv", "type": "url", "pick_size": 6, "max_ball": 45},
    "Oz Lotto (Tuesday)": {"source": "https://www.lotterywest.wa.gov.au/api/games/5129/results-csv", "type": "url", "pick_size": 7, "max_ball": 47},
    "Millionaire Medley (Mon/Wed/Fri)": {"source": "milli.csv", "type": "local", "pick_size": 6, "max_ball": 45},
    "Powerball (Thursday)": {"source": "powerball.csv", "type": "local", "pick_size": 7, "max_ball": 35}
}

st.set_page_config(page_title="Universal Lotto Engine", layout="centered")
st.title("🎯 Universal Lotto Ratio Matrix Engine")

st.markdown("### 🎲 Select Lottery Game:")
with st.container():
    selected_game = st.selectbox("Select a game:", list(GAMES.keys()), label_visibility="collapsed")
    st.write("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)
    game = GAMES[selected_game]

def extract_number(s):
    """Safely extracts digits from a string, returning 0 if none exist."""
    nums = ''.join(filter(str.isdigit, s))
    return int(nums) if nums else 0


# --- Data Fetching ---
@st.cache_data(ttl=3600)
def get_data(game_config):
    source = game_config["source"]
    source_type = game_config["type"]
    base_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        if source_type == "url":
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(source, headers=headers)
            if response.status_code == 200:
                df = pd.read_csv(io.StringIO(response.text))
            else:
                return None
        else:
            full_path = os.path.join(base_dir, "data", source)
            if os.path.exists(full_path):
                df = pd.read_csv(full_path)
            else:
                st.error(f"⚠️ File not found: {source}")
                return None
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception:
        return None


# --- UPDATED: Ball Frequency Square Grid (Hot → Cold order) ---
def build_heatmap(df, game_config, last_n_draws):
    """
    Renders each ball as a coloured square ordered hot → cold (left to right,
    top to bottom). Ball number and frequency shown inside each square.
    """
    ball_cols = get_winning_columns(df)
    max_ball  = game_config["max_ball"]

    df_slice  = df.head(last_n_draws)
    all_balls = (
        df_slice[ball_cols]
        .apply(pd.to_numeric, errors='coerce')
        .stack().dropna().astype(int)
    )
    all_balls = all_balls[(all_balls >= 1) & (all_balls <= max_ball)]
    freq = all_balls.value_counts()

    # Sort all balls hot → cold
    all_ball_nums = list(range(1, max_ball + 1))
    sorted_pairs  = sorted(all_ball_nums, key=lambda b: freq.get(b, 0), reverse=True)
    max_freq = max(freq.get(b, 0) for b in all_ball_nums) or 1

    def ordinal(n):
        suffix = {1:"st", 2:"nd", 3:"rd"}.get(n if n < 20 else n % 10, "th")
        return f"{n}{suffix}"

    def freq_colour(f):
        n = f / max_freq
        if n >= 0.80: return "#b71c1c", "white"   # crimson
        elif n >= 0.60: return "#e65100", "white"  # deep orange
        elif n >= 0.40: return "#f9a825", "#222"   # amber
        elif n >= 0.20: return "#1565c0", "white"  # mid blue
        else: return "#1a237e", "white"             # deep navy

    # Grid layout: 10 columns
    cols = 10
    rows = int(np.ceil(max_ball / cols))

    # Build scatter with shapes — use SVG-style squares via scatter markers
    # We'll use a heatmap with reordered z so squares appear hot→cold L→R T→B
    z, text, customdata = [], [], []

    for r in range(rows):
        z_row, text_row, cd_row = [], [], []
        for c in range(cols):
            idx = r * cols + c
            if idx < len(sorted_pairs):
                ball = sorted_pairs[idx]
                f    = int(freq.get(ball, 0))
                rank = ordinal(idx + 1)
                z_row.append(f)
                text_row.append(f"<b>{ball}</b><br>{f}x<br><i>{rank}</i>")
                cd_row.append(f"Ball {ball} | Drawn {f}x | Rank: {rank}")
            else:
                z_row.append(None)
                text_row.append("")
                cd_row.append("")
        z.append(z_row)
        text.append(text_row)
        customdata.append(cd_row)

    fig = go.Figure(data=go.Heatmap(
        z=z,
        text=text,
        texttemplate="%{text}",
        textfont=dict(size=15),
        hovertext=customdata,
        hoverinfo="text",
        colorscale=[
            [0.00, "#1a237e"],
            [0.20, "#1565c0"],
            [0.40, "#f9a825"],
            [0.60, "#e65100"],
            [1.00, "#b71c1c"],
        ],
        showscale=True,
        colorbar=dict(title="Frequency", thickness=14, len=0.8),
        xgap=4,
        ygap=4,
    ))

    fig.update_layout(
        title=dict(
            text=f"🔥 Ball Frequency — Hottest to Coldest | Last {last_n_draws} draws",
            font=dict(size=15),
        ),
        xaxis=dict(showticklabels=False, showgrid=False),
        yaxis=dict(showticklabels=False, showgrid=False, autorange="reversed"),
        height=max(300, rows * 75 + 80),
        margin=dict(l=20, r=20, t=70, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13),
    )
    return fig


def build_bell_curve(df_matrix, game_config, min_pool_sum, max_pool_sum):
    """
    Builds a Plotly chart showing:
    - Histogram of generated combination sums
    - Theoretical normal (bell curve) overlay
    - Shaded region showing the selected sum range
    """
    sums = df_matrix["Sum"].values
    mean = np.mean(sums)
    std  = np.std(sums)

    # Theoretical bell curve x range
    x_min = min(sums.min(), min_pool_sum) - 5
    x_max = max(sums.max(), max_pool_sum) + 5
    x_curve = np.linspace(x_min, x_max, 300)
    y_curve = (1 / (std * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_curve - mean) / std) ** 2)

    # Scale curve to match histogram counts
    bin_width = max(1, int((x_max - x_min) / 40))
    scale = len(sums) * bin_width
    y_curve_scaled = y_curve * scale

    fig = go.Figure()

    # Shaded selected range
    fig.add_vrect(
        x0=min_pool_sum, x1=max_pool_sum,
        fillcolor="#4caf50", opacity=0.12,
        layer="below", line_width=0,
        annotation_text="Selected range",
        annotation_position="top left",
        annotation_font_size=11,
        annotation_font_color="#4caf50",
    )

    # Histogram of actual combination sums
    fig.add_trace(go.Histogram(
        x=sums,
        nbinsx=40,
        name="Your combinations",
        marker_color="#1565c0",
        opacity=0.75,
    ))

    # Theoretical bell curve overlay
    fig.add_trace(go.Scatter(
        x=x_curve,
        y=y_curve_scaled,
        mode="lines",
        name="Theoretical bell curve",
        line=dict(color="#e65100", width=2.5, dash="dash"),
    ))

    # Mean line
    fig.add_vline(
        x=mean, line_dash="dot", line_color="#f9a825", line_width=2,
        annotation_text=f"Mean: {mean:.1f}",
        annotation_position="top right",
        annotation_font_color="#f9a825",
    )

    fig.update_layout(
        title=dict(text="📈 Sum Distribution vs Bell Curve", font=dict(size=15)),
        xaxis_title="Combination Sum",
        yaxis_title="Count",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        bargap=0.05,
        height=350,
        margin=dict(l=40, r=20, t=70, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=12),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.2)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(128,128,128,0.2)")
    return fig


df = get_data(game)

if df is not None:
    # ------------------------------------------------------------------ #
    #  Draw Window Selector (controls BOTH heatmap AND hot/cold pools)   #
    # ------------------------------------------------------------------ #
    total_draws = len(df)
    draw_options = [50, 100, 200, 500, total_draws]
    draw_options = sorted(set(min(o, total_draws) for o in draw_options))
    draw_labels  = [f"Last {n} draws" if n < total_draws else f"All {n} draws" for n in draw_options]

    st.markdown("### 📅 Analysis Draw Window")
    st.caption("Controls both the frequency heatmap and the Hot/Cold number pools below.")
    selected_label = st.select_slider(
        "Draw window:",
        options=draw_labels,
        value=draw_labels[min(1, len(draw_labels)-1)],
        label_visibility="collapsed",
    )
    last_n = draw_options[draw_labels.index(selected_label)]

    # ------------------------------------------------------------------ #
    #  Heatmap Visualization                                              #
    # ------------------------------------------------------------------ #
    with st.expander("🔥 Ball Frequency Ranking", expanded=False):
        fig_heatmap = build_heatmap(df, game, last_n)
        st.plotly_chart(fig_heatmap, use_container_width=True)
        st.caption(
            "🔴 Crimson = hottest  ·  🟠 Orange = warm  ·  🟡 Amber = neutral  ·  🔵 Blue = coldest  ·  "
            "Ordered hot → cold left to right, top to bottom  ·  Hover a square for full details."
        )

    st.write("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

    # ------------------------------------------------------------------ #
    #  Strategy Filters (unchanged)                                       #
    # ------------------------------------------------------------------ #
    st.subheader("🛡️ Strategy Filters")
    col1, col2 = st.columns(2)
    with col1:
        o_type = st.radio("Odd Type", ["Hot", "Cold"], horizontal=True)
        o_size = st.slider("Size of Odd Pool", 5, 20, 10)
    with col2:
        e_type = st.radio("Even Type", ["Hot", "Cold"], horizontal=True)
        e_size = st.slider("Size of Even Pool", 5, 20, 10)
        
    st.write("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

    # new section
    st.markdown("## 🔢 Custom Pattern Ratio")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        req_odds = st.number_input("Odds to pick", 0, game["pick_size"], value=game["pick_size"] // 2)
    with col_p2:
        req_evens = st.number_input("Evens to pick", 0, game["pick_size"], value=game["pick_size"] - (game["pick_size"] // 2))


    # --- Frequency Calculation ---
    freq_percent = calculate_ratio_frequency(df, game, req_odds)
    st.write(f"The **{req_odds}:{req_evens}** ratio historically covers **{freq_percent:.2f}%** of winning draws.")

    odds_pool, evens_pool = get_filtered_pools(df, game, o_size, e_size, o_type, e_type, last_n)

    st.markdown(f"**Current Pool Odds No Supps Taken ({o_type}):** `{sorted(odds_pool)}`")
    st.markdown(f"**Current Pool Evens No Supps Taken ({e_type}):** `{sorted(evens_pool)}`")


    # --- Dynamic Range Calculation ---
    all_selected_nums = sorted(odds_pool + evens_pool)
    min_pool_sum = sum(all_selected_nums[:game["pick_size"]])
    max_pool_sum = sum(all_selected_nums[-game["pick_size"]:])
    global_max = sum(range(game["max_ball"], game["max_ball"] - game["pick_size"], -1))
    
    with st.container():
        sum_range = st.slider(
            "Select sum range:", 
            21, 
            global_max, 
            (min_pool_sum, max_pool_sum), 
            label_visibility="collapsed"
        )        
        st.markdown("<p style='text-align: center; margin-top: -15px; margin-bottom: 25px;'>Move slider to refine your search.</p>", unsafe_allow_html=True)

    enable_filter = st.checkbox("Apply Bell Curve Filter", value=True)


    # 1. Generate Matrix
    gen_status_placeholder = st.empty()


    # 2. THE BUTTON BLOCK (Logic only)
    if st.button("Generate Matrix"):
        gen_status_placeholder.markdown('<div class="loading-overlay">Generating Matrix... Please wait</div>', unsafe_allow_html=True)
        time.sleep(1) 
        
        try:
            if (req_odds + req_evens) != game["pick_size"]:
                st.error(f"⚠️ Invalid Pattern: Must total {game['pick_size']} numbers.")
                st.session_state.df_matrix = None
            else:
                matrix_data = []
                for o in itertools.combinations(odds_pool, req_odds):
                    for e in itertools.combinations(evens_pool, req_evens):
                        combo = sorted(list(o) + list(e))
                        combo_sum = sum(combo)
                        if not enable_filter or (min_pool_sum <= combo_sum <= max_pool_sum):
                            matrix_data.append([combo_sum] + combo)
                
                if not matrix_data:
                    st.warning("⚠️ No combinations found in this range.")
                    st.session_state.df_matrix = None
                else:
                    st.session_state.df_matrix = pd.DataFrame(matrix_data, columns=["Sum"] + [f"N{i}" for i in range(1, game['pick_size']+1)])
                    st.session_state.matrix_msg = f"Successfully generated {len(st.session_state.df_matrix)} combinations."
        except Exception as e:
            st.error(f"Error: {e}")
            st.session_state.df_matrix = None
        finally:
            gen_status_placeholder.empty()


    # 3. THE DISPLAY BLOCK (Renders once per rerun)  
    if 'df_matrix' in st.session_state and st.session_state.df_matrix is not None:
        df_display = st.session_state.df_matrix.reset_index(drop=True)
        df_display.insert(0, "Record Id", range(1, len(df_display) + 1))
        df_display = df_display.sort_values(by="Record Id", ascending=True)
        
        st.subheader("🎲 Generated Matrix")
        
        if 'matrix_msg' in st.session_state:
            st.success(st.session_state.matrix_msg)
            
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Record Id": st.column_config.NumberColumn("Record Id", format="%d")
            }
        )
   
        # --- Bell Curve Visualization ---
        with st.expander("📈 Sum Distribution & Bell Curve", expanded=True):
            fig_bell = build_bell_curve(st.session_state.df_matrix, game, min_pool_sum, max_pool_sum)
            st.plotly_chart(fig_bell, use_container_width=True)
            st.caption(
                "🔵 Blue bars = your generated combinations  ·  "
                "🟠 Dashed line = theoretical bell curve  ·  "
                "🟢 Green band = your selected sum range  ·  "
                "🟡 Dotted line = mean sum of your combinations"
            )

        csv = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name='lotto_matrix.csv',
            mime='text/csv',
        )


    # History Analysis Section
    st.markdown("## 🔍 Historical Coverage Analysis")
    show_details = st.checkbox("Show Detailed Match List", key="details_toggle")

    status_placeholder = st.empty()

    if st.button("Check Historical Wins"):
        status_placeholder.markdown('<div class="loading-overlay">Processing... Please wait</div>', unsafe_allow_html=True)
        st.session_state.is_loading = True
        
        try:
            if 'df_matrix' in st.session_state and st.session_state.df_matrix is not None:
                df_matrix = st.session_state.df_matrix
                df_history = get_data(game)
                
                if df_history is not None:
                    draw_col = 'draw number' 
                    
                    all_ball_cols = [c for c in df_history.columns if any(char.isdigit() for char in c) and c != draw_col]
                    all_ball_cols = sorted(all_ball_cols, key=extract_number)
                    
                    main_ball_cols = all_ball_cols[:6]
                    
                    historical_data = [
                        (set(pd.to_numeric(row[main_ball_cols], errors='coerce').dropna().astype(int)), row[draw_col])
                        for _, row in df_history.iterrows()
                    ]

                    results = {"6/6": [], "5/6": [], "4/6": []}
                    counts = {"6/6": 0, "5/6": 0, "4/6": 0}
                    matrix_cols = [f"N{i}" for i in range(1, game['pick_size'] + 1)]
                    
                    for _, row in df_matrix.iterrows():
                        combo_set = set(row[matrix_cols].astype(int))
                        
                        for hist_set, draw_id in historical_data:
                            intersection = combo_set.intersection(hist_set)
                            match_count = len(intersection)
                            if match_count >= 4:
                                label = f"{match_count}/6"
                                counts[label] += 1
                                
                                if show_details:
                                    results[label].append({
                                        "Draw Number": draw_id,
                                        "Combination": sorted(list(combo_set)),
                                        "Matched Numbers": sorted(list(intersection))
                                    })

                    st.success("Analysis complete.")
                    st.subheader("📊 Match Summary")
                    st.table(pd.DataFrame.from_dict(counts, orient='index', columns=['Frequency']))
                    
                    # show detail of winning combination if selected
                    if show_details:
                        st.subheader("🔍 Detailed Matches by Category")
                        for label in ["6/6", "5/6", "4/6"]:
                            if results[label]:
                                df_res = pd.DataFrame(results[label])
                                df_res = df_res.sort_values(by="Draw Number", ascending=True)
                                df_res.insert(0, "Record ID", range(1, len(df_res) + 1))
                                
                                with st.expander(f"View {label} Matches ({len(df_res)} total matches)"):
                                    st.dataframe(
                                        df_res,
                                        use_container_width=True,
                                        hide_index=True,
                                        column_config={
                                            "Record ID": st.column_config.NumberColumn("Record ID", format="%d"),
                                            "Draw Number": st.column_config.NumberColumn("Draw Number", format="%d")
                                        }
                                    )
                            else:
                                st.write(f"No {label} matches found.")
                else:
                    st.error("Could not load historical data.")
            else:
                st.warning("⚠️ Please Generate the Matrix first.")
        
        except Exception as e:
            st.error(f"Error: {e}")
        
        finally:
            status_placeholder.empty()
            st.session_state.is_loading = False