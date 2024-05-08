"""
State shared globally.

Not ideal, but I want the user to know that the same graph is being used across
the entire framework.
"""

import logging

from dataclasses import dataclass
import networkx as nx
import plotly

import graph_utils

logger = logging.getLogger(__name__)

@dataclass
class GraphParameters:
    n: int
    k: int
    p: float
    
    def to_ws_graph(self) -> nx.Graph:
        return nx.watts_strogatz_graph(self.n, self.k, self.p)

# The parameters for the currently active graph.
GRAPH_PARAMETERS: GraphParameters = None

# The active graph itself.
GRAPH: nx.Graph = None

# The current positions.
POSITIONS = None

# The active "base" figure.
FIGURE: plotly.graph_objs.Figure = None

def update_global_state(n: int, k: int, p: float) -> plotly.graph_objs.Figure:
    global GRAPH_PARAMETERS, GRAPH, FIGURE, POSITIONS
    
    while True:
        GRAPH_PARAMETERS = GraphParameters(n=n, k=k, p=p)
        GRAPH = GRAPH_PARAMETERS.to_ws_graph()
        POSITIONS = nx.spring_layout(GRAPH)
        
        if not nx.is_connected(GRAPH):
            logger.info("Need to regenerate graph, not connected")
            continue
        else:
            break
        
    FIGURE = graph_utils.create_figure_from_graph(GRAPH, POSITIONS)
    
    return FIGURE

update_global_state(20, 2, 0.75)