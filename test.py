import pandas as pd
import requests
import io

# URL for Saturday Lotto
url = "https://www.lotterywest.wa.gov.au/api/games/5127/results-csv"
headers = {'User-Agent': 'Mozilla/5.0'}

try:
    response = requests.get(url, headers=headers)
    df = pd.read_csv(io.StringIO(response.text))
    df.columns = df.columns.str.strip().str.lower()
    
    # Target only ball columns
    ball_cols = [col for col in df.columns if 'n' in col or 'ball' in col]
    all_balls = df[ball_cols].apply(pd.to_numeric, errors='coerce').stack().dropna().astype(int)
    
    # Calculate frequency
    freq = all_balls.value_counts()
    
    # Get all odd numbers (1-45)
    all_odds = [n for n in range(1, 46) if n % 2 != 0]
    
    # Rank by frequency (desc), then number (asc) for stability
    ranked_odds = sorted(all_odds, key=lambda x: (-freq.get(x, 0), x))
    
    print("--- Top 10 Odd Numbers by Frequency (Saturday Lotto) ---")
    for n in ranked_odds[:10]:
        print(f"Number {n:02d}: Appeared {freq.get(n, 0)} times")
        
except Exception as e:
    print(f"Error fetching data: {e}")