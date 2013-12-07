'''
Maximum concurrent flow solver using the iterative method on the dual of MCF
as described in http://cgi.csc.liv.ac.uk/~piotr/ftp/mcf-jv.pdf
'''
import networkx as nx
from networkx.algorithms.flows import min_cost_flow_cost as min_cost_flow

# constants
LENGTH_ATTRIBUTE = 'length'
DEMAND_ATTRIBUTE = 'demand'
FP_ERROR_MARGIN = 10 ** -10  # floating point error margin


class Edge(object):

    def __init__(self, head, tail, capacity, length=None):
        self.head = head
        self.tail = tail
        self.capacity = capacity
        self.length = length or 0


class Commodity(object):

    def __init__(self, source, sink, demand):
        self.source = source
        self.sink = sink
        self.demand = demand


def construct_graph(edges):
    '''
    Takes in an iterable of edges and constructs a graph
    '''
    G = nx.DiGraph()
    for edge in edges:
        G.add_edge(edge.head
                   edge.tail,
                   capacity=edge.capacity,
                   length=edge.length)
    return G


def update_lengths(G, lengths):
    for node, length in lengths.iteritems():
        G.node[node][LENGTH_ATTRIBUTE] = length 


def calculate_alpha(G, lengths, commodities, min_cost_flow=True):
    '''
    Takes in a digraph and an iterable of commodities, returns the sum of the
    min cost flows for satisfying these commodity demands independently

    Throws a NetworkXUnfeasible exception if there is no way to satisfy the
    demands
    '''
    update_lengths(G, lengths)

    total = 0

    if min_cost_flow:
        for commodity in commodities:
            source, sink = commodity.source, commodity.sink

            G.node[source][DEMAND_ATTRIBUTE] = -commodity.demand
            G.node[sink][DEMAND_ATTRIBUTE] = commodity.demand

            total += min_cost_flow(G, weight='length')

            G.node[source][DEMAND_ATTRIBUTE] = 0
            G.node[sink][DEMAND_ATTRIBUTE] = 0
    else:
        raise NotImplementedError

    return total


def calculate_delta(m, epsilon):
    return (m / (1 - epsilon)) ** (-1. / epsilon)


def calculate_epsilon(error):
    return (1 + error) ** (1. / 3) - 1 - FP_ERROR_MARGIN


def maximum_concurrent_flow(edges, commodities, error=0.01):
    '''
    Takes in an iterable of edges and commodities and calculates the maximum
    concurrent flow
    '''
    lengths = {}  # hashmap of nodes to lengths

    G = construct_graph(edges)

