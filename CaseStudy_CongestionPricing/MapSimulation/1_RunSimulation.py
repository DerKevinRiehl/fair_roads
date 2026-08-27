# Imports
import os
import sys
if 'SUMO_HOME' in os.environ:
    sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
import traci
import numpy as np

# Functions
def startSumo():
    sumoBinary = "C:/Users/kriehl/AppData/Local/sumo-1.19.0/bin/sumo.exe"
    sumoConfigFile = "Configuration.sumocfg" #"Configuration.sumocfg"
    sumoCmd = [sumoBinary, "-c", sumoConfigFile, "--start", "--quit-on-end", "--time-to-teleport", "-1"]
    traci.start(sumoCmd)
   
def stopSumo():
    traci.close()

def spawnProcedure(route, flow_third, vcounter):
    spawn_prob = flow_third/60/60

    # rand_exp_variable = min(1, np.random.exponential(1/5))
    # if rand_exp_variable <= -np.log(1-spawn_prob)/5: # CDF of exp. variable CDF(x) = 1-e^(-lambda*x)
    #     traci.vehicle.add("v"+str(vcounter)+"_1", route+"_1", typeID="vtype"+str(np.random.randint(1,10+1)))
    #     vcounter += 1
    rand_exp_variable = min(1, np.random.exponential(1/5))
    if rand_exp_variable <= -np.log(1-spawn_prob)/5: # CDF of exp. variable CDF(x) = 1-e^(-lambda*x)
        traci.vehicle.add("v"+str(vcounter)+"_2", route+"_2", typeID="vtype"+str(np.random.randint(1,10+1)))
        vcounter += 1
    rand_exp_variable = min(1, np.random.exponential(1/5))
    if rand_exp_variable <= -np.log(1-spawn_prob)/5: # CDF of exp. variable CDF(x) = 1-e^(-lambda*x)
        traci.vehicle.add("v"+str(vcounter)+"_1", route+"_3", typeID="vtype"+str(np.random.randint(1,10+1)))
        vcounter += 1
    return vcounter

# Parameters
fundamental_diagram_lane_name = "E0_0" #'E0_0'
vehicle_spawn_period = 5
simulation_steady_state_iterations = 100
flow_observation_period = 2000 # seconds
vehicles_per_spawn = 3


# Freeflow Speeds
# RouteA = 138s [0]
# routeA_1 = 138s [0]
# routeA_2 = 139s [0]
# routeA_3 = 138s [0]
# 0 149.74358974358975 147.0 156 [ 10.365049627493715 ]
# 100 152.63276836158192 151.0 177 [ 10.99489607926338 ]
# 200 154.9047619047619 154.0 189 [ 10.518888456548062 ]
# 300 158.35 158.0 200 [ 9.655438881790927 ]
# 400 164.605 162.0 200 [ 11.037163358399658 ]

# RouteB = 241s
# routeB_1 = 241s [0]
# routeB_2 = 240s [0]
# routeB_3 = 241s [0]
# 0 264.18589743589746 258.5 156 [ 19.279258313474763 ]
# 100 265.85185185185185 265.0 162 [ 21.044110704329533 ]
# 200 267.42011834319527 265.0 169 [ 22.705885324918775 ]
# 300 267.2471264367816 264.0 174 [ 20.78466133751157 ]
# 400 269.95628415300547 267.0 183 [ 20.322757745132535 ]

quickest_possible_time = 0
route = "routeB"
testRoute = "routeB_1"
for flow in range(389,550+1): #[0, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550]: # [0, 100, 200, 300, 400]:#, 500, 600]:
    times = []
    # for n in range(0, 10):
    # Start Sumo
    startSumo()
    # print("Started SUMO")
    
    # Warmup Run
    vcounter = 0
    for it in range(0,60*60):
        traci.simulationStep()
        vcounter = spawnProcedure(route, flow, vcounter)
    
    # Create Test Vehicle
    for n in range(0,200):
        testVehicleID = "Test"+str(n)
        traci.vehicle.add(testVehicleID, testRoute)
        traci.simulationStep()
        vcounter = spawnProcedure(route, flow, vcounter)
        
        while testVehicleID not in traci.vehicle.getIDList():
            traci.simulationStep()
            vcounter = spawnProcedure(route, flow, vcounter)
            
        timestart = traci.simulation.getTime()
        while testVehicleID in traci.vehicle.getIDList():
            traci.simulationStep()
            vcounter = spawnProcedure(route, flow, vcounter)
        timeend = traci.simulation.getTime()
        
        # print(timeend-timestart)
        if timeend-timestart>=quickest_possible_time-2:
            times.append(timeend-timestart)
    
    # # Stop Sumo
    stopSumo()
    # print("Closed SUMO")
    # print("======================")
    print(flow, np.nanmean(times), np.nanmedian(times), len(times), "[", np.nanstd(times), "]")
    f = open(route+".txt", "a+")
    f.write(str(flow))
    f.write("\t")
    f.write(str(np.nanmean(times)))
    f.write("\t")
    f.write(str(np.nanmedian(times)))
    f.write("\t")
    f.write(str(len(times)))
    f.write("\t")
    f.write(str(np.nanstd(times)))
    f.write("\t")
    f.write("\n")
    f.close()