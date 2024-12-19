# utils/data_prep.py
import pandas as pd
import plotly.colors

def prepare_data(df):
    # Format the 'Den' column with corrected date parsing
    df['Den'] = pd.to_datetime(df['Den'], errors='coerce').dt.strftime('%d/%m/%Y')

    # Prepare last game data
    Last_game_rows = df[pd.to_datetime(df['Den'], format='%d/%m/%Y') == pd.to_datetime(df['Den'], format='%d/%m/%Y').max()]
    players = df['Hráč'].unique()
    #players = Last_game_rows['Hráč'].unique()

    # Venue and Date for the last game
    venue = Last_game_rows.iloc[0]['Podnik']
    date = Last_game_rows.iloc[0]['Den']
    num_rounds = Last_game_rows['Pořadové č. hry'].max()

    # Calculate summary statistics for last game
    sum_scores = Last_game_rows.groupby('Hráč', as_index=False)['Skóre 10. kolo'].sum()
    max_sum_score = sum_scores.loc[sum_scores['Skóre 10. kolo'].idxmax()]
    max_score = Last_game_rows.groupby('Hráč', as_index=False)['Skóre 10. kolo'].max().loc[sum_scores['Skóre 10. kolo'].idxmax()]
    total_score = Last_game_rows['Skóre 10. kolo'].sum()
    team_avg_score = total_score / (num_rounds * len(Last_game_rows['Hráč'].unique()))

    # Count strikes
    strike_columns = [col for col in Last_game_rows.columns if 'kolo' in col and 'Skóre' not in col]
    strike_counts = Last_game_rows.groupby('Hráč')[strike_columns].apply(lambda x: (x == 'Strike').sum().sum())
    strike_counts_df = strike_counts.reset_index(name='Num Strikes').sort_values(by='Num Strikes', ascending=False)
    top_strikes = strike_counts_df.iloc[0]

    # Prepare data for additional graphs
    df['Den'] = pd.to_datetime(df['Den'], dayfirst=True, errors='coerce')
    df = df.sort_values(by=['Hráč', 'Pořadové č. hry'])
    df['cumulative_avg_score'] = df.groupby('Hráč')['Skóre 10. kolo'].expanding().mean().reset_index(level=0, drop=True)

    ordered_dates = df['Den'].sort_values().unique()
    cumulative_games = 0
    games_per_date = {}
    for date in ordered_dates:
        date_str = date.strftime('%Y-%m-%d')
        games_today = df[df['Den'] == date]['Pořadové č. hry'].max()
        games_per_date[date] = cumulative_games
        cumulative_games += games_today
    df['absolute_game_position'] = df['Den'].map(games_per_date) + df['Pořadové č. hry']

    grouped = df.groupby('absolute_game_position')['Skóre 10. kolo']
    avg_min_max_scores = [grouped.mean(), grouped.min() ,grouped.max()]

    round_columns = [col for col in df.columns if 'kolo' in col and 'Skóre' not in col]
    round_results = df[round_columns].astype(str).apply(pd.Series.value_counts).sum(axis=1).fillna(0)
    round_results_percentage = (round_results / round_results.sum()) * 100

    df = df.sort_values(by=['Hráč', 'absolute_game_position'])

    # Calculate the rank for each player at each absolute game position
    df['Rank'] = df.groupby('absolute_game_position')['Skóre 10. kolo'].rank(ascending=False, method='min')

    # Color assignment
    colors = plotly.colors.qualitative.Plotly
    color_dict = {player: colors[i % len(colors)] for i, player in enumerate(players)}



    return {
        "df": df,
        "players": players,
        "venue": venue,
        "date": date,
        "num_rounds": num_rounds,
        "max_sum_score": max_sum_score,
        "max_score": max_score,
        "team_avg_score": team_avg_score,
        "top_strikes": top_strikes,
        "avg_min_max_scores": avg_min_max_scores,
        "round_results_percentage": round_results_percentage,
        "color_dict": color_dict
    }
