import pandas as pd
import numpy as np

def get_winning_columns(df):
  
   # 1. Normalize headers to lowercase
    df.columns = df.columns.str.lower()
    
    # 2. Define the terms that identify ANY ball we want to count
    # This will catch 'winning number 1', 'supplementary number', etc.
    search_terms = ['winning']
    
    # 3. Build the list of columns
    final_cols = [
        col for col in df.columns 
        if any(term in col for term in search_terms)
    ]
    
    # This will print every time the function is called
    print(f"DEBUG: Found {len(final_cols)} winning columns: {final_cols}")
    
    return sorted(final_cols)
    

    
def get_filtered_pools(df, game_config, o_size, e_size, o_type, e_type):
    ball_cols = get_winning_columns(df)
    
    # Extract only valid numeric balls
    all_balls = df[ball_cols].apply(pd.to_numeric, errors='coerce').stack().dropna().astype(int)
    all_balls = all_balls[(all_balls >= 1) & (all_balls <= game_config['max_ball'])]
    
    # Calculate frequency
    freq = all_balls.value_counts()
    
    odds = [n for n in range(1, game_config['max_ball'] + 1) if n % 2 != 0]
    evens = [n for n in range(1, game_config['max_ball'] + 1) if n % 2 == 0]
    
    # Sort pools based on frequency (Hot=High count, Cold=Low count)
    odds_pool = sorted(odds, key=lambda x: freq.get(x, 0), reverse=(o_type == "Hot"))[:o_size]
    evens_pool = sorted(evens, key=lambda x: freq.get(x, 0), reverse=(e_type == "Hot"))[:e_size]
        
    return sorted(odds_pool), sorted(evens_pool)



def calculate_ratio_frequency(df, game_config, req_odds):
    ball_cols = get_winning_columns(df)
    
    def count_odds(row):
        nums = pd.to_numeric(row[ball_cols], errors='coerce').dropna()
        valid_balls = [int(n) for n in nums if 1 <= n <= game_config['max_ball']]
        if len(valid_balls) != game_config['pick_size']: return -1
        return sum(1 for n in valid_balls if n % 2 != 0)
    
    odd_counts = df.apply(count_odds, axis=1)
    matches = (odd_counts == req_odds)
    valid_rows = (odd_counts != -1)
    
    return (matches.sum() / valid_rows.sum()) * 100 if valid_rows.sum() > 0 else 0.0