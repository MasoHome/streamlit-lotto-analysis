import os
import io
import requests
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from analyzer import get_winning_columns


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


def extract_number(s):
    """Safely extracts digits from a string, returning 0 if none exist."""
    nums = ''.join(filter(str.isdigit, s))
    return int(nums) if nums else 0


# --- Consecutive Number Helpers ---
def has_two_consecutive(combo):
    """Returns True if any two adjacent numbers exist in the combo."""
    s = sorted(combo)
    return any(s[i + 1] - s[i] == 1 for i in range(len(s) - 1))


def has_three_consecutive(combo):
    """Returns True if any three consecutive numbers exist in the combo."""
    s = sorted(combo)
    return any(s[i + 2] - s[i] == 2 and s[i + 1] - s[i] == 1 for i in range(len(s) - 2))


# --- Last Digit Variety Helper ---
def exceeds_last_digit_limit(combo, max_allowed):
    """Returns True if any last-digit group (0-9) appears more than max_allowed times."""
    from collections import Counter
    digit_counts = Counter(n % 10 for n in combo)
    return any(count > max_allowed for count in digit_counts.values())


# --- Ball Frequency Square Grid (Hot -> Cold order) ---
def build_heatmap(df, game_config, last_n_draws):
    ball_cols = get_winning_columns(df)
    max_ball = game_config["max_ball"]

    df_slice = df.head(last_n_draws)
    all_balls = (
        df_slice[ball_cols]
        .apply(pd.to_numeric, errors='coerce')
        .stack().dropna().astype(int)
    )
    all_balls = all_balls[(all_balls >= 1) & (all_balls <= max_ball)]
    freq = all_balls.value_counts()

    all_ball_nums = list(range(1, max_ball + 1))
    sorted_pairs = sorted(all_ball_nums, key=lambda b: freq.get(b, 0), reverse=True)
    max_freq = max(freq.get(b, 0) for b in all_ball_nums) or 1

    def ordinal(n):
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n if n < 20 else n % 10, "th")
        return f"{n}{suffix}"

    cols = 10
    rows = int(np.ceil(max_ball / cols))

    z, text, customdata = [], [], []

    for r in range(rows):
        z_row, text_row, cd_row = [], [], []
        for c in range(cols):
            idx = r * cols + c
            if idx < len(sorted_pairs):
                ball = sorted_pairs[idx]
                f = int(freq.get(ball, 0))
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
    sums = df_matrix["Sum"].values
    mean = np.mean(sums)
    std = np.std(sums)

    x_min = min(sums.min(), min_pool_sum) - 5
    x_max = max(sums.max(), max_pool_sum) + 5
    x_curve = np.linspace(x_min, x_max, 300)
    y_curve = (1 / (std * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_curve - mean) / std) ** 2)

    bin_width = max(1, int((x_max - x_min) / 40))
    scale = len(sums) * bin_width
    y_curve_scaled = y_curve * scale

    fig = go.Figure()

    fig.add_vrect(
        x0=min_pool_sum, x1=max_pool_sum,
        fillcolor="#4caf50", opacity=0.12,
        layer="below", line_width=0,
        annotation_text="Selected range",
        annotation_position="top left",
        annotation_font_size=11,
        annotation_font_color="#4caf50",
    )

    fig.add_trace(go.Histogram(
        x=sums,
        nbinsx=40,
        name="Your combinations",
        marker_color="#1565c0",
        opacity=0.75,
    ))

    fig.add_trace(go.Scatter(
        x=x_curve,
        y=y_curve_scaled,
        mode="lines",
        name="Theoretical bell curve",
        line=dict(color="#e65100", width=2.5, dash="dash"),
    ))

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
