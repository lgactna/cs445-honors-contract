from textwrap import dedent
import copy

from dash import html, Input, Output, callback, dcc
from typing import Callable, Tuple
import pandas as pd
import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import networkx as nx
import plotly

import graph_utils
import simul_utils
import global_state

# This is registered as the homepage with path `/`, else accessing the server
# yields a 404 until you click on one of the pages
dash.register_page(__name__, name="Edge sampling", group="Simulations", order=2)

def generate_options():
    # Regenerate this every time the page is loaded
    
    return dbc.Form(
        [
            dbc.Label("Packets to send", html_for="slider-esample-packets"),   
            dcc.Slider(0, 5000, 10, value=100, id='slider-esample-packets', marks=None, tooltip={"placement": "bottom", "always_visible": True}),
            dbc.Label("Index of victim node", html_for="slider-esample-victim"),   
            dcc.Slider(0, global_state.GRAPH_PARAMETERS.n-1, 1, value=0, id='slider-esample-victim', marks=None, tooltip={"placement": "bottom", "always_visible": True}),
            dbc.Label("Indices of attackers", html_for="dropdown-esample-attackers"), 
            dcc.Dropdown(
            {str(i): i for i in range(global_state.GRAPH_PARAMETERS.n)},
            ['1'],
            multi=True,
            id="dropdown-esample-attackers"
            ),
            dbc.Label("Marking probability (p)", html_for="slider-esample-p"),   
            dcc.Slider(0, 1, 0.01, value=0.5, id='slider-esample-p', marks=None, tooltip={"placement": "bottom", "always_visible": True}),
        ]
    )

layout = html.Div(
    [
        html.H1("Edge sampling"),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.B("Network"),
                        dbc.Tabs(
                            [
                                dbc.Tab(
                                    dbc.Spinner(dcc.Graph(id="graph-esample-base")),
                                    label="Base graph"
                                ),
                                dbc.Tab(
                                    [
                                        dbc.Spinner(dcc.Graph(id="graph-esample-new"))
                                    ],
                                    label="Reconstructed path to attackers"
                                )
                            ],
                            id="tabs-esample"
                        )
                    ],
                    width=12,
                    xxl=8,
                ),
                dbc.Col(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.B("Options"),
                                        html.Div(generate_options(), id="esample-options-dummy")
                                    ],
                                    width=12,
                                    #style={"height": "50vh"}
                                ),
                                dbc.Col(
                                    [
                                        html.B("Results"),
                                        dbc.Spinner(id="esample-results")
                                    ],
                                    width=12
                                    
                                )                                
                            ]
                        ),
                    ],
                    width=12,
                    xxl=4,
                ),
            ]
        ),
    ]
)

@callback(
    Output("esample-options-dummy", "children"),
    Input("esample-options-dummy", "children")
)
def update_dummy(_):
    return generate_options()

@callback(
    Output("graph-esample-base", "figure"),
    Output("graph-esample-new", "figure"),
    Output("esample-results", "children"),
    Input("slider-esample-victim", 'value'),
    Input("dropdown-esample-attackers", 'value'),
    Input("slider-esample-packets", 'value'),
    Input("slider-esample-p", 'value')
)
def update_output(
    victim_node: int, 
    attackers: list[str],
    packets: int,
    p
) -> Tuple[
    plotly.graph_objs.Figure,
    plotly.graph_objs.Figure,
    str
]:
    # Default to at least two attackers, even if none is defined.
    if not attackers:
        attackers = ["0", "1"]

    # Cast all attackers to integers.
    attackers = [int(x) for x in attackers]
    
    if victim_node in attackers:
        attackers.remove(victim_node)

    # Copy the global figure.
    fig = copy.deepcopy(global_state.FIGURE)
    
    # Create a copy of the global graph. This allows attributes to be reused,
    # since all of our attributes are not containers (and therefore are properly
    # copied with new references).
    graph = global_state.GRAPH.copy()
    
    # Carry out the simulation.
    result = simul_utils.simulate_transmissions(graph, victim_node, attackers, p, packets)
    
    # Color the copy of the figure based on the simulation results.
    fig = graph_utils.color_nodes_by_property(result.graph, fig, "times_used")
    fig_2 = copy.deepcopy(fig)
    fig_2 = graph_utils.color_nodes_by_property(result.graph, fig_2, "times_marked")
    fig_2 = graph_utils.rebuild_edge_sampling_paths(result.graph, fig_2, victim_node)
    
    # Spit out the simulation results.
    df: pd.DataFrame = nx.to_pandas_edgelist(result.graph)
    print(df)
    df['edge'] = df.apply(lambda x: f"({x['source']}, {x['target']})", axis=1)
    df = df[['edge', 'times_marked', 'times_used']]
    df = df.sort_values("times_marked", ascending=False)
    
    md_str = dedent(
        f"""
        - Number of packets sent: {result.packets_sent}
        - Total number of intermediate routers: {result.intermediate_routers}
        - Additional bytes of overhead (naive implementation): {result.esample_overhead}
        
        The reconstructed graph for node appending can be viewed by clicking on
        "Reconstructed path to attackers" on the left. The reconstructed edge
        sampling table is below.
        """
    ).strip()
    res_layout = [
        dcc.Markdown(md_str),
        dbc.Container(
            dash.dash_table.DataTable(df.to_dict('records'), [{"name": i, "id": i} for i in df.columns], sort_action='native'), 
            style={"height": "25vh", "overflow": "scroll"})
    ]
    
    
    return fig, fig_2, res_layout
