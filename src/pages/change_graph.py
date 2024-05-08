import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output
import plotly

import global_state
import graph_utils

# This is registered as the homepage with path `/`, else accessing the server
# yields a 404 until you click on one of the pages
dash.register_page(__name__, name="Change graph", group="Options", order=3)

layout = html.Div(
    [
        html.H1("Change graph"),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.P(
                            "Use this form to change the graph used across all"
                            " pages. The generated graph will be a Watts-Strogatz"
                            " small world graph based on the parameters provided"
                            " below."
                        ),
                        html.B("Current network"),
                        dbc.Spinner(dcc.Graph(id="graph-options", figure=global_state.FIGURE)),
                    ],
                    width=12,
                    xxl=8,
                ),
                dbc.Col(
                    [
                        html.B("Graph options"),
                        dbc.Form(
                            [
                                dbc.Label("Number of nodes (n)", html_for="slider-options-nodes"),   
                                dcc.Slider(5, 200, 1, value=global_state.GRAPH_PARAMETERS.n, id='slider-options-nodes', marks=None, tooltip={"placement": "bottom", "always_visible": True}),
                                dbc.Label("Minimum neighbors per node (k)", html_for="slider-options-neighbors"),   
                                dcc.Slider(2, 10, 1, value=global_state.GRAPH_PARAMETERS.k, id='slider-options-neighbors', marks=None, tooltip={"placement": "bottom", "always_visible": True}),
                                dbc.Label("Probability of connection (p)", html_for="slider-options-probability"),   
                                dcc.Slider(0, 1, 0.01, value=global_state.GRAPH_PARAMETERS.p, id='slider-options-probability', marks=None, tooltip={"placement": "bottom", "always_visible": True}),
                                dbc.Button(
                                    "Generate new graph",
                                    id="button-change-graph",
                                    style={"margin-bottom": "10px"},
                                ),
                            ]
                        )
                    ],
                    width=12,
                    xxl=4,
                ),
            ]
        ),
    ]
)

cur_clicks = 0
figure = graph_utils.color_nodes_by_adjacency(global_state.GRAPH, global_state.FIGURE)

@callback(
    Output("graph-options", "figure"),
    Input('button-change-graph', 'n_clicks'),
    Input('slider-options-nodes', 'value'),
    Input('slider-options-neighbors', 'value'),
    Input('slider-options-probability', 'value'),
    prevent_inital_call=True
)
def update_graph(clicks, n, k, p) -> plotly.graph_objs.Figure:
    global cur_clicks, figure
    # If the button hasn't actually been pressed, do nothing.
    if clicks == cur_clicks:
        return figure
    else:
        cur_clicks = clicks
    
    # Generate new graph based on parameters and update the global state
    figure = global_state.update_global_state(n, k, p)
    figure = graph_utils.color_nodes_by_adjacency(global_state.GRAPH, figure)
    
    return figure