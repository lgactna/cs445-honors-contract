"""
Various shared routines for generating graphs.
"""

import copy

from typing import Callable, Tuple
import plotly.graph_objects as go
import networkx as nx
import plotly

import global_state

DEFAULT_FIGURE_LAYOUT = go.Layout(
    showlegend=False,
    hovermode="closest",
    margin=dict(b=20, l=5, r=5, t=40),
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    height=800,
)


def create_figure_from_graph(
    graph: nx.Graph,
    positions = None,
    layout: Callable[..., dict[int, tuple[float, float]]] = nx.spring_layout,
    figure_layout: go.Layout = DEFAULT_FIGURE_LAYOUT,
) -> plotly.graph_objs.Figure:
    """
    Generate a Plotly figure from a NetworkX graph object.
    """
    # Create absolute positioning of nodes based on the spring layout; note that
    # the official example at https://plotly.com/python/network-graphs/ doesn't
    # do this, because geometric graphs are already based on absolute positions.
    #
    # For pretty much every other graph, we have to do the positioning of nodes
    # ourselves. In turn, we use a layout callable.
    if not positions:
        positions = layout(graph)

    # Create edge listing
    edge_x = []
    edge_y = []
    for node_idx_1, node_idx_2 in graph.edges():
        x0, y0 = positions[node_idx_1]
        x1, y1 = positions[node_idx_2]
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

    # Generate a scatter plot composed of only the edges.
    edge_trace = go.Scatter(
        name="edge_trace",
        x=edge_x,
        y=edge_y,
        line=dict(width=0.5, color="#888"),
        hoverinfo="none",
        mode="lines",
    )

    # Get the absolute positions of all nodes from the layout.
    node_x = []
    node_y = []
    for node in graph.nodes():
        x, y = positions[node]
        node_x.append(x)
        node_y.append(y)

    # Generate a scatter plot from the nodes.
    node_trace = go.Scatter(
        name="node_trace",
        texttemplate="%{customdata}",
        textposition='top center',
        customdata=[str(x) for x in graph.nodes()],
        mode="markers+text",
        hoverinfo="text",
        x=node_x,
        y=node_y,
        marker=dict(
            showscale=False,
            # colorscale options
            #'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
            #'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
            #'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |
            colorscale="Hot",
            reversescale=True,
            color=[],
            size=10,
            line_width=2,
            colorbar=dict(
                titleside='right'
            )
        ),
    )

    # Create the actual graph object. Overlay the node and the edge figure
    # on top of each other to form a single network graph.
    fig = go.Figure(data=[edge_trace, node_trace], layout=figure_layout)

    return fig

def color_nodes_by_role(
    graph: nx.Graph,
    fig: plotly.graph_objs.Figure,
    victim_node: int,
    attacker_nodes: list[int],
) -> plotly.graph_objs.Figure:
    """
    Recolor the "reconstructed" graph from a node appending algorithm graph.
    
    :param graph: The marked graph passed through `simul_utils.simulate_transmissions()`.
    :param fig: The figure to update.
    :param victim_node: The victim node. Marked blue.
    :param attacker_nodes: The attacker nodes. Marked red.
    """
    # Color and label nodes based on the number of adjacencies that they have.
    # The actual color is decided automatically based on the value of each node
    # passed through node_trace.marker.color; the color scheme is also predefined
    # in create_graph.
    node_values = []
    node_text = []
    for node in graph.nodes():
        node_value = ""
        node_label = ""
        
        if node == victim_node:
            node_value = "blue"
            node_label = "Victim"
        elif node in attacker_nodes:
            node_value = "red"
            node_label = "Attacker"
        elif graph.nodes[node]["times_used"] == 0:
            node_value = "gray"
            node_label = "Unused router"
        else:
            node_value = "white"
            node_label = f"Router (used {graph.nodes[node]['times_used']} times)"
        
        node_values.append(node_value)
        node_text.append(node_label)

    # Update the node component of the graph by name
    # https://community.plotly.com/t/need-to-target-a-specific-trace-by-name-when-use-update-traces-s-selector/63151
    #
    # This code is equivalent to the original, where the traces are accessed directly:
    #   node_trace.marker.color = node_adjacencies
    #   node_trace.text = node_text
    fig.update_traces(
        {
            "text": node_text,
            "marker": {
                "color": node_values,
                "showscale": False,
            },
            "hovertemplate": f"%{{text}}",
        },
        selector = {'name':'node_trace'}
    )
    
    return fig 

def color_nodes_by_property(graph: nx.Graph, fig: plotly.graph_objs.Figure, property: str) -> plotly.graph_objs.Figure:
    """
    Color nodes on a figure generated by `create_figure_from_graph` based on the
    number of nodes that are adjacent to it.
    
    The graph represented by `fig` and `graph` itself must be identical.
    """
    # Color and label nodes based on the number of adjacencies that they have.
    # The actual color is decided automatically based on the value of each node
    # passed through node_trace.marker.color; the color scheme is also predefined
    # in create_graph.
    node_values = []
    node_text = []
    for node in graph.nodes():
        val = graph.nodes[node][property]
        
        node_values.append(val)
        node_text.append(f"{property}={val}")


    # Update the node component of the graph by name
    # https://community.plotly.com/t/need-to-target-a-specific-trace-by-name-when-use-update-traces-s-selector/63151
    #
    # This code is equivalent to the original, where the traces are accessed directly:
    #   node_trace.marker.color = node_adjacencies
    #   node_trace.text = node_text
    fig.update_traces(
        {
            "text": node_text,
            "marker": {
                "color": node_values,
                "showscale": True,
                "colorbar": {
                    "title": property,
                    "thickness":15,
                    "xanchor":"left",
                    "titleside":"right",
                }
            },
            "hovertemplate": f"%{{text}}",
        },
        selector = {'name':'node_trace'}
    )
    
    return fig
    
def color_nodes_by_adjacency(graph: nx.Graph, fig: plotly.graph_objs.Figure) -> plotly.graph_objs.Figure:
    """
    Color nodes on a figure generated by `create_figure_from_graph` based on the
    number of nodes that are adjacent to it.
    
    The graph represented by `fig` and `graph` itself must be identical.
    """
    
    # Color and label nodes based on the number of adjacencies that they have.
    # The actual color is decided automatically based on the value of each node
    # passed through node_trace.marker.color; the color scheme is also predefined
    # in create_graph.
    node_adjacencies = []
    node_text = []
    for node, adjacencies in enumerate(graph.adjacency()):
        node_adjacencies.append(len(adjacencies[1]))
        node_text.append(f"Connections: {len(adjacencies[1])}")


    # Update the node component of the graph by name
    # https://community.plotly.com/t/need-to-target-a-specific-trace-by-name-when-use-update-traces-s-selector/63151
    #
    # This code is equivalent to the original, where the traces are accessed directly:
    #   node_trace.marker.color = node_adjacencies
    #   node_trace.text = node_text
    fig.update_traces(
        {
            "text": node_text,
            "textposition": 'top center',
            "marker": {
                "color": node_adjacencies,
                "showscale": True,
                "colorbar": {
                    "title": "Number of connections",
                    "thickness": 15,
                    "xanchor":"left",
                    "titleside":"right",
                }
            }
        },
        selector = {'name':'node_trace'}
    )
    
    return fig

def rebuild_node_sampling_paths(graph: nx.Graph, fig: plotly.graph_objs.Figure, victim_node: int) -> plotly.graph_objs.Figure:
    """
    Perform path reconstruction according to the node sampling algorithm.
    
    For obvious reasons, this will give you a rather inaccurate representation
    of how things actually work.
    
    You should call this after coloring the nodes.
    """
    # Copy the figure
    fig_2 = copy.deepcopy(fig)
    
    # First, destroy the edges currently present in the figure by outright
    # removing the edge traces on the original figure (more accurately,
    # hiding them since this apparently isn't really all that easy)
    for i, trace in enumerate(fig.data):
        if 'name' in trace and trace['name'] == 'edge_trace':
            fig_2.data[i].visible = False
    
    # Now perform the path reconstruction exactly as stated by the paper
    counts = {}
    for node in graph.nodes():
        # print(f"{node=}, {graph.nodes[node]['times_marked']=}")
        if graph.nodes[node]['times_marked'] != 0:
            counts[node] = graph.nodes[node]['times_marked']
    counts = {k: v for k, v in sorted(counts.items(), key=lambda item: item[1])}
    
    # Draw edges according to the order of keys (node indices) in `counts`, 
    # including one edge to the victim node from the most frequent node
    ordered_nodes = list(counts.keys()) + [victim_node]
    edge_x = []
    edge_y = []
    for i in range(len(ordered_nodes)-1):
        a = ordered_nodes[i]
        b = ordered_nodes[i+1]
        
        # print(f"{a=}, {b=}")
        
        x0, y0 = global_state.POSITIONS[a]
        x1, y1 = global_state.POSITIONS[b]
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)
        
    # Generate a scatter plot composed of only the edges.
    edge_trace = go.Scatter(
        name="node_sampling_edge_trace",
        x=edge_x,
        y=edge_y,
        line=dict(width=0.5, color="#888"),
        hoverinfo="none",
        mode="lines",
    )
    
    # Add the new trace to the figure
    fig_2.add_trace(edge_trace)
    
    # Return
    return fig_2
    
    
    
    
    