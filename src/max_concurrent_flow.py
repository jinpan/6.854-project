'''
Maximum concurrent flow solver using the iterative method on the dual of MCF
as described in http://cgi.csc.liv.ac.uk/~piotr/ftp/mcf-jv.pdf
'''
from math import log
import math
import networkx as nx

# constants
CAPACITY_ATTRIBUTE = 'capacity'
DEMAND_ATTRIBUTE = 'demand'
FLOW_ATTRIBUTE = '_flow'
LENGTH_ATTRIBUTE = 'weight'
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


def scale_demands(commodities,scaleFactor):
    '''
    Scales each demand commodities by multiplying by scaleFactor
    '''
    for commodity in commodities:
        commodity.demand*= scaleFactor


def construct_graph(edges):
    '''
    Takes in an iterable of edges and constructs a directed graph
    '''
    G = nx.DiGraph()
    for edge in edges:
        G.add_edge(edge.head,
                   edge.tail,
                   capacity=edge.capacity,
                   weight=edge.length)

    return G


def run_shortest_path_commodity(G, commodity):
    '''
    Given a digraph G and commodity, this runs a shortest path from the source
    of the commodity to the sink of the commodity.
    '''
    source, sink = commodity.source, commodity.sink
    result_nodes = nx.shortest_path(G,source,sink,'weight')
    result = []
    for index in xrange(len(result_nodes)-1):
        result.append(G.edge[result_nodes[index]][result_nodes[index+1]])
    return result


def calculate_alpha(G, commodities):
    '''
    Takes in a digraph and an iterable of commodities, returns the sum of the
    min cost flows for satisfying these commodity demands independently

    Throws a NetworkXUnfeasible exception if there is no way to satisfy the
    demands
    '''
    total = 0
    for commodity in commodities:
        dist_j = sum([edge[LENGTH_ATTRIBUTE] for edge in run_shortest_path_commodity(G,commodity)])
        total+= commodity.demand*dist_j

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
    epsilon =  (error+1-((error+1)**2)**(1.0/3))/(error+1)
    epsilon *=0.99
    print epsilon, (1/(1-epsilon)**3), 1+error
    assert(1/(1-epsilon)**3<=1+error)
    return epsilon


def calculate_dual_objective(G):
    '''
    Calculates D(l) = sum c(e)l(e) over all e
    '''
    total = 0

    for head in G.edge.iterkeys():
        for tail, edge_dict in G.edge[head].iteritems():
            total += edge_dict[LENGTH_ATTRIBUTE] * edge_dict[CAPACITY_ATTRIBUTE]
    return total


def calculate_z(G, commodities):
    '''
    Calculates Z = min(z_i/d_i) where z_i is the max flow of commodity i
    and d_i is the demand for commodity i
    '''
    zList = []
    for commodity in commodities:
        zList.append(nx.max_flow(G,commodity.source,commodity.sink)/float(commodity.demand))
    return min(zList)



    

def maximum_concurrent_flow(edges, commodities, error=.01,scale_beta=True):
    '''
    Takes in an iterable of edges and commodities and calculates the maximum
    concurrent flow
    '''
    #calculate parameters
    epsilon = calculate_epsilon(error)
    delta = calculate_delta(len(edges), epsilon)

    #set initial edge lengths
    for edge in edges:
        edge.length = delta / edge.capacity

    #construct graph
    G = construct_graph(edges)
    
    #calculate z and scale demands
    if scale_beta:
        z = calculate_z(G,commodities)
        k = float(len(commodities))
        t = 2 * (1. / epsilon) * log(len(edges) / (1 - epsilon)) / log(1 + epsilon)
        t = int(t)
        print t
        scale_demands(commodities,k/z) #so z/k is 1
    
    count = 0 
    #start iterations
    
    while calculate_dual_objective(G) < 1:  # phases
        count += 1 
        if count%1000==0:
            print count, calculate_dual_objective(G)
        if count % t == 0:
            scale_demands(commodities,2)
            for commodity in commodities:
                print commodity.demand
        for commodity in commodities:  # iterations
            d_j = commodity.demand
            while d_j>0:
                sp = run_shortest_path_commodity(G,commodity)
                c = min([edge[CAPACITY_ATTRIBUTE] for edge in sp])
                added_flow = min(c,d_j)
                d_j-= added_flow
                for edge in sp:
                    edge[FLOW_ATTRIBUTE] = edge.get(FLOW_ATTRIBUTE,0)+added_flow
                    edge[LENGTH_ATTRIBUTE]= edge[LENGTH_ATTRIBUTE]*(1+epsilon*added_flow/edge[CAPACITY_ATTRIBUTE])
                
    
    # scale by log_(1+e) (1+e)
    total = 0
    for head in G.edge.iterkeys():
        for tail, edge_dict in G.edge[head].iteritems():
            #raw_input(edge_dict)
            edge_dict[FLOW_ATTRIBUTE] = edge_dict.get(FLOW_ATTRIBUTE,0)/(log(1. / delta) / log(1 + epsilon))
            total+= edge_dict[FLOW_ATTRIBUTE]
    

    return G.edge

