import networkx as nx
from networkx import min_cost_flow_cost as min_cost_flow
from max_concurrent_flow import *

''' Test suite for max concurrent flow algorithms
    Types of test cases we want to build:
        -Easy test case with one commodity, solvable by hand
        -Easy test case with more than one commodity, solvable by hand
        -Easy test case with >1 commodity with weird betas
        This should be enough to assure functionality. 
    
    Now we can build larger test cases to do experiments and profile on 
    (we might do this in another file)
'''


##########Test cases###############
#Basic test case: Simple flow graph
#This graph right here: http://en.wikipedia.org/wiki/File:Max-flow_min-cut_example.svg
#max flow of this graph is 7, so we can instantiate the graph and call an mcf method
#on the graph by run_max_concurrent_flow(demand) with whatever demand we want
class TestCase1():
    def __init__(self):
        self.edgeList = [
            Edge("S", "1", 4),
            Edge("S", "2", 3),
            Edge("1", "2", 3),
            Edge("1", "T", 4),
            Edge("2", "T", 5),
        ]

    def run_max_concurrent_flow(self,demand):
        commodity1 = Commodity("S","T",demand)
        return maximum_concurrent_flow(self.edgeList,[commodity1])


tc1 = TestCase1()
print tc1.run_max_concurrent_flow(7) #Beta = 1
# print tc1.run_max_concurrent_flow(.7) #Beta = 10
# print tc1.run_max_concurrent_flow(70) #Beta = .1


#Less basic test case: multiple commodities

class TestCase2():
    def __init__(self):
        self.edgeList = [
            Edge("S","1",4),
            Edge("S","4",5),
            Edge("4","1",1),
            Edge("1","2",5),
            Edge("4","5",3),
            Edge("5","2",2),
            Edge("2","3",4),
            Edge("5","6",5),
        ]
        
    def run_max_concurrent_flow(self,demand1,demand2):
        peas = Commodity("S","3",demand1)
        carrots = Commodity("S","6",demand2)
        return maximum_concurrent_flow(self.edgeList,[peas,carrots])



