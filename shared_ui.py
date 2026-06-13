import io
import math
import time
import itertools

import streamlit as st
import pandas as pd

from analyzer import calculate_ratio_frequency
from lotto_utils import (
    extract_number,
    has_two_consecutive,
    has_three_consecutive,
    exceeds_last_digit_limit,
    build_bell_curve,
)


def render_strategy_workflow(df, game, odds_pool, evens_pool, page_key,
                              show_pool_breakdown=True,
                              show_consecutive_filter=True,
                              show_last_digit_filter=True):
    """
    Renders the shared part of every strategy page:
      - Current pool display
      - Custom pattern ratio
      - Reduction filters (consecutive, last digit, sum range)
      - Generate System
      - Bell curve
      - Exports
      - Historical coverage analysis
      - Probability of win estimate

    page_key: short unique string (e.g. "singles", "consec") used to namespace
    session_state keys so multiple strategy pages don't collide.
    """

    def k(name):
        return f"{page_key}_{name}"

    if show_pool_breakdown:
        st.markdown(f"**Current Pool Odds:** `{sorted(odds_pool)}`")
        st.markdown(f"**Current Pool Evens:** `{sorted(evens_pool)}`")

        st.write("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

    # ------------------------------------------------------------------ #
    #  Custom Pattern Ratio
    # ------------------------------------------------------------------ #
    st.markdown("## 🔢 Custom Pattern Ratio")
    enable_ratio = st.checkbox("Apply Custom Pattern Ratio", value=True, key=k("enable_ratio"))

    if game.get("bonus_ball"):
        col_p1, col_p2, col_p3 = st.columns(3)
    else:
        col_p1, col_p2 = st.columns(2)
    with col_p1:
        req_odds = st.number_input(
            "Odds to pick", 0, game["pick_size"], value=game["pick_size"] // 2,
            key=k("req_odds"), disabled=not enable_ratio
        )
    with col_p2:
        req_evens = st.number_input(
            "Evens to pick", 0, game["pick_size"],
            value=game["pick_size"] - (game["pick_size"] // 2),
            key=k("req_evens"), disabled=not enable_ratio
        )
    if game.get("bonus_ball"):
        with col_p3:
            powerball_num = st.selectbox(
                "Powerball number",
                options=list(range(1, game["bonus_ball"] + 1)),
                key=k("powerball_num"),
            )
    else:
        powerball_num = None

    if enable_ratio:
        freq_percent = calculate_ratio_frequency(df, game, req_odds)
        st.write(f"The **{req_odds}:{req_evens}** ratio historically covers **{freq_percent:.2f}%** of winning draws.")
    else:
        st.caption("Ratio filter disabled — all odd/even splits will be included.")

    st.write("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

    # ------------------------------------------------------------------ #
    #  Reduction Filters
    # ------------------------------------------------------------------ #
    st.markdown("## 🛠️ Reduction Filters")
    st.caption("Set these before generating — they'll be applied as the system is built.")

    if show_consecutive_filter:
        st.markdown("### 🔗 Consecutive Number Exclusion")
        consec_col1, consec_col2 = st.columns(2)
        with consec_col1:
            exclude_two_consec = st.checkbox(
                "Exclude 2 consecutive  (e.g. 7, 8)",
                value=False,
                key=k("exclude_two_consec"),
                help="Removes any combination where two numbers sit side by side (e.g. 7 & 8). This is the strictest filter — it also removes all 3-in-a-row runs."
            )
        with consec_col2:
            exclude_three_consec = st.checkbox(
                "Exclude 3 consecutive  (e.g. 6, 7, 8)",
                value=False,
                key=k("exclude_three_consec"),
                help="Removes any combination with three or more numbers in a row (e.g. 6, 7, 8). Pairs like 7 & 8 are still allowed."
            )

        st.write("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    else:
        exclude_two_consec = False
        exclude_three_consec = False

    # ------------------------------------------------------------------ #
    #  Last Digit Variety Filter
    # ------------------------------------------------------------------ #
    if show_last_digit_filter:
        st.markdown("### 🔠 Last Digit Variety Filter")
        digit_col1, digit_col2 = st.columns(2)
        with digit_col1:
            enable_last_digit_filter = st.checkbox(
                "Enable Last Digit Variety Filter",
                value=False,
                key=k("enable_last_digit_filter"),
                help="Limits how many numbers in a combination can share the same final digit "
                     "(e.g. 7, 17, 27, 37 all end in '7'). Helps avoid combinations that are "
                     "statistically skewed toward one digit ending."
            )
        with digit_col2:
            max_same_last_digit = st.slider(
                "Max numbers sharing the same last digit",
                min_value=1,
                max_value=game["pick_size"],
                value=2,
                disabled=not enable_last_digit_filter,
                key=k("max_same_last_digit"),
                help="A combination is excluded if more than this many numbers share the same last digit."
            )
        st.caption(
            "Example: with a max of 2, a combo containing 7, 17 and 27 (three numbers ending in '7') "
            "would be excluded."
        )

        st.write("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    else:
        enable_last_digit_filter = False
        max_same_last_digit = 2

    # ------------------------------------------------------------------ #
    #  Sum Range Filter
    # ------------------------------------------------------------------ #
    st.markdown("### 🔔 Sum Range Filter (Bell Curve Filter)")

    all_selected_nums = sorted(odds_pool + evens_pool)
    if len(all_selected_nums) >= game["pick_size"]:
        min_pool_sum = sum(all_selected_nums[:game["pick_size"]])
        max_pool_sum = sum(all_selected_nums[-game["pick_size"]:])
    else:
        min_pool_sum = sum(all_selected_nums)
        max_pool_sum = sum(all_selected_nums)

    global_min = sum(range(1, game["pick_size"] + 1))
    global_max = sum(range(game["max_ball"], game["max_ball"] - game["pick_size"], -1))

    current_pool_sig = (tuple(odds_pool), tuple(evens_pool))
    if st.session_state.get(k("last_pool_sig")) != current_pool_sig:
        st.session_state[k("sum_range")] = (min_pool_sum, max_pool_sum)
        st.session_state[k("last_pool_sig")] = current_pool_sig

    sum_range = st.slider(
        "Select sum range:",
        global_min,
        global_max,
        (min_pool_sum, max_pool_sum),
        label_visibility="collapsed",
        key=k("sum_range"),
    )
    st.caption(
        f"Minimum **{sum_range[0]}** is calculated from the {game['pick_size']} smallest numbers in your odd and even pools. "
        f"Maximum **{sum_range[1]}** is calculated from the {game['pick_size']} largest numbers in your odd and even pools."
    )
    enable_filter = st.checkbox("Apply Sum Range Filter (Bell Curve Filter)", value=True, key=k("enable_filter"))

    st.write("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

    # ------------------------------------------------------------------ #
    #  Generate System
    # ------------------------------------------------------------------ #
    st.markdown("## 🎰 Generate System")
    st.caption("📌 Once generated, your system will be available to download as a **CSV**, **XLSX** or **JSON** file.")

    def run_generation():
        if enable_ratio:
            if (req_odds + req_evens) != game["pick_size"]:
                st.error(f"⚠️ Invalid Pattern: Must total {game['pick_size']} numbers.")
                st.session_state[k("df_matrix")] = None
                return
            if req_odds > len(odds_pool) or req_evens > len(evens_pool):
                st.error(
                    f"⚠️ Pool too small: need {req_odds} odd / {req_evens} even numbers, "
                    f"but pool has {len(odds_pool)} odd / {len(evens_pool)} even."
                )
                st.session_state[k("df_matrix")] = None
                return

        full_pool = sorted(odds_pool + evens_pool)
        if not enable_ratio and len(full_pool) < game["pick_size"]:
            st.error(f"⚠️ Pool too small: need at least {game['pick_size']} numbers.")
            st.session_state[k("df_matrix")] = None
            return

        matrix_data = []
        excluded_consec = 0
        excluded_last_digit = 0
        excluded_sum = 0

        combos_iter = (
            (itertools.combinations(odds_pool, req_odds), itertools.combinations(evens_pool, req_evens))
            if enable_ratio
            else None
        )

        def all_combos():
            if enable_ratio:
                for o in itertools.combinations(odds_pool, req_odds):
                    for e in itertools.combinations(evens_pool, req_evens):
                        yield sorted(list(o) + list(e))
            else:
                for c in itertools.combinations(full_pool, game["pick_size"]):
                    yield list(c)

        for combo in all_combos():
                combo_sum = sum(combo)
                if enable_filter and not (sum_range[0] <= combo_sum <= sum_range[1]):
                    excluded_sum += 1
                    continue
                if exclude_two_consec and has_two_consecutive(combo):
                    excluded_consec += 1
                    continue
                if exclude_three_consec and not exclude_two_consec and has_three_consecutive(combo):
                    excluded_consec += 1
                    continue
                if enable_last_digit_filter and exceeds_last_digit_limit(combo, max_same_last_digit):
                    excluded_last_digit += 1
                    continue
                row = [combo_sum] + combo
                if powerball_num is not None:
                    row.append(powerball_num)
                matrix_data.append(row)

        st.session_state[k("sum_filter_info")] = {
            "excluded": excluded_sum,
            "range": sum_range,
            "enabled": enable_filter,
        }

        if not matrix_data:
            st.warning("⚠️ No combinations found with the current filters. Try relaxing the consecutive, last digit, or sum range filters.")
            st.session_state[k("df_matrix")] = None
        else:
            cols = ["Sum"] + [f"N{i}" for i in range(1, game['pick_size'] + 1)]
            if powerball_num is not None:
                cols.append("Powerball")
            st.session_state[k("df_matrix")] = pd.DataFrame(matrix_data, columns=cols)
            msg = f"Successfully generated {len(st.session_state[k('df_matrix')])} combinations."
            extras = []
            if excluded_consec > 0:
                extras.append(f"{excluded_consec} removed by consecutive filter")
            if excluded_last_digit > 0:
                extras.append(f"{excluded_last_digit} removed by last digit filter")
            if extras:
                msg += " (" + "; ".join(extras) + ")"
            st.session_state[k("matrix_msg")] = msg

            if enable_ratio:
                st.session_state[k("pool_space_total")] = (
                    math.comb(len(odds_pool), req_odds) * math.comb(len(evens_pool), req_evens)
                )
            else:
                st.session_state[k("pool_space_total")] = math.comb(len(odds_pool) + len(evens_pool), game["pick_size"])

    current_filter_state = (
        game["source"], game["pick_size"],
        enable_ratio, sum_range, enable_filter, exclude_two_consec, exclude_three_consec,
        enable_last_digit_filter, max_same_last_digit,
        req_odds, req_evens, tuple(odds_pool), tuple(evens_pool),
        powerball_num,
    )
    if k("last_filter_state") not in st.session_state:
        st.session_state[k("last_filter_state")] = None

    gen_status_placeholder = st.empty()

    if st.button("Generate System", key=k("generate_btn")):
        gen_status_placeholder.markdown('<div class="loading-overlay">Generating Matrix... Please wait</div>', unsafe_allow_html=True)
        time.sleep(1)
        try:
            run_generation()
            st.session_state[k("last_filter_state")] = current_filter_state
        except Exception as e:
            st.error(f"Error: {e}")
            st.session_state[k("df_matrix")] = None
        finally:
            gen_status_placeholder.empty()

    elif (
        st.session_state[k("last_filter_state")] is not None
        and current_filter_state != st.session_state[k("last_filter_state")]
        and k("df_matrix") in st.session_state
    ):
        try:
            run_generation()
            st.session_state[k("last_filter_state")] = current_filter_state
        except Exception as e:
            st.error(f"Error: {e}")

    # --- Display block ---
    if k("df_matrix") in st.session_state and st.session_state[k("df_matrix")] is not None:
        df_full = st.session_state[k("df_matrix")].reset_index(drop=True)
        df_full.insert(0, "Record Id", range(1, len(df_full) + 1))
        df_display = df_full

        if k("matrix_msg") in st.session_state:
            st.success(st.session_state[k("matrix_msg")])

        st.markdown("### 🎲 Generated System")

        if not df_display.empty:
            with st.expander("📋 View All Combinations", expanded=True):
                st.dataframe(df_display, use_container_width=True, hide_index=True)

        if not df_display.empty:
            with st.expander("📈 Sum Distribution & Bell Curve", expanded=True):
                fig_bell = build_bell_curve(df_display, game, min_pool_sum, max_pool_sum)
                st.plotly_chart(fig_bell, use_container_width=True)
                st.caption(
                    "🔵 Blue bars = your generated combinations  ·  "
                    "🟠 Dashed line = theoretical bell curve  ·  "
                    "🟢 Green band = your selected pool sum range  ·  "
                    "🟡 Dotted line = mean sum of your combinations"
                )

                sum_info = st.session_state.get(k("sum_filter_info"), {})
                if sum_info.get("enabled") and sum_info.get("excluded", 0) > 0:
                    excl = sum_info["excluded"]
                    remaining = len(df_display)
                    grand_total = excl + remaining
                    pct = excl / grand_total * 100
                    lo, hi = sum_info["range"]
                    st.info(
                        f"Sum range **{lo}–{hi}** eliminated **{excl:,} combinations** "
                        f"({pct:.1f}% of pool) — **{remaining:,} remain**."
                    )

        if not df_display.empty:
            csv = df_display.to_csv(index=False).encode('utf-8')

            xlsx_buffer = io.BytesIO()
            df_display.to_excel(xlsx_buffer, index=False, engine='openpyxl')
            xlsx_buffer.seek(0)

            json_data = df_display.to_json(orient='records', indent=2).encode('utf-8')

            dl_col1, dl_col2, dl_col3 = st.columns(3)
            with dl_col1:
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv,
                    file_name='lotto_matrix.csv',
                    mime='text/csv',
                    use_container_width=True,
                    key=k("dl_csv"),
                )
            with dl_col2:
                st.download_button(
                    label="📥 Download as XLSX",
                    data=xlsx_buffer,
                    file_name='lotto_matrix.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    use_container_width=True,
                    key=k("dl_xlsx"),
                )
            with dl_col3:
                st.download_button(
                    label="📥 Download as JSON",
                    data=json_data,
                    file_name='lotto_matrix.json',
                    mime='application/json',
                    use_container_width=True,
                    key=k("dl_json"),
                )

    # ------------------------------------------------------------------ #
    #  Historical Coverage Analysis
    # ------------------------------------------------------------------ #
    st.write("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)
    st.markdown("## 🔍 Historical Coverage Analysis")
    show_details = st.checkbox("Show Detailed Match List", key=k("details_toggle"))

    status_placeholder = st.empty()

    if st.button("Check Historical Wins", key=k("check_wins_btn")):
        status_placeholder.markdown('<div class="loading-overlay">Processing... Please wait</div>', unsafe_allow_html=True)
        st.session_state.is_loading = True

        try:
            if k("df_matrix") in st.session_state and st.session_state[k("df_matrix")] is not None:
                df_matrix = st.session_state[k("df_matrix")]
                df_history = df

                if df_history is not None:
                    draw_col = 'draw number'

                    all_ball_cols = [c for c in df_history.columns if any(char.isdigit() for char in c) and c != draw_col]
                    all_ball_cols = sorted(all_ball_cols, key=extract_number)

                    pick = game['pick_size']
                    main_ball_cols = all_ball_cols[:pick]

                    historical_data = [
                        (set(pd.to_numeric(row[main_ball_cols], errors='coerce').dropna().astype(int)), row[draw_col])
                        for _, row in df_history.iterrows()
                    ]

                    match_labels = [f"{n}/{pick}" for n in range(pick, 3, -1)]
                    results = {lbl: [] for lbl in match_labels}
                    counts = {lbl: 0 for lbl in match_labels}

                    matrix_cols = [f"N{i}" for i in range(1, pick + 1)]

                    for _, row in df_matrix.iterrows():
                        combo_set = set(row[matrix_cols].astype(int))

                        for hist_set, draw_id in historical_data:
                            intersection = combo_set.intersection(hist_set)
                            match_count = len(intersection)
                            if match_count >= 4:
                                label = f"{match_count}/{pick}"
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

                    if show_details:
                        st.subheader("🔍 Detailed Matches by Category")
                        for label in match_labels:
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
                st.warning("⚠️ Please Generate the System first.")

        except Exception as e:
            st.error(f"Error: {e}")

        finally:
            status_placeholder.empty()
            st.session_state.is_loading = False

    # ------------------------------------------------------------------ #
    #  Probability of Win
    # ------------------------------------------------------------------ #
    st.write("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)
    st.markdown("## 🎯 Probability of Win Estimate")

    if k("df_matrix") in st.session_state and st.session_state[k("df_matrix")] is not None:
        total_possible = math.comb(game["max_ball"], game["pick_size"]) * game.get("bonus_ball", 1)
        your_combos = len(st.session_state[k("df_matrix")])
        coverage_pct = (your_combos / total_possible) * 100

        odds_single = total_possible
        odds_with_set = total_possible / your_combos if your_combos > 0 else total_possible

        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            st.metric("Total Possible Combinations", f"{total_possible:,}")
        with pc2:
            st.metric("Your Generated Combinations", f"{your_combos:,}")
        with pc3:
            st.metric("Coverage of All Outcomes", f"{coverage_pct:.6f}%")

        st.caption(
            f"A single random ticket has odds of **1 in {odds_single:,.0f}** of matching the jackpot. "
            f"With your **{your_combos:,}** generated combination(s), your odds improve to "
            f"approximately **1 in {odds_with_set:,.0f}** — assuming the winning combination "
            f"falls within your selected pools."
        )

        st.write("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
        st.markdown("### 🎯 Pool-Conditional Probability")
        st.caption(
            "If the winning combination falls within your selected odd/even pools and ratio, "
            "here's how your filtered set compares to all combinations possible from that same pool."
        )

        pool_space_total = st.session_state.get(k("pool_space_total"), 0)
        if pool_space_total > 0:
            pool_coverage_pct = (your_combos / pool_space_total) * 100
            pool_odds = pool_space_total / your_combos if your_combos > 0 else pool_space_total

            ppc1, ppc2, ppc3 = st.columns(3)
            with ppc1:
                st.metric("Pool Space (Before Filters)", f"{pool_space_total:,}")
            with ppc2:
                st.metric("Your Filtered Combos", f"{your_combos:,}")
            with ppc3:
                st.metric("Pool Coverage", f"{pool_coverage_pct:.2f}%")

            st.caption(
                f"Within your chosen pools and ratio, there are **{pool_space_total:,}** possible combinations. "
                f"Your filtered set of **{your_combos:,}** covers **{pool_coverage_pct:.2f}%** of that space — "
                f"odds of approximately **1 in {pool_odds:,.0f}** if the winner is within your pools."
            )
        else:
            st.info("⚠️ Pool space data unavailable — try regenerating the system.")
    else:
        st.info("⚠️ Generate a system above to see your probability of win estimate.")
