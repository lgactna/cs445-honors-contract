import dash
import dash_bootstrap_components as dbc
from dash import html, Input, Output, callback

# This is registered as the homepage with path `/`, else accessing the server
# yields a 404 until you click on one of the pages
dash.register_page(__name__, name="Edge sampling", group="Simulations", order=2)

layout = html.Div(
    [
        html.H1("Edge sampling"),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.P(
                            "Use this to update the global ranked player statistics. You are limited"
                            " to retrieving this information once per day based on the most recent"
                            " timestamps available in the databse. Unranked players are not included."
                            " This will take about two minutes - be patient!"
                        ),
                        dbc.Button(
                            "Request global statistics",
                            id="request-global-update-btn",
                            style={"margin-bottom": "10px"},
                        ),
                    ],
                    width=6,
                    md=12,
                ),
                dbc.Col(
                    [
                        html.B("Request results will appear below."),
                        dbc.Spinner(html.Div(id="request-result")),
                    ],
                    width=6,
                    md=12,
                ),
            ]
        ),
    ]
)
