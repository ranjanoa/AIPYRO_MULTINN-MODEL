# Copyright © 2025 INNOMOTICS
# Interactive_plot_duna.py

import plotly.graph_objects as go
import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Output, Input
from flask import has_app_context
import config


def create_dash_app(flask_server):
    dash_app = dash.Dash(__name__, server=flask_server, url_base_pathname="/simulator/",
                         suppress_callback_exceptions=True)

    def get_df():
        # Stub: This requires a DB connection or CSV. For now, returns empty.
        return pd.DataFrame()

    def create_figure():
        return go.Figure().update_layout(
            plot_bgcolor='black', paper_bgcolor='black', font=dict(color='white'),
            annotations=[
                dict(text="Simulator data not connected.", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
                     font=dict(size=16, color='white'))]
        )

    dash_app.layout = html.Div([
        html.Div([html.H1("Digital Simulator", style={"color": "Black", "font-size": "30px", "text-align": "center"})],
                 style={'background-color': '#e1f000', 'padding': '10px'}),
        html.Div([dcc.Graph(id='plot', figure=create_figure(), style={'height': '90vh'})],
                 style={'background-color': 'black'}),
        html.Button("Refresh", id="reset-button", n_clicks=0,
                    style={"position": "fixed", "top": "50px", "right": "10px", "color": "cyan"})
    ])
    return dash_app