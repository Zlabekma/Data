

import pandas as pd
import plotly.graph_objs as go
import plotly.express as px

# Function to generate the cumulative score plot
def generate_cumulative_score_plot(df,color_dict):
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


def generate_total_score_dist(df,binsize):
    start = int(df['Skóre 10. kolo'].min());
    end = int(df['Skóre 10. kolo'].max()) + binsize;

    # Create bin labels
    bin_labels = [f"{i}-{i+binsize-1}" for i in range(start, end, binsize)];

    fig = go.Figure(data=[go.Histogram(
        x=df['Skóre 10. kolo'],
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
        title='Scores Distribution',
        xaxis_title='Score Ranges',
        yaxis_title='Frequency',
        xaxis=dict(
            tickmode='array',
            tickvals=[i + binsize / 2 for i in range(start, end, binsize)],
            ticktext=bin_labels
        )
    )
    return fig

# Function to generate the absolute game score plot
def generate_absolute_game_score_plot(df,color_dict):
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

def generate_avg_min_max_plot(avg_min_max_scores):
    avg_scores = avg_min_max_scores[0]
    min_scores = avg_min_max_scores[1]
    max_scores = avg_min_max_scores[2]
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

def generate_result_distribution_pie(round_results_percentage):
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
