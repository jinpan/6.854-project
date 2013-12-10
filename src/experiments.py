'''
Code that contains all the experiments. Will write useful data to csv files
Types of information we want to be able to glean from graphs:
-Dependence on epsilon
-Dependence on k
-Dependence on k groupings (more grouped, more better?)

Types of graphs we want to run on:
-Random graphs of x nodes for x in [50,500,5000]
-Places where we can caluclate L

Algorithms we want to use:
-Standard algorithm
-Algorithm with 2-approx
-Algorithm with 2-Approx, karakosta
-Alogrithm with karakosta
'''

import random
import pickle
import time

import networkx as nx

from max_concurrent_flow import *


def random_connected_graph(numNodes, numEdges):
    '''Generates a weakly connected random graph with numNodes nodes
       and numEdges edges
    '''
    tries = 0
    while tries < 100:
        tries += 1
        random_graph = nx.gnm_random_graph(numNodes,numEdges,directed = True)
        if nx.is_weakly_connected(random_graph): 
            return random_graph
    return None

def randomCommodities(random_graph, numCommodities, commodityDistribution = None):
    '''Generates a list of commodities with reachable source and sink
       and numCommodity groups numbers of commodities with the same starting source
    '''

    edgeDict = random_graph.edge
    nodes = set([key for key in edgeDict.iterkeys()])
    commodities = []
    commodityDistribution = commodityDistribution or [1] * numCommodities
    assert len(commodityDistribution) <= len(nodes)
    for xCommodities in commodityDistribution:
        done = False
        while not done:
            randomChoice = random.sample(nodes, 1)[0]
            possSinks = [k for k in nx.shortest_path(random_graph,randomChoice).iterkeys()]
            possSinks.remove(randomChoice)
            if len(possSinks) < xCommodities:
                pass
            else:
                nodes.remove(randomChoice)
                sinks = random.sample(possSinks, xCommodities)
                
                for sink in sinks:
                    commodities.append(Commodity(randomChoice, sink, random.randint(1,50)))
                done = True
    assert len(commodities) == numCommodities
    for commodity in commodities:
        assert(commodity.sink in nx.shortest_path(random_graph, commodity.source))
    return commodities


def prepare_random_input(numNodes,numEdges,numCommodities,commodityDistribution=None):
    print "Making random graph"
    random_graph = random_connected_graph(numNodes,numEdges)
    if random_graph is None:
        return None, None
    print "Finished making random graph\n Making random commodities"
    commodities = randomCommodities(random_graph, numCommodities, commodityDistribution)
    print "Finished making random commodities"
    edgeList = []
    for head,v in random_graph.edge.iteritems():
        for tail in v.iterkeys():
            edgeList.append(Edge(head,tail, random.randint(2,10)))
    return edgeList, commodities


def run_series(numNodes, numEdges, numCommodities, outFile, omegas,
               commodityDistribution=None, two_factor=False, karakosta=False,
               multi_route=False):
    outData = {}
    for idx in range(10):
        edgeList,commodities = prepare_random_input(numNodes,numEdges,
                                                    numCommodities,commodityDistribution)
        if edgeList is None and commodities is None:
            continue

        for omega in omegas:
            print "ITERATION: %d; OMEGA: %f" % (idx, omega)
            now = time.time()
            try:
                if two_factor:
                    spc, iterations = two_approx(edgeList, commodities,
                                                error=omega, karakosta=karakosta)
                else:
                    spc, iterations = maximum_concurrent_flow(edgeList, commodities,
                                                            error=omega,
                                                            karakosta=karakosta)
                if omega not in outData: outData[omega] = []
                outData[omega].append((spc,iterations,time.time()-now))
            except:
                outData[omega].append((None, None, None))

    pickle.dump(outData,open(outFile,'wb'))


def generate_csv(pkl_file_name):
    data = pickle.load(open(pkl_file_name))

    averaged_data = {}
    for omega, datum in data.iteritems():
        spc_total, iterations_total, seconds_total = 0., 0., 0.

        for spc, iterations, seconds in datum:
            spc_total += float(spc)
            iterations_total += float(iterations)
            seconds_total += float(iterations)

        spc_total /= len(datum)
        iterations_total /= len(datum)
        seconds_total /= len(datum)

        averaged_data[omega] = (spc_total, iterations_total, seconds_total)
    
    with open(pkl_file_name.rstrip('pkl') + 'csv', 'w') as f:
        f.write('w, num_shortest_paths, num_iterations, num_seconds')
        for key in sorted(averaged_data.keys(), reverse=True):
            f.write('%s, %s, %s, %s\n' % ((key, ) + averaged_data[key]))

