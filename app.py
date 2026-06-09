import streamlit as st
import pandas as pd
import itertools
import requests
import io
import os
import time
from analyzer import get_filtered_pools, calculate_ratio_frequency

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
    # selected_game = st.selectbox("", list(GAMES.keys()))    
    selected_game = st.selectbox("Select a game:", list(GAMES.keys()), label_visibility="collapsed")
    # This adds vertical space before the Strategy Filters section starts
    st.write("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)
    game = GAMES[selected_game]

def extract_number(s):
    """Safely extracts digits from a string, returning 0 if none exist."""
    nums = ''.join(filter(str.isdigit, s))
    return int(nums) if nums else 0


# --- Data Fetching ---
@st.cache_data(ttl=3600) # Cache for 1 hour
@st.cache_data
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

df = get_data(game)

if df is not None:
    # section
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

    odds_pool, evens_pool = get_filtered_pools(df, game, o_size, e_size, o_type, e_type)

    st.markdown(f"**Current Pool Odds No Supps Taken ({o_type}):** `{sorted(odds_pool)}`")
    st.markdown(f"**Current Pool Evens No Supps Taken ({e_type}):** `{sorted(evens_pool)}`")
    



    # --- Dynamic Range Calculation ---
    all_selected_nums = sorted(odds_pool + evens_pool)
    min_pool_sum = sum(all_selected_nums[:game["pick_size"]])
    max_pool_sum = sum(all_selected_nums[-game["pick_size"]:])
    global_max = sum(range(game["max_ball"], game["max_ball"] - game["pick_size"], -1))
    
    # CORRECT
    with st.container():
        # st.markdown(f"**Auto-Calculated Pool Range:** `{min_pool_sum}` to `{max_pool_sum}`")   
        sum_range = st.slider("Select range:", 21, global_max, (min_pool_sum, max_pool_sum), label_visibility="collapsed")
        # sum_range = st.slider("", 21, global_max, (min_pool_sum, max_pool_sum) )        
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
        # Trigger the processing message
        gen_status_placeholder.markdown('<div class="loading-overlay">Generating Matrix... Please wait</div>', unsafe_allow_html=True)
        
        # We use a slight delay so the UI registers the loading state
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
            # Clear the processing message immediately when done
            gen_status_placeholder.empty()



    # 3. THE DISPLAY BLOCK (Renders once per rerun)  
    if 'df_matrix' in st.session_state and st.session_state.df_matrix is not None:
        # 1. Prepare data
        df_display = st.session_state.df_matrix.reset_index(drop=True)
        df_display.insert(0, "Record Id", range(1, len(df_display) + 1))
        df_display = df_display.sort_values(by="Record Id", ascending=True)
        
        st.subheader("🎲 Generated Matrix")
        
        # 2. Render Message FIRST (Now it appears above the table)
        if 'matrix_msg' in st.session_state:
            st.success(st.session_state.matrix_msg)
            
        # 3. Render Table SECOND
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Record Id": st.column_config.NumberColumn("Record Id", format="%d")
            }
        )
   



    # History Analysis Section
    st.markdown("## 🔍 Historical Coverage Analysis")
    show_details = st.checkbox("Show Detailed Match List", key="details_toggle")

    # Create a persistent placeholder for the overlay
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
                    
                    # 1. Identify all ball columns and sort them correctly
                    all_ball_cols = [c for c in df_history.columns if any(char.isdigit() for char in c) and c != draw_col]
                    all_ball_cols = sorted(all_ball_cols, key=extract_number)
                    
                    # 2. IMPORTANT: Only use the first 6 main balls for matching
                    main_ball_cols = all_ball_cols[:6]
                    
                    historical_data = [
                        (set(pd.to_numeric(row[main_ball_cols], errors='coerce').dropna().astype(int)), row[draw_col])
                        for _, row in df_history.iterrows()
                    ]

                    # 3. Initialize tracking
                    results = {"6/6": [], "5/6": [], "4/6": []}
                    counts = {"6/6": 0, "5/6": 0, "4/6": 0}
                    matrix_cols = [f"N{i}" for i in range(1, game['pick_size'] + 1)]
                    
                    # 4. Perform match analysis
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

                    # 5. Display Summary Table
                    st.success("Analysis complete.")
                    st.subheader("📊 Match Summary")
                    st.table(pd.DataFrame.from_dict(counts, orient='index', columns=['Frequency']))
                    
                    # 6. Display Detailed Matches
                    if show_details:
                        st.subheader("🔍 Detailed Matches by Category")
                        for label in ["6/6", "5/6", "4/6"]:
                            if results[label]:
                                df_res = pd.DataFrame(results[label])
                                
                                # Sort chronologically
                                df_res = df_res.sort_values(by="Draw Number", ascending=True)
                                
                                # Add sequential Record ID (1, 2, 3...)
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