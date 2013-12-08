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
        self.edgeList = []
        self.edgeList.append(Edge("S","1",4))
        self.edgeList.append(Edge("S","2",3))
        self.edgeList.append(Edge("1","2",3))
        self.edgeList.append(Edge("1","T",4))
        self.edgeList.append(Edge("2","T",5))


    def run_max_concurrent_flow(self,demand):
        commodity1 = Commodity("S","T",demand)
        return maximum_concurrent_flow(self.edgeList,[commodity1],karakosta=True)


tc1 = TestCase1()
if True:
    for demand in [7,.7,70]:
        result =  tc1.run_max_concurrent_flow(demand) #Beta = 3/7
        print (result['1']['T']['_flow']+result['2']['T']['_flow'])/demand
        print result

#Less basic test case: multiple commodities

class TestCase2():
    def __init__(self):
        self.edgeList = []
        self.edgeList.append(Edge("S","1",4))
        self.edgeList.append(Edge("S","4",5))
        self.edgeList.append(Edge("4","1",1))
        self.edgeList.append(Edge("1","2",5))
        self.edgeList.append(Edge("4","5",3))
        self.edgeList.append(Edge("2","5",2))
        self.edgeList.append(Edge("2","3",4))
        self.edgeList.append(Edge("5","6",5))
        
    def run_max_concurrent_flow(self,demand1,demand2):
        peas = Commodity("S","3",demand1)
        carrots = Commodity("S","6",demand2)

        return maximum_concurrent_flow(self.edgeList,[peas,carrots],karakosta=False)


    def run_two_approx(self,demand1,demand2):
        commodities = [Commodity("S","3",demand1),Commodity("S","6",demand2)]
        return two_approx(self.edgeList,commodities)

tc2 = TestCase2()
if False:
    for demand in [(1,.5),(10,10),(4,4)]:

        result = tc2.run_max_concurrent_flow(demand[0],demand[1])    
        print min(result['2']['3']['_flow']/demand[0],result['5']['6']['_flow']/demand[1])
        print result

        print("\n Two approx \n")
        result = tc2.run_two_approx(demand[0],demand[1])
        print min(result['2']['3']['_flow']/demand[0],result['5']['6']['_flow']/demand[1])
        print result



