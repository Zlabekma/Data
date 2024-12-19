from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import plotly.colors
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

import utils

# Initialize the Dash app
app = Dash(__name__)

# Define the scope for Google Sheets API
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file",
         "https://www.googleapis.com/auth/drive"]

# Authenticate Google Sheets client

#local
#credentials = ServiceAccountCredentials.from_json_keyfile_name("GOOGLE_SHEETS_KEY.JSON", scope)
# non local 
credentials = ServiceAccountCredentials.from_json_keyfile_name('/etc/secrets/GOOGLE_SHEETS_KEY.JSON', scope)

client = gspread.authorize(credentials)


# Load data from Google Sheets
spreadsheet = client.open("Bowling-liga")
worksheet = spreadsheet.sheet1
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# Use the function from utils.data_prep
data_dict = utils.data_prep.prepare_data(df)

# Extract variables from data_dict
df = data_dict["df"]
players = data_dict["players"]
venue = data_dict["venue"]
date = data_dict["date"]
num_rounds = data_dict["num_rounds"]
max_sum_score = data_dict["max_sum_score"]
max_score = data_dict["max_score"]
team_avg_score = data_dict["team_avg_score"]
top_strikes = data_dict["top_strikes"]
avg_min_max_scores = data_dict["avg_min_max_scores"]
round_results_percentage = data_dict["round_results_percentage"]
color_dict = data_dict["color_dict"]






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

    # Box for Player or Team
    html.Div(id='selection-overview-box', style={
        'backgroundColor': '#2B3E50', 'color': 'white', 'fontSize': '1.1em', 'padding': '15px 20px',
        'borderRadius': '10px', 'marginBottom': '20px', 'textAlign': 'left'
    }),

    # Graphs container for Team or Player tab
    html.Div(id='graphs-container', style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'space-around'})
], style={'backgroundColor': '#1A1A2E', 'minHeight': '100vh', 'padding': '20px'})

# Callback to update the new box content based on tab selection and player selection
@app.callback(
    Output('selection-overview-box', 'children'),
    [Input('filter-tabs', 'value'), Input('player-dropdown', 'value')]
)

def update_selection_overview(tab, selected_player):
    if tab == 'Player' and selected_player:
        best_round = df[df['Hráč'] == selected_player]['Skóre 10. kolo'].max()
        worst_round = df[df['Hráč'] == selected_player]['Skóre 10. kolo'].min()
        avg_score = df[df['Hráč'] == selected_player]['Skóre 10. kolo'].mean().round()

        return html.Div([
            html.Span(f"Selected Player: {selected_player}", style={'fontWeight': 'bold', 'marginRight': '15px'}),
            html.Span(f"Best round: {best_round}", style={'marginRight': '15px'}),
            html.Span(f"Worst round: {worst_round}", style={'marginRight': '15px'}),
            html.Span(f"Average score: {avg_score}", style={'marginRight': '15px'})
        ], style={'display': 'flex', 'alignItems': 'center', 'flexWrap': 'wrap'})

    else:
        top_team_player = df.loc[df['Skóre 10. kolo'].idxmax(), 'Hráč']
        top_team_score = df['Skóre 10. kolo'].max()
        worst_team_player = df.loc[df['Skóre 10. kolo'].idxmin(), 'Hráč']
        worst_team_score = df['Skóre 10. kolo'].min()
        avg_team_score = df['Skóre 10. kolo'].mean().round()
        return html.Div([
            html.Span("Team Overview: Duto Duto", style={'fontWeight': 'bold', 'marginRight': '15px'}),
            html.Span(f"Top team score: {top_team_player} - {top_team_score} points", style={'marginRight': '15px'}),
            html.Span(f"Worst team score: {worst_team_player} - {worst_team_score} points", style={'marginRight': '15px'}),
            html.Span(f"Average team score: {avg_team_score}")
        ], style={'display': 'flex', 'alignItems': 'center', 'flexWrap': 'wrap'})




# Callback for showing graphs based on tab selection and player filter
@app.callback(
    Output('graphs-container', 'children'),
    [Input('filter-tabs', 'value'),
     Input('player-dropdown', 'value')]
)
def display_graphs(tab, selected_player):
    if tab == 'Player' and selected_player:
        return [
            dcc.Graph(id='strikes-spare-evolution-plot', figure=utils.graph_player.generate_combined_strikes_and_spares_evolution_plot(df,selected_player), style={'width': '48%'}),
            dcc.Graph(id='position-over-time-plot', figure=utils.graph_player.generate_player_score_dist(df,selected_player, 10), style={'width': '48%'}),
            dcc.Graph(id='spares-evolution-plot', figure=utils.graph_player.generate_position_over_time_plot(df,selected_player), style={'width': '48%'}),
            dcc.Graph(id='round-distribution-plot', figure=utils.graph_player.generate_round_distribution_plot(df,selected_player), style={'width': '48%'})
        ]
    elif tab == 'Team':
        return [
            dcc.Graph(id='absolute-game-score-plot', figure=utils.graph_team.generate_absolute_game_score_plot(df,color_dict), style={'width': '48%'}),
            dcc.Graph(id='total_total_score_dist', figure=utils.graph_team.generate_total_score_dist(df,10), style={'width': '48%'}),
            dcc.Graph(id='avg-min-max-plot', figure=utils.graph_team.generate_avg_min_max_plot(avg_min_max_scores), style={'width': '48%'}),
            dcc.Graph(id='result-distribution-pie', figure=utils.graph_team.generate_result_distribution_pie(round_results_percentage), style={'width': '48%'})
        ]
    else:
        return []


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


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)

#if __name__ == '__main__':
#    app.run_server(debug=True)