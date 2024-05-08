from textwrap import dedent
import copy

from dash import html, Input, Output, callback, dcc
from typing import Callable, Tuple
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
dash.register_page(__name__, path="/", name="Node append", group="Simulations", order=0)

def generate_options():
    # Regenerate this every time the page is loaded
    
    return dbc.Form(
        [
            dbc.Label("Packets to send", html_for="slider-nappend-packets"),   
            dcc.Slider(0, 5000, 10, value=100, id='slider-nappend-packets', marks=None, tooltip={"placement": "bottom", "always_visible": True}),
            dbc.Label("Index of victim node", html_for="slider-nappend-victim"),   
            dcc.Slider(0, global_state.GRAPH_PARAMETERS.n-1, 1, value=0, id='slider-nappend-victim', marks=None, tooltip={"placement": "bottom", "always_visible": True}),
            dbc.Label("Indices of attackers", html_for="dropdown-nappend-attackers"), 
            dcc.Dropdown(
            {str(i): i for i in range(global_state.GRAPH_PARAMETERS.n)},
            ['1'],
            multi=True,
            id="dropdown-nappend-attackers"
            )
        ]
    )

layout = html.Div(
    [
        html.H1("Node append"),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.B("Network"),
                        dbc.Tabs(
                            [
                                dbc.Tab(
                                    dbc.Spinner(dcc.Graph(id="graph-nappend-base")),
                                    label="Base graph"
                                ),
                                dbc.Tab(
                                    [
                                        dbc.Spinner(dcc.Graph(id="graph-nappend-new"))
                                    ],
                                    label="Reconstructed path to attackers"
                                )
                            ],
                            id="tabs-nappend"
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
                                        html.Div(generate_options(), id="nappend-options-dummy")
                                    ],
                                    width=12,
                                    style={"height": "400px"}
                                ),
                                dbc.Col(
                                    [
                                        html.B("Results"),
                                        dbc.Spinner(dcc.Markdown(id="md-nappend-results"))
                                    ],
                                    width=12,
                                    style={"height": "400px"}
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
    Output("nappend-options-dummy", "children"),
    Input("nappend-options-dummy", "children")
)
def update_dummy(_):
    return generate_options()

@callback(
    Output("graph-nappend-base", "figure"),
    Output("graph-nappend-new", "figure"),
    Output("md-nappend-results", "children"),
    Input("slider-nappend-victim", 'value'),
    Input("dropdown-nappend-attackers", 'value'),
    Input("slider-nappend-packets", 'value')
)
def update_output(
    victim_node: int, 
    attackers: list[str],
    packets: int
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
    result = simul_utils.simulate_transmissions(graph, victim_node, attackers, 1, packets)
    
    # Color the copy of the figure based on the simulation results.
    fig = graph_utils.color_nodes_by_property(result.graph, fig, "times_used")
    fig_2 = copy.deepcopy(fig)
    fig_2 = graph_utils.color_nodes_by_role(result.graph, fig_2, victim_node, attackers)
    fig_2 = graph_utils.rebuild_node_append_paths(result.graph, fig_2, victim_node, global_state.POSITIONS)
    
    # Spit out the simulation results.
    res = dedent(
        f"""
        - Number of packets sent: {result.packets_sent}
        - Total number of intermediate routers: {result.intermediate_routers}
        - Additional bytes of overhead: {result.nappend_overhead}
        
        ---
        
        The reconstructed graph for node appending can be viewed by clicking on
        "Reconstructed path to attackers" on the left. Elements are colored
        as follows:
        - **Blue** is the victim node.
        - **Red** are attacker nodes.
        - **White** nodes are routers on at least one path to from an attacker to the victim.
        - **Gray** nodes are routers not involved in routing attacker traffic.
        """
    ).strip()
    
    return fig, fig_2, res