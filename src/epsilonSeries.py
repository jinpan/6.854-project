from experiments import *

#Epsilon series

omegas = [1,0.5,0.4,0.3,0.2,0.1,0.05]
run_series(50,200,10,"epsilon_series_50_200_10.pkl",omegas)
run_series(500,2000,100,"epsilon_series_500_2000_100.pkl",omegas)
