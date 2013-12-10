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
FP_ERROR_MARGIN = 10e-10  # floating point error margin
GLOBAL_ERROR = 0.05


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


def scale_demands(commodities, scaleFactor):
    '''
    Scales each demand commodities by multiplying by scaleFactor
    '''
    for commodity in commodities:
        commodity.demand *= scaleFactor


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


def get_edges(G, node_path, headTail=False):
    '''
    Given a graph G and a list of nodes in a path, this returns the list of
    edges in that graph

    If headTail is given as True, we return a list of tuples (head, tail, edge)
    '''
    edges = []
    for idx, head in enumerate(node_path[:-1]):
        tail = node_path[idx + 1]
        if headTail: 
            edges.append((head, tail, G.edge[head][tail]))
        else:
            edges.append(G.edge[head][tail])
    return edges


def run_shortest_path_commodity(G, commodity, allSinks=False):
    '''
    Given a digraph G and commodity, this runs a shortest path from the source
    of the commodity to the sink of the commodity.
    '''
    source, sink = commodity.source, commodity.sink

    if not allSinks:
        node_path = nx.shortest_path(G, source, sink, weight=LENGTH_ATTRIBUTE)
        return get_edges(G, node_path)
    else:
        result_map = nx.shortest_path(G, source, target=None, weight=LENGTH_ATTRIBUTE)
        return result_map
        

def calculate_alpha(G, commodities):
    '''
    Takes in a digraph and an iterable of commodities, returns the sum of the
    min cost flows for satisfying these commodity demands independently

    Throws a NetworkXUnfeasible exception if there is no way to satisfy the
    demands
    '''
    total = 0
    for commodity in commodities:
        dist_j = sum([edge[LENGTH_ATTRIBUTE]
                      for edge in run_shortest_path_commodity(G,commodity)])
        total += commodity.demand * dist_j
    return total


def calculate_delta(num_edges, epsilon):
    '''
    Calculates delta = (m/(1-e)) ^ (-1/e)
    '''
    return (num_edges / (1 - epsilon)) ** (-1. / epsilon)


def calculate_epsilon(error):
    '''
    Calculates the largest epsilon such that (1-e) ^ -3 is at most 1+error
    '''
    epsilon = (error + 1 - ((error + 1) ** 2) ** (1. / 3))/(error + 1)
    epsilon *= 0.99
    assert(1 / (1 - epsilon) ** 3 <= 1 + error)
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
        zList.append(nx.max_flow(G, commodity.source, commodity.sink) / float(commodity.demand))
    return min(zList)


def calculate_demand_ratios(commodities, demands=None):
    '''
    Takes in a list of commodities and demands.  If demands are not given,
    it defaults to a list of the full demands for the commodities.

    Returns a multi-ratio of the demands
    '''
    demands = demands or [commodity.demand for commodity in commodities]
    totalDemand = sum(demands)
    return [demand / float(totalDemand) for demand in demands]


def maximum_concurrent_flow(edges, commodities, error=GLOBAL_ERROR,
                            scale_beta=False, returnBeta=False,
                            karakosta = False, shortestPathComputations=0):
    '''
    Takes in an iterable of edges and commodities and calculates the maximum
    concurrent flow
    '''
    twoApprox = False
    if shortestPathComputations!=0:
        twoApprox = True
    #calculate parameters
    epsilon = calculate_epsilon(error)
    delta = calculate_delta(len(edges), epsilon)
    print "Epislon, Delta: ", epsilon, delta

    #set initial edge lengths
    for edge in edges:
        edge.length = delta / edge.capacity

    #construct graph
    G = construct_graph(edges)
    
    #calculate z and scale demands
    if scale_beta:
        z = calculate_z(G, commodities)  # z is minimum of shortest paths
        k = float(len(commodities))  # k is number of commodities
        t = 2 * (1. / epsilon) * log(len(edges) / (1 - epsilon)) / log(1 + epsilon)
        t = int(t)  # t is iteration threshold
        scale_demands(commodities, k/z)  # so z/k is 1
    
    count = -1
    #start iterations
    
    # group commodities by source if karakosta
    if karakosta:
        commoditySourceMap = set()  # collects all possible sources
        for commodity in commodities:
            commoditySourceMap.add(commodity.source)

        commoditiesGroupedBySource, defaultDemandRatios = {}, {}
        for commoditySource in commoditySourceMap:
            commoditySourceList = [commodity for commodity in commodities
                                   if commodity.source == commoditySource]
            defaultDemandRatios[commoditySource] = calculate_demand_ratios(commoditySourceList)
            commoditiesGroupedBySource[commoditySource] = commoditySourceList

    old_objective = -1
    while True:  # phases
        current_objective = calculate_dual_objective(G)
        if current_objective >= 1: break

        if old_objective >= calculate_dual_objective(G):
            raise Exception
        else:
            old_objective = current_objective

        count += 1 
        if count % 1000 == 0:
            print count, current_objective
            
        if scale_beta and count % t == 0:  # for scaling
            scale_demands(commodities, 2)
        
        # if we grouped commodities by source
        if karakosta:
            for source, comList in commoditiesGroupedBySource.iteritems():
                repElement = comList[0]
                pathMap = run_shortest_path_commodity(G, repElement, allSinks=True)
                shortestPathComputations += 1
                demandRatios = defaultDemandRatios[source][:]
                demandRemaining = [com.demand for com in comList]
                tempFlowAdd = {}

                if len(comList) == 1:
                    d_j = repElement.demand
                    while d_j > 0:
                        sp = get_edges(G,pathMap[repElement.sink])

                        min_cap = min([edge[CAPACITY_ATTRIBUTE] for edge in sp])
                        added_flow = min(min_cap,d_j)
                        d_j -= added_flow
                        for edge in sp:
                            edge[FLOW_ATTRIBUTE] = edge.get(FLOW_ATTRIBUTE, 0) + added_flow
                            edge[LENGTH_ATTRIBUTE] = edge[LENGTH_ATTRIBUTE] * (1 + epsilon * added_flow / edge[CAPACITY_ATTRIBUTE])
                    continue

                while True:
                    for index, commodity in enumerate(comList):  # for every commodity that shares a source
                        edgeList = get_edges(G,pathMap[commodity.sink],headTail = True)

                        ratio = demandRatios[index]
                        min_cap = min([edge_dict[CAPACITY_ATTRIBUTE] for head,tail,edge_dict in edgeList])  # select the minimum capacity from the edges
                        added_flow = ratio * min(demandRemaining[index], min_cap)  # scale min_cap by the ratio
                        for head, tail, edgeDict in edgeList:
                            edgeDict[FLOW_ATTRIBUTE] = edgeDict.get(FLOW_ATTRIBUTE, 0) + added_flow
                            tempFlowAdd[(head, tail)]= tempFlowAdd.get((head, tail), 0) + added_flow
                        demandRemaining[index] -= added_flow
                    demandRatios = calculate_demand_ratios(comList, demandRemaining)
                    if max(demandRemaining) <= FP_ERROR_MARGIN: break  # all remaining demands effectively 0

                for identifier, flow in tempFlowAdd.iteritems():
                    head, tail = identifier
                    edge = G.edge[head][tail]
                    edge[LENGTH_ATTRIBUTE] = edge[LENGTH_ATTRIBUTE] * (1 + epsilon * flow / edge[CAPACITY_ATTRIBUTE])
        else:  # if not karakosta
            for commodity in commodities:  # iterations
                d_j = commodity.demand

                while d_j > 0:
                    sp = run_shortest_path_commodity(G, commodity)
                    shortestPathComputations +=1
                    min_cap = min([edge[CAPACITY_ATTRIBUTE] for edge in sp])
                    added_flow = min(min_cap, d_j)
                    d_j -= added_flow
                    for edge in sp:
                        edge[FLOW_ATTRIBUTE] = edge.get(FLOW_ATTRIBUTE, 0) + added_flow
                        edge[LENGTH_ATTRIBUTE]= edge[LENGTH_ATTRIBUTE] * (1 + epsilon * added_flow / edge[CAPACITY_ATTRIBUTE])
                
    if returnBeta:  # returns beta value, not edge_dict, used in 2-approx
        return shortestPathComputations, calculate_dual_objective(G) / calculate_alpha(G, commodities)
    # scale by log_(1+e) (1+e)
    for head in G.edge.iterkeys():
        for tail, edge_dict in G.edge[head].iteritems():
            edge_dict[FLOW_ATTRIBUTE] = edge_dict.get(FLOW_ATTRIBUTE, 0) / (log(1. / delta) / log(1 + epsilon))
    print "SPC-"+str(karakosta)+"-"+str(twoApprox)+ " for G(" + str(len(G.node.keys()))+","+str(len(edges))+") w/ error " + str(error)+ ": " + str(shortestPathComputations)
    return shortestPathComputations,count


def two_approx(edges, commodities, error=GLOBAL_ERROR, karakosta=False):
    spc, beta_hat = maximum_concurrent_flow(edges, commodities, error=1., returnBeta=True, karakosta=karakosta)
    scale_demands(commodities, beta_hat / 2.)
    return maximum_concurrent_flow(edges, commodities, error=error, scale_beta=False, karakosta=karakosta, shortestPathComputations=spc)

