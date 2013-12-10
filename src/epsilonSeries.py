from itertools import product

from experiments import *

#Epsilon series

omegas = [1, 0.5, 0.4, 0.3, 0.2, 0.1]
nodes = [50, 100, 200, 400]
edges = [200, 400, 800]
commodities = [10, 20, 40, 80, 160, 320]


def make_commodity_distributions(commodities):
    half = commodities / 2
    return ([commodities],
            [half, commodities - half],
            [1 for _ in range(commodities)])

def make_file_name(nodes, edges, commodities, commodity_distribution,
                   two_factor=False, karakosta=False, multi_route=False):
    if two_factor or karakosta or multi_route:
        opt_string = '_'
        if two_factor:
            opt_string += 'b'
        if karakosta:
            opt_string += 'k'
        if multi_route:
            opt_string += 'm'
    else:
        opt_string = ''
    com_dist = len(commodity_distribution)
    return 'data2/omega_series_%d_%d_%d%s_%d.pkl' % (nodes, edges, commodities, opt_string, com_dist)

node = int(raw_input("node: "))

# for node, edge, commodity in product(nodes, edges, commodities):
for edge, commodity in product(edges, commodities):
    for commodity_distribution in make_commodity_distributions(commodity):
        for two_factor, karakosta in product([True, False],
                                             [True, False], ):
            name = make_file_name(node, edge, commodity, commodity_distribution,
                                  two_factor, karakosta, )
            print node, edge, commodity, name, omegas, commodity_distribution, two_factor, karakosta
            run_series(node, edge, commodity, name, omegas,
                       commodity_distribution, two_factor, karakosta, )

