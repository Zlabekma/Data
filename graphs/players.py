import pandas as pd
import plotly.graph_objs as go
import plotly.express as px

def generate_player_score_dist(df,player, binsize):
    # Filter the DataFrame for the specific player
    df_player = df[df['Hráč'] == player]
    
    start = int(df_player['Skóre 10. kolo'].min())
    end = int(df_player['Skóre 10. kolo'].max()) + binsize

    # Create bin labels
    bin_labels = [f"{i}-{i+binsize-1}" for i in range(start, end, binsize)]

    fig = go.Figure(data=[go.Histogram(
        x=df_player['Skóre 10. kolo'],
        xbins=dict(
            start=start,
            end=end,
            size=binsize
        ),
        marker_color='blue',
        marker_line_color='black',
        marker_line_width=1
    )])

    fig.update_layout(
        title=f'Scores Distribution for Player {player}',
        xaxis_title='Score Ranges',
        yaxis_title='Frequency',
        xaxis=dict(
            tickmode='array',
            tickvals=[i + binsize / 2 for i in range(start, end, binsize)],
            ticktext=bin_labels
        )
    )
    return fig


def generate_combined_strikes_and_spares_evolution_plot(df,player):
    df_player = df[df['Hráč'] == player]
    strike_columns_all = [col for col in df_player.columns if 'kolo' in col and 'Skóre' not in col]
    
    # Calculate total strikes
    df_player['Total_Strikes'] = df_player[strike_columns_all].apply(lambda x: (x == 'Strike').sum(), axis=1)
    
    # Calculate total spares
    df_player['Total_Spares'] = df_player[strike_columns_all].apply(lambda x: (x == 'Spare').sum(), axis=1)
    
    # Create a combined figure
    fig = go.Figure()
    
    # Add strikes trace
    fig.add_trace(go.Scatter(x=df_player['absolute_game_position'], y=df_player['Total_Strikes'],
                             mode='lines+markers', name='Strikes Over Time'))
    
    # Add spares trace
    fig.add_trace(go.Scatter(x=df_player['absolute_game_position'], y=df_player['Total_Spares'],
                             mode='lines+markers', name='Spares Over Time'))
    
    # Update layout
    fig.update_layout(title=f'Evolution of Strikes and Spares Over Time for Player {player}',
                      xaxis_title='Absolute Game Position',
                      yaxis_title='Number of Strikes/Spares',
                      template='plotly_white')
    
    return fig


# Graph generation functions for individual players
def generate_round_distribution_plot(df,player):
    df_player = df[df['Hráč'] == player]
    round_columns = [col for col in df_player.columns if 'kolo' in col and 'Skóre' not in col]
    round_results = df_player[round_columns].astype(str).apply(pd.Series.value_counts).sum(axis=1).fillna(0)
    round_results_percentage = (round_results / round_results.sum()) * 100
    fig = px.pie(values=round_results_percentage, names=round_results_percentage.index,
                 title=f'Distribution of Round Results for Player {player}', hole=0.3)
    return fig

def generate_strikes_evolution_plot(df,player):
    df_player = df[df['Hráč'] == player]
    strike_columns_all = [col for col in df_player.columns if 'kolo' in col and 'Skóre' not in col]
    df_player['Total_Strikes'] = df_player[strike_columns_all].apply(lambda x: (x == 'Strike').sum(), axis=1)
    fig = go.Figure(go.Scatter(x=df_player['absolute_game_position'], y=df_player['Total_Strikes'],
                               mode='lines+markers', name='Strikes Over Time'))
    fig.update_layout(title=f'Evolution of Number of Strikes Over Time for Player {player}',
                      xaxis_title='Absolute Game Position', yaxis_title='Number of Strikes', template='plotly_white')
    return fig

def generate_spares_evolution_plot(df,player):
    df_player = df[df['Hráč'] == player]
    strike_columns_all = [col for col in df_player.columns if 'kolo' in col and 'Skóre' not in col]
    df_player['Total_Spares'] = df_player[strike_columns_all].apply(lambda x: (x == 'Spare').sum(), axis=1)
    fig = go.Figure(go.Scatter(x=df_player['absolute_game_position'], y=df_player['Total_Spares'],
                               mode='lines+markers', name='Spares Over Time'))
    fig.update_layout(title=f'Evolution of Number of Spares Over Time for Player {player}',
                      xaxis_title='Absolute Game Position', yaxis_title='Number of Spares', template='plotly_white')
    return fig

def generate_position_over_time_plot(df,player):
    df_player = df[df['Hráč'] == player]
    if 'Rank' not in df_player.columns:
        df_player['Rank'] = df_player.groupby('absolute_game_position')['Skóre 10. kolo'].rank(ascending=False, method='min')
    
    fig = px.line(df_player, x='absolute_game_position', y='Rank',
                  title=f'Position Over Time for Player {player}',
                  labels={'absolute_game_position': 'Absolute Game Position', 'Rank': 'Position'},
                  markers=True)
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(template='plotly_white')
    return fig
