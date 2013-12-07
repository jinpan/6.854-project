'''
Maximum concurrent flow solver using the iterative method on the dual of MCF
as described in http://cgi.csc.liv.ac.uk/~piotr/ftp/mcf-jv.pdf
'''
from math import log

import networkx as nx
from networkx.algorithms.flow import min_cost_flow
from networkx.algorithms.flow import min_cost_flow_cost

# constants
CAPACITY_ATTRIBUTE = 'capacity'
DEMAND_ATTRIBUTE = 'demand'
FLOW_ATTRIBUTE = '_flow'
LENGTH_ATTRIBUTE = 'length'
FP_ERROR_MARGIN = 10 ** -10  # floating point error margin


class Edge(object):

    length = None

    def __init__(self, head, tail, capacity):
        self.head = head
        self.tail = tail
        self.capacity = capacity
        self.flow = 0


class Commodity(object):

    def __init__(self, source, sink, demand):
        self.source = source
        self.sink = sink
        self.demand = demand


def construct_graph(edges):
    '''
    Takes in an iterable of edges and constructs a directed graph
    '''
    G = nx.DiGraph()
    for edge in edges:
        G.add_edge(edge.head,
                   edge.tail,
                   capacity=edge.capacity,
                   length=edge.length)
    return G


def run_min_cost_flow(G, commodity, cost=False):
    '''
    Given a digraph G and commodity, this runs a min cost flow on the graph for
    that commodity.

    If cost is true, we return just the cost; otherwise, we return a hashmap of
    the flow
    '''
    source, sink = commodity.source, commodity.sink

    G.node[source][DEMAND_ATTRIBUTE] = -commodity.demand
    G.node[sink][DEMAND_ATTRIBUTE] = commodity.demand

    if cost:
        result = min_cost_flow_cost(G, weight=LENGTH_ATTRIBUTE)
    else:
        result = min_cost_flow(G, weight=LENGTH_ATTRIBUTE)

    G.node[source][DEMAND_ATTRIBUTE] = 0
    G.node[sink][DEMAND_ATTRIBUTE] = 0

    return result


def calculate_alpha(G, commodities, min_cost_flow=True):
    '''
    Takes in a digraph and an iterable of commodities, returns the sum of the
    min cost flows for satisfying these commodity demands independently

    Throws a NetworkXUnfeasible exception if there is no way to satisfy the
    demands
    '''
    total = 0

    if min_cost_flow:
        for commodity in commodities:
            total += run_min_cost_flow(G, commodity, cost=True)

    else:  # use the shortest paths
        raise NotImplementedError

    return total


def calculate_delta(num_edges, epsilon):
    '''
    Calculates delta = (m/(1-e)) ^ (-1/e)
    '''
    return (num_edges / (1 - epsilon)) ** (-1. / epsilon)


def calculate_epsilon(error):
    '''
    Calculates epsilon such that (1-e) ^ -3 is at most 1+error
    '''
    return 1 - (1 + error) ** -1./3 - FP_ERROR_MARGIN


def calculate_dual_objective(G):
    '''
    Calculates D(l) = sum c(e)l(e) over all e
    '''
    total = 0

    for head in G.edge.iterkeys():
        for tail, edge_dict in G.edge[head].iteritems():
            edge = G.edge[head][tail]
            total += edge[LENGTH_ATTRIBUTE] * edge[CAPACITY_ATTRIBUTE]

    return total


def maximum_concurrent_flow(edges, commodities, error=0.01):
    '''
    Takes in an iterable of edges and commodities and calculates the maximum
    concurrent flow
    '''
    epsilon = calculate_epsilon(error)
    delta = calculate_delta(len(edges), epsilon)

    for edge in edges:
        head, tail = edge.head, edge.tail

        edge.length = delta / edge.capacity

    G = construct_graph(edges)
    
    count = 0
    while calculate_dual_objective(G) < 1:  # phases
        count += 1
        print count, calculate_dual_objective(G)
        for commodity in commodities:  # iterations
            
            # 1 Get the edges and flows in the min cost flow
            flow_dict = run_min_cost_flow(G, commodity)

            # 2 send flow along those edges and update our length function
            for head in flow_dict.iterkeys():
                for tail, flow in flow_dict[head].iteritems():
                    edge = G.edge[head][tail]

                    edge[FLOW_ATTRIBUTE] = edge.get(FLOW_ATTRIBUTE, 0) + flow
                    edge[LENGTH_ATTRIBUTE] = (edge[LENGTH_ATTRIBUTE]
                                              * (1. + epsilon * flow
                                                 / edge[CAPACITY_ATTRIBUTE]))

    # scale by log_(1+e) (1+e)
    for head in G.edge.iterkeys():
        for tail, edge_dict in G.edge[head].iteritems():
            edge_dict[FLOW_ATTRIBUTE] * log(1. / delta) / log(1 + epsilon)

    return G.edge

