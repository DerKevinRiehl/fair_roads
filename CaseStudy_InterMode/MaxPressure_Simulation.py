# *****************************************************************************
# ******* IMPORTS *************************************************************
# *****************************************************************************
import os
import sys
if "SUMO_HOME" in os.environ:
    sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))
import traci
import numpy as np
import pandas as pd
import shutil
import sys
import ast



# *****************************************************************************
# ******* SUMO FUNCTIONS ******************************************************
# *****************************************************************************
def startSumo(sumo_binary_path, sumo_config_file, seed):
    """This function starts SUMO simulator"""
    sumo_run_command = [sumo_binary_path, "-c", sumo_config_file, "--start", 
                        "--quit-on-end", "--time-to-teleport", "-1", "--seed", 
                        str(seed), "--tripinfo-output", "logs/LOG_tripinfo_"+LOG_NAME+"_"+str(seed)+".xml",
                        "--tripinfo-output.write-unfinished", "true",]
    traci.start(sumo_run_command)
    
def stopSumo():
    """This function stops SUMO simulator"""
    traci.close()
    
    
# *****************************************************************************
# ******* PHASE AND LANE INFORMATION & FUNCTIONS ******************************
# *****************************************************************************
WEIGHTS = [1,1,1,1,1]
LOG_NAME = "DEMO"

intersection_setup = {
    "relevant_lanes": {
        0:  ["-E2_5", "-E2_4", "-E2_3", "-E2_2", "-E3_5", "-E3_4", "-E3_3", "-E3_2"],
        4:  ["E0_5", "E0_4", "E0_3", "E0_2", "-E1_5", "-E1_4", "-E1_3", "-E1_2"],
        8:  [":J1_w6", ":J1_w7", ":J1_w3", ":J1_w2"],
        10: [":J1_w0", ":J1_w1", ":J1_w5", ":J1_w4"]
    },
    "reevaluation_durations": {
        0:  10,
        4:  10,
        8:  5,
        10: 5
    },
    "transition_phase": {
        0:  1,
        4:  5,
        8:  9,
        10: 11
    },
    "transition_duration": {
        0: 12,
        4: 12,
        8: 3,
        10: 3
    }
}

def categorizeVehicles(vehicle_ids):
    car_ids = []
    truck_ids = []
    bus_ids = []
    bicycle_ids = []
    pedestrian_ids = []
    for vehicle in vehicle_ids:
        if "car" in vehicle:
            car_ids.append(vehicle)
        elif "truck" in vehicle:
            truck_ids.append(vehicle)
        elif "bus" in vehicle:
            bus_ids.append(vehicle)
        elif "bicycle" in vehicle:
            bicycle_ids.append(vehicle)
        else:
            pedestrian_ids.append(vehicle)
    return car_ids, truck_ids, bus_ids, bicycle_ids, pedestrian_ids
    
def getVehicleIDs(relevant_lanes):
    vehicle_ids = []
    for lane in relevant_lanes:
        if lane.startswith(":"):
            vehicles = traci.edge.getLastStepPersonIDs(lane)
            for vehicle in vehicles:
                vehicle_ids.append(vehicle)
        else:
            vehicles = traci.lane.getLastStepVehicleIDs(lane)
            for vehicle in vehicles:
                vehicle_ids.append(vehicle)
    return categorizeVehicles(vehicle_ids)

def getWaitingTime(car_ids, truck_ids, bus_ids, bicycle_ids, pedestrian_ids):
    wait_cars = 0
    wait_trucks = 0
    wait_bus = 0
    wait_bicycles = 0
    lst_wait_pedestrian = []
    for car in car_ids:
        wait_cars += traci.vehicle.getWaitingTime(car)
    for truck in truck_ids:
        wait_trucks += traci.vehicle.getWaitingTime(truck)
    for bus in bus_ids:
        wait_bus += traci.vehicle.getWaitingTime(bus)
    for bicycle in bicycle_ids:
        wait_bicycles += traci.vehicle.getWaitingTime(bicycle)
    for person in pedestrian_ids:
        lst_wait_pedestrian.append(traci.person.getWaitingTime(person))
    if len(lst_wait_pedestrian)==0:
        lst_wait_pedestrian = [0]
    return wait_cars, wait_trucks, wait_bus, wait_bicycles, sum(lst_wait_pedestrian), max(lst_wait_pedestrian)

def getPressureOfPhase(phase):
    relevant_lanes = intersection_setup["relevant_lanes"][phase]
    car_ids, truck_ids, bus_ids, bicycle_ids, pedestrian_ids = getVehicleIDs(relevant_lanes)
    wait_cars, wait_trucks, wait_bus, wait_bicycles, wait_pedestrians_sum, wait_pedestrians_max = getWaitingTime(car_ids, truck_ids, bus_ids, bicycle_ids, pedestrian_ids)
    n_vehicles = len(car_ids) + len(truck_ids) + len(bus_ids) + len(bicycle_ids) + (1 if pedestrian_ids else 0)
    n_waittime = WEIGHTS[0]*wait_cars + WEIGHTS[1]*wait_trucks + WEIGHTS[2]*wait_bus + WEIGHTS[3]*wait_bicycles + WEIGHTS[4]*wait_pedestrians_max
    return n_vehicles, n_waittime




# *****************************************************************************
# ******* GET INPUT FROM COMMAND LINE *****************************************
# *****************************************************************************
RANDOM_SEED = 42
args = sys.argv 
for argX in range(0, len(args)):
    arg = args[argX]
    if arg=="weights":
        weightsString = args[argX+1]
        logname = args[argX+2]
        seed = args[argX+3]
        WEIGHTS = ast.literal_eval(weightsString)
        LOG_NAME = logname
        RANDOM_SEED = int(seed)



# *****************************************************************************
# ******* SIMULATION RUN ******************************************************
# *****************************************************************************

# Start Sumo
# sumo_binary_path = "C:/Program Files (x86)/Eclipse/Sumo/bin/sumo.exe" # sumo-gui.exe
sumo_binary_path = "C:/Users/kriehl/AppData/Local/sumo-1.19.0/bin/sumo.exe"
sumo_config_file = "Configuration.sumocfg" 
startSumo(sumo_binary_path, sumo_config_file, RANDOM_SEED)

# Init Control
current_phase = 0
next_phase = 0
timer_reevaluation = intersection_setup["reevaluation_durations"][current_phase]
timer_transition = -1

# Run Simulation
for it_time in range(0, 3600):
    traci.simulationStep()
    traci.simulationStep()
    traci.simulationStep()
    traci.simulationStep()
    
    # Re-evaluation
    if timer_transition==-1:
        timer_reevaluation -= 1
        if timer_reevaluation == 0:
            # print(it_time, ">>Re-evaluation from ", current_phase)
            # Determine Phase with Highest Pressure
            max_pressure = 0
            max_pressure_phase = current_phase
            for phase in intersection_setup["relevant_lanes"]:
                n_vehicles, n_waittime = getPressureOfPhase(phase)
                # print("\t", "...", phase, n_vehicles, n_waittime)
                pressure = n_waittime 
                if pressure > max_pressure:
                    max_pressure = pressure 
                    max_pressure_phase = phase 
                    # print("*", max_pressure_phase)
            # Transition or not
            if max_pressure_phase == current_phase:
                timer_reevaluation = intersection_setup["reevaluation_durations"][current_phase]
                traci.trafficlight.setPhase("J1", current_phase)
                # print(it_time, "\t", current_phase, "stays")
            else:
                timer_transition = intersection_setup["transition_duration"][current_phase] 
                next_phase = max_pressure_phase
                # print(it_time, "\t", next_phase, "will be next")
                traci.trafficlight.setPhase("J1", intersection_setup["transition_phase"][current_phase])
    # Waiting for transition
    else:
        timer_transition -= 1
        if timer_transition == 0:
            current_phase = next_phase
            timer_reevaluation = intersection_setup["reevaluation_durations"][current_phase]
            traci.trafficlight.setPhase("J1", current_phase)
            # print(it_time, ">>Change State from ", current_phase, "to", next_phase)
                
# Stop Sumo
stopSumo()

# # Store Log
# if LOG_NAME!="DEMO":
#     shutil.move("logs/LOG_tripinfo.xml", "logs/LOG_tripinfo_"+LOG_NAME+"_"+weightsString+"_"+str(RANDOM_SEED)+".txt")
