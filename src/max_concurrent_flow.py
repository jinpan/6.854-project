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


def run_shortest_path_commodity(G, commodity, allSink = False):
    '''
    Given a digraph G and commodity, this runs a shortest path from the source
    of the commodity to the sink of the commodity.
    '''
    source, sink = commodity.source, commodity.sink
    if not allSink:
        result_nodes = nx.shortest_path(G,source,sink,'weight')
        result = []
        for index in xrange(len(result_nodes)-1):
            result.append(G.edge[result_nodes[index]][result_nodes[index+1]])
        return result
    else:
        result_map = nx.shortest_path(G,source,target=None,weight ='weight')
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


def calculate_demand_ratios(commodities, demands=None):
    '''
    lol
    '''
    demands = demands or [commodity.demand for commodity in commodities]
    totalDemand = sum(demands)
    return [x / float(totalDemand) for x in demands]


    

def maximum_concurrent_flow(edges, commodities, error=GLOBAL_ERROR,scale_beta=True, returnBeta = False, karakosta = False):
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
    
    #group commodities by source if karakosta
    if karakosta:
        commoditySourceMap = {}
        for commodity in commodities:
            commoditySourceMap[commodity.source]= 1
        commoditiesGroupedBySource,defaultDemandRatios = {},{}
        for commoditySource in commoditySourceMap.iterkeys():
            
            commoditySourceList = []
            for commodity in commodities:
                if commodity.source == commoditySource:
                    commoditySourceList.append(commodity)
            defaultDemandRatios[commoditySource] = calculate_demand_ratios(\
                                        commoditySourceList)
            commoditiesGroupedBySource[commoditySource]=commoditySourceList
            
        
            

    
    while calculate_dual_objective(G) < 1:  # phases
        count += 1 
        if count%1000==0:
            print count, calculate_dual_objective(G)
        if scale_beta and count % t == 0:
            scale_demands(commodities,2)
            for commodity in commodities:
                print commodity.demand
        
        #if we grouped commodities by source
        if karakosta:
            for source,comList in commoditiesGroupedBySource.iteritems():
                repElement = comList[0]
                pathMap = run_shortest_path_commodity(G,repElement,allSink=True)
                demandRatios = defaultDemandRatios[source][:]
                demandsRemaining = [com.demand for com in comList]
                tempFlowAdd = {}
                if len(comList) == 1:
                    d_j = commodity.demand
                    while d_j>0:
                        sp = run_shortest_path_commodity(G,commodity)
                        c = min([edge[CAPACITY_ATTRIBUTE] for edge in sp])
                        added_flow = min(c,d_j)
                        d_j-= added_flow
                        for edge in sp:
                            edge[FLOW_ATTRIBUTE] = edge.get(FLOW_ATTRIBUTE,0)+added_flow
                            edge[LENGTH_ATTRIBUTE]= edge[LENGTH_ATTRIBUTE]*(1+epsilon*added_flow/edge[CAPACITY_ATTRIBUTE])
                    continue

                while True:
                    for index,commodity in enumerate(comList):
                        path = pathMap[commodity.sink]
                        edgeList = []
                        for i,node in enumerate(path[:-1]):
                            edgeList.append((node,path[i+1],G.edge[node][path[i+1]]))
                        ratio = demandRatios[index]
                        minCapacity = min([edgeDict[CAPACITY_ATTRIBUTE] for head,tail,edgeDict in edgeList])
                        flow_added = ratio*min(demandsRemaining[index],minCapacity)
                        for head,tail,edgeDict in edgeList:
                            edgeDict[FLOW_ATTRIBUTE] = edgeDict.get(FLOW_ATTRIBUTE,0)+flow_added
                            tempFlowAdd[(head,tail)]= tempFlowAdd.get((head,tail),0)+ flow_added
                        demandsRemaining[index]-=flow_added
                    demandRatios = calculate_demand_ratios(comList,demandsRemaining)
                    if max(demandsRemaining)<=FP_ERROR_MARGIN: break
                for identifier,flow in tempFlowAdd.iteritems():
                    head,tail = identifier
                    edge = G.edge[head][tail]
                    edge[LENGTH_ATTRIBUTE]= edge[LENGTH_ATTRIBUTE]*(1+epsilon*flow/edge[CAPACITY_ATTRIBUTE])
        else:
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
                
    
    if returnBeta:
        return calculate_dual_objective(G)/calculate_alpha(G,commodities)
    # scale by log_(1+e) (1+e)
    total = 0
    for head in G.edge.iterkeys():
        for tail, edge_dict in G.edge[head].iteritems():
            #raw_input(edge_dict)
            edge_dict[FLOW_ATTRIBUTE] = edge_dict.get(FLOW_ATTRIBUTE,0)/(log(1. / delta) / log(1 + epsilon))
            total+= edge_dict[FLOW_ATTRIBUTE]
    

    return G.edge

def two_approx(edges, commodities, error=GLOBAL_ERROR):
    beta_hat = maximum_concurrent_flow(edges,commodities,error=1.,returnBeta=True)
    scale_demands(commodities,beta_hat/2.)
    return maximum_concurrent_flow(edges,commodities,error=error,scale_beta=False)
    
    
def karakosta(edges, commodities, error=GLOBAL_ERROR):
    pass
