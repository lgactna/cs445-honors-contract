"""
Utility functions for performing simulations.
"""

import networkx as nx
import random
import logging
from dataclasses import dataclass
from typing import Union, Tuple

logger = logging.getLogger(__name__)

@dataclass
class SimulationResult:
    # The graph itself, with nodes annotated
    graph: nx.Graph
    
    # Overall statistics
    packets_sent: int
    intermediate_routers: int
    
    # The number of additional bytes beyond "normal", without any of the optimizations
    # described by Savage et al. This means that we assume a naive implementation
    # of the algorithms, such that:
    # - Node append adds an extra 4 bytes of data per element on the path, for
    #   each packet
    # - Node sampling adds an extra 4 bytes of data to each packet
    # - Edge sampling adds an extra 9 bytes of data to each packet
    #
    # The net result is that these are *not* true implementations of the sampling
    # algorithms described by Savage et al, and would not be compatible with
    # IPv4/IPv6.
    nappend_overhead: int  # Variable
    nsample_overhead: int  # == packets_sent * 4
    esample_overhead: int  # == packets_sent * 9
    
def initialize_graph(
    graph: nx.Graph
) -> nx.Graph:
    """
    Return an initialized graph for simulation.

    If the graph is undirected, the graph is converted to a digraph.
    The original graph is not modified.

    :param graph: The graph to initialize.
    """
    # Create copy of incoming graph
    G = graph.copy()

    # If the graph is undirected, make it a directed graph with edges
    # in both directions (i.e. the graph is functionally the same)
    # if isinstance(G, nx.Graph):
    #     G = G.to_directed()

    # Initialize node attributes.
    # - `times_sampled` is the number of times this node was 
    # - `times_used` is the number of packets that passed through this router.
    nx.set_node_attributes(G, 0, "times_marked")
    nx.set_node_attributes(G, 0, "times_used")
    nx.set_edge_attributes(G, 0, "times_used")

    return G

def simulate_transmissions(
    graph: nx.Graph, 
    target_node: int, 
    attacking_nodes: list[int],
    p: float,
    num_packets: int,
) -> SimulationResult:
    """
    Simulate a DDoS attack, in which multiple nodes all send traffic to a single
    target node.
    
    This collects data need for computing all traceback algorithms, as well as
    specific data associated with each traceback algorithm.
    
    The graph is modified in place; that is, each node is given a new attribute
    containing relevant data for the simulation.
    
    :param graph: The graph to perform the simulation on.
    :param target_node: The index of the node that all traffic is directed towards.
    :param attacking_nodes: A nonempty list of node indexes that are the source
        of traffic directed at the target node.
    :param p: The probability that an edge or node is marked as part of their
        respective sampling algorithms.
    :param packets_to_send: The number of packets to send over all the nodes.
    :param payload_size: The TCP payload size of the "packets".
    """
    logger.info(f"Starting simulation ({target_node=}, {attacking_nodes=}, {p=}, {num_packets=})")
    
    # Clamp p to [0, 1]
    p = max(0, min(p, 1))
    
    # Initialize graph with required attributes
    graph = initialize_graph(graph)
    
    nappend_overhead = 0
    intermediate_routers = 0
    for _ in range(num_packets):
        # Select a random attacker node, then calculate a path from the attacker
        # node to the target node. In our case, we're always going to use the
        # shortest path by distance, which is not necessarily true of real 
        # networks. However, this makes the outcome of the simulation a lot
        # clearer, since the network conditions aren't changing halfway through.
        attacker_node = random.choice(attacking_nodes)
        path = nx.shortest_path(graph, attacker_node, target_node)
        
        # logger.info(f"Path selected: {path}")
        
        # Increment the count for the attacker node itself.
        graph.nodes[attacker_node]["times_used"] += 1
        
        # Treat all nodes except the first and last nodes as routers. Evaluate 
        # the sampling algorithms at each router.
        #
        # For the purposes of sampling, we have complete knowledge of the entire
        # graph, so it's fine to just save the router that's decided to write
        # itself into the associated packet field. For node sampling, this
        # value is precisely what we want.
        #
        # For edge sampling, we simply search for the index of this router in
        # the path. The number of elements after that router, minus one, is the
        # distance of the "edge" from the victim (as described by the algorithm).
        #
        # Because Dijkstra's/shortest path is deterministic for our graph, saving
        # the relevant nodes is sufficient to determine the would-be edges in
        # all cases.
        saved_router: int | None = None
        
        for idx, node in enumerate(path[0:-1], 0):
            # yes, all redundant, but a little nicer
            graph.nodes[node]["times_used"] += 1
            graph.edges[path[idx], path[idx+1]]["times_used"] += 1
            intermediate_routers += 1
            
            # Test if sampling applies to this node.
            x = random.random()
            if x < p:
                saved_router = node
                
            # Add this router to the "overhead", a 32-bit address.
            nappend_overhead += 4
            
        # When the victim receives the packet, increment the number of times
        # that router has been marked. Again, for shortest path, there will
        # only be one edge out of this node that is the shortest path to 
        # the victim, so there's no need to save it here.
        if saved_router is not None:
            graph.nodes[saved_router]["times_marked"] += 1
        
        # TODO: Because we won't have any weird cyclic routing, it will *never*
        # be the case that the saved distance d != the actual distance from a
        # saved edge. There's no need to save the distance, and the actual path
        # reconstructed will simply be all the nodes with a nonzero mark count,
        # plus the victim themselves. 
        #
        # For visual clarity, we will also add the attacker nodes.
        
    return SimulationResult(
        graph=graph,
        packets_sent=num_packets,
        intermediate_routers=intermediate_routers,
        nappend_overhead=nappend_overhead,
        nsample_overhead=num_packets*4,
        esample_overhead=num_packets*9
    )
        