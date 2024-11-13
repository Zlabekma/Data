from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import plotly.colors
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime


# Initialize the Dash app
app = Dash(__name__)

# Define the scope for Google Sheets API
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file",
         "https://www.googleapis.com/auth/drive"]

# Authenticate Google Sheets client
credentials = ServiceAccountCredentials.from_json_keyfile_name("bowling-440309-db098bc08118.json", scope)
client = gspread.authorize(credentials)

# Load data from Google Sheets
spreadsheet = client.open("Bowling-liga")
worksheet = spreadsheet.sheet1
data = worksheet.get_all_records()
df = pd.DataFrame(data)

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
avg_scores = grouped.mean()
min_scores = grouped.min()
max_scores = grouped.max()

round_columns = [col for col in df.columns if 'kolo' in col and 'Skóre' not in col]
round_results = df[round_columns].astype(str).apply(pd.Series.value_counts).sum(axis=1).fillna(0)
round_results_percentage = (round_results / round_results.sum()) * 100

df = df.sort_values(by=['Hráč', 'absolute_game_position'])

# Calculate the rank for each player at each absolute game position
df['Rank'] = df.groupby('absolute_game_position')['Skóre 10. kolo'].rank(ascending=False, method='min')


# COLOUR ETC
colors = plotly.colors.qualitative.Plotly  # Use a predefined color set from Plotly
player_list = df['Hráč'].unique()
color_dict = {player: colors[i % len(colors)] for i, player in enumerate(player_list)}



# Dash Layout with CSS styling and Graphs
app.layout = html.Div([
    # Bowling Title
    html.Div([
        html.H1("Bowling", style={'color': 'white', 'fontSize': '3.5em', 'marginBottom': '20px'}),
    ], style={'textAlign': 'center'}),

    # Last Game Data label and data box
    html.Div([
        html.Div("Last Game Data", style={'color': 'white', 'fontSize': '1.2em', 'marginBottom': '5px'}),
        html.Div([
            html.Div([
                html.Span(f"Venue: {venue}", style={'marginRight': '20px'}),
                html.Span(f"Date: {date}", style={'marginRight': '20px'}),
                html.Span(f"Number of rounds: {num_rounds}", style={'marginRight': '20px'}),
            ], style={'marginBottom': '10px'}),
            html.Div([
                html.Span(f"Top player: {max_sum_score['Hráč']} - {max_sum_score['Skóre 10. kolo']} points", style={'marginRight': '20px'}),
                html.Span(f"Top round: {max_score['Hráč']} - {max_score['Skóre 10. kolo']} points", style={'marginRight': '20px'}),
                html.Span(f"Average team score: {team_avg_score:.2f}", style={'marginRight': '20px'}),
                html.Span(f"Top strikes: {top_strikes['Hráč']} - {top_strikes['Num Strikes']} strikes"),
            ]),
        ], style={
            'backgroundColor': '#2B3E50', 'color': 'white', 'fontSize': '1.1em', 'padding': '15px 20px',
            'borderRadius': '10px', 'marginBottom': '20px'
        }),
    ], style={'textAlign': 'center', 'marginBottom': '30px'}),

    # Filter toggle and dropdown
    html.Div([
        html.Div([
            html.Label("Filter By:", style={'color': 'white', 'fontSize': '1.1em', 'marginRight': '10px'}),
            dcc.Tabs(
                id='filter-tabs',
                value='Team',
                children=[
                    dcc.Tab(label='Player', value='Player', style={'color': 'white'}),
                    dcc.Tab(label='Team', value='Team', style={'color': 'white'})
                ],
                colors={'border': '#2B3E50', 'primary': 'gray', 'background': '#2B3E50'},
                style={'width': '150px'}
            )
        ], style={'display': 'inline-block', 'verticalAlign': 'top'}),

        html.Div([
            html.Label("Select Player:", style={'color': 'white', 'fontSize': '1.1em', 'marginRight': '10px'}),
            dcc.Dropdown(
                id='player-dropdown',
                options=[{'label': player, 'value': player} for player in players],
                placeholder="Select...",
                style={'width': '200px', 'fontSize': '1em'}
            ),
        ], id='player-dropdown-container', style={'display': 'none', 'marginLeft': '20px'}),
    ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'flex-start', 'padding': '10px 0'}),

    # Graphs container for Team or Player tab
    html.Div(id='graphs-container', style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'space-around'})
], style={'backgroundColor': '#1A1A2E', 'minHeight': '100vh', 'padding': '20px'})

# Callback for showing graphs based on tab selection and player filter
@app.callback(
    Output('graphs-container', 'children'),
    [Input('filter-tabs', 'value'),
     Input('player-dropdown', 'value')]
)
def display_graphs(tab, selected_player):
    if tab == 'Player' and selected_player:
        return [
            dcc.Graph(id='strikes-evolution-plot', figure=generate_strikes_evolution_plot(selected_player), style={'width': '48%'}),
            dcc.Graph(id='position-over-time-plot', figure=generate_position_over_time_plot(selected_player), style={'width': '48%'}),
            dcc.Graph(id='spares-evolution-plot', figure=generate_spares_evolution_plot(selected_player), style={'width': '48%'}),
            dcc.Graph(id='round-distribution-plot', figure=generate_round_distribution_plot(selected_player), style={'width': '48%'})
        ]
    elif tab == 'Team':
        return [
            dcc.Graph(id='cumulative-score-plot', figure=generate_cumulative_score_plot(color_dict), style={'width': '48%'}),
            dcc.Graph(id='absolute-game-score-plot', figure=generate_absolute_game_score_plot(color_dict), style={'width': '48%'}),
            dcc.Graph(id='avg-min-max-plot', figure=generate_avg_min_max_plot(), style={'width': '48%'}),
            dcc.Graph(id='result-distribution-pie', figure=generate_result_distribution_pie(), style={'width': '48%'})
        ]
    else:
        return []

# Function to generate the cumulative score plot
def generate_cumulative_score_plot(color_dict):
    fig = go.Figure()
    for player in df['Hráč'].unique():
        player_data = df[df['Hráč'] == player]
        avg_scores = player_data.groupby('Pořadové č. hry')['Skóre 10. kolo'].mean()
        min_scores = player_data.groupby('Pořadové č. hry')['Skóre 10. kolo'].min()
        max_scores = player_data.groupby('Pořadové č. hry')['Skóre 10. kolo'].max()

        color = color_dict[player]  # Use the color from the dictionary
        rgb_color = plotly.colors.hex_to_rgb(color)  # Convert hex color to RGB tuple

        fig.add_trace(go.Scatter(
            x=avg_scores.index,
            y=avg_scores,
            mode='lines+markers',
            name=player,
            line=dict(width=2, color=color)
        ))

        fig.add_trace(go.Scatter(
            x=avg_scores.index,
            y=min_scores,
            mode='lines',
            line=dict(width=0),
            showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=avg_scores.index,
            y=max_scores,
            mode='lines',
            fill='tonexty',
            fillcolor=f'rgba({rgb_color[0]},{rgb_color[1]},{rgb_color[2]},0.1)',  # Correct rgba format
            line=dict(width=0),
            showlegend=False
        ))

    fig.update_layout(
        title="Development of Average Game Score by Game Order for Each Player",
        xaxis_title="Game Order (Pořadové č. hry)",
        yaxis_title="Average Score",
        legend_title="Player"
    )
    return fig

# Function to generate the absolute game score plot
def generate_absolute_game_score_plot(color_dict):
    fig = go.Figure()
    for player in df['Hráč'].unique():
        player_data = df[df['Hráč'] == player]
        color = color_dict[player]  # Use the color from the dictionary

        fig.add_trace(go.Scatter(
            x=player_data['absolute_game_position'],
            y=player_data['Skóre 10. kolo'],
            mode='lines+markers',
            name=player,
            line=dict(color=color)
        ))

    fig.update_layout(
        title="Scores for Each Player by Absolute Game Order",
        xaxis_title="Absolute Game Order",
        yaxis_title="Score",
        legend_title="Player"
    )
    return fig

def generate_avg_min_max_plot():
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=avg_scores.index,
        y=avg_scores,
        mode='lines+markers',
        name='Average Score',
        line=dict(color='blue')
    ))
    fig.add_trace(go.Scatter(
        x=avg_scores.index,
        y=min_scores,
        fill=None,
        mode='lines',
        line=dict(color='lightgray', width=0),
        showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=avg_scores.index,
        y=max_scores,
        fill='tonexty',
        mode='lines',
        line=dict(color='lightgray', width=0),
        showlegend=True,
        name='Min-Max Range'
    ))
    fig.update_layout(
        title="Average Scores with Min-Max Range by Absolute Game Order",
        xaxis_title="Absolute Game Order",
        yaxis_title="Average Score",
        legend_title="Score Type"
    )
    return fig

def generate_result_distribution_pie():
    fig = go.Figure(
        go.Pie(
            labels=round_results_percentage.index,
            values=round_results_percentage,
            hole=0.3
        )
    )
    fig.update_layout(
        title="Distribution of Round Results"
    )
    return fig

# Graph generation functions for individual players
def generate_round_distribution_plot(player):
    df_player = df[df['Hráč'] == player]
    round_columns = [col for col in df_player.columns if 'kolo' in col and 'Skóre' not in col]
    round_results = df_player[round_columns].astype(str).apply(pd.Series.value_counts).sum(axis=1).fillna(0)
    round_results_percentage = (round_results / round_results.sum()) * 100
    fig = px.pie(values=round_results_percentage, names=round_results_percentage.index,
                 title=f'Distribution of Round Results for Player {player}', hole=0.3)
    return fig

def generate_strikes_evolution_plot(player):
    df_player = df[df['Hráč'] == player]
    strike_columns_all = [col for col in df_player.columns if 'kolo' in col and 'Skóre' not in col]
    df_player['Total_Strikes'] = df_player[strike_columns_all].apply(lambda x: (x == 'Strike').sum(), axis=1)
    fig = go.Figure(go.Scatter(x=df_player['absolute_game_position'], y=df_player['Total_Strikes'],
                               mode='lines+markers', name='Strikes Over Time'))
    fig.update_layout(title=f'Evolution of Number of Strikes Over Time for Player {player}',
                      xaxis_title='Absolute Game Position', yaxis_title='Number of Strikes', template='plotly_white')
    return fig

def generate_spares_evolution_plot(player):
    df_player = df[df['Hráč'] == player]
    strike_columns_all = [col for col in df_player.columns if 'kolo' in col and 'Skóre' not in col]
    df_player['Total_Spares'] = df_player[strike_columns_all].apply(lambda x: (x == 'Spare').sum(), axis=1)
    fig = go.Figure(go.Scatter(x=df_player['absolute_game_position'], y=df_player['Total_Spares'],
                               mode='lines+markers', name='Spares Over Time'))
    fig.update_layout(title=f'Evolution of Number of Spares Over Time for Player {player}',
                      xaxis_title='Absolute Game Position', yaxis_title='Number of Spares', template='plotly_white')
    return fig

def generate_position_over_time_plot(player):
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

# Toggle player dropdown visibility
@app.callback(
    Output('player-dropdown-container', 'style'),
    Input('filter-tabs', 'value')
)
def toggle_player_dropdown(filter_value):
    if filter_value == 'Player':
        return {'display': 'inline-block', 'marginLeft': '20px'}
    else:
        return {'display': 'none'}

if __name__ == '__main__':
    app.run_server(debug=True)
