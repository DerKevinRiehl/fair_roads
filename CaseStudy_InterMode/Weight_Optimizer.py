# *****************************************************************************
# ******* IMPORTS *************************************************************
# *****************************************************************************
import pandas as pd
import numpy as np
import subprocess
import sys
import random
from concurrent.futures import ThreadPoolExecutor
import os
import ast




# *****************************************************************************
# ******* METHODS *************************************************************
# *****************************************************************************
PASSENGER_COUNTS = {"car": 1.5, "truck": 10, "bus": 20, "bicycle": 1, "pedestrian": 1}
SEEDS = [41, 42, 43, 44, 45, 46, 47, 48, 49, 50]

def loadLogFile(file):
    # Load LogFile Content
    f = open(file, "r")
    content = f.read()
    f.close()
    lines = content.split("\n")
    # Extract Information
    records = []
    for line in lines:
        if "<tripinfo " in line:
            id_string = line.split("id=\"")[1].split("\"")[0]
            veh_category = id_string.split("_")[1]
            total_travel_time = line.split("duration=\"")[1].split("\"")[0]
            route_length = line.split("routeLength=\"")[1].split("\"")[0]
            delay_time = line.split("timeLoss=\"")[1].split("\"")[0]
            records.append([veh_category, route_length, total_travel_time, delay_time ])
        if "<walk " in line:
            veh_category = "pedestrian"
            total_travel_time = line.split("duration=\"")[1].split("\"")[0]
            route_length = line.split("routeLength=\"")[1].split("\"")[0]
            delay_time = line.split("timeLoss=\"")[1].split("\"")[0]
            records.append([veh_category, route_length, total_travel_time, delay_time ])
    # Transform to DataFrame
    vehicle_df = pd.DataFrame(records, columns=["Mode", "RouteLength", "TTT", "Delay"])
    for col in ["RouteLength", "TTT", "Delay"]:
        vehicle_df[col] = vehicle_df[col].astype(float)
    # Filter only completed trips
    vehicle_df = vehicle_df[vehicle_df["RouteLength"] != -1]
    # Delay Per Distance
    vehicle_df["PassengerCount"] = vehicle_df["Mode"].map(PASSENGER_COUNTS)
    vehicle_df["DelayPD"] = vehicle_df["Delay"]/vehicle_df["RouteLength"]*1000
    # Expand Rows By Number of Passengers
    passenger_df = []
    for idx, row in vehicle_df.iterrows():
        n = row["PassengerCount"]
        num_copies = int(n) + (1 if np.random.rand() < n % 1 else 0)
        for n in range(0, num_copies):
            passenger_df.append(row)
    passenger_df = pd.DataFrame(passenger_df, columns=["Mode", "RouteLength", "TTT", "Delay", "PassengerCount", "DelayPD"])
    del passenger_df["PassengerCount"]
    return vehicle_df, passenger_df

# Define the function to run the simulation
def run_simulation(candidate_weights, seed):
    script_name = "MaxPressure_Simulation.py"
    arguments = ["weights", str(candidate_weights).replace(" ", ""), LOGNAME, str(seed)]
    result = subprocess.run(["python", script_name] + arguments, capture_output=True, text=True)
    return result.stdout, result.stderr  

def evaluateScore(goal_function, candidate_weights):
    # Run Simulations in parallel
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(run_simulation, candidate_weights, seed) for seed in SEEDS]    
    for future in futures:
        stdout, stderr = future.result()
    # Evaluate results & delete logs
    logfile = "logs/LOG_tripinfo_"+LOGNAME
    scores = []
    for SEED in SEEDS:
        vehicle_df, passenger_df = loadLogFile(file=logfile+"_"+str(SEED)+".xml")
        score = goal_function(vehicle_df, passenger_df)
        scores.append(score)
        os.remove(logfile+"_"+str(SEED)+".xml")
    return np.nanmean(scores), np.nanstd(scores)

def logProcess(LOGNAME, iteration, candidate_weights, candidate_score, std):
    f = open("logs/optim_log_"+LOGNAME+".txt", "a+")
    f.write(str(iteration))
    f.write("\t")
    f.write(str(candidate_score))
    f.write("\t")
    f.write(str(std))
    f.write("\t")
    f.write(str(candidate_weights).replace(" ",""))
    f.write("\n")
    f.close()

def loadLastOptim():
    f = open("logs/optim_log_"+LOGNAME+".txt", "r")
    content = f.read()
    f.close()
    lines = content.split("\n")
    line = lines[-2]
    best_weights = ast.literal_eval(line.split("\t")[3].replace("\n", ""))
    best_score = float(line.split("\t")[1])
    return best_weights, best_score

def goal_EFFICIENCY(vehicle_df, passenger_df):
    score = sum(vehicle_df["TTT"])
    return score

def goal_UTILITARIAN(vehicle_df, passenger_df):
    score = sum(passenger_df["TTT"])
    return score

def goal_HARSANYIAN(vehicle_df, passenger_df):
    score = sum(passenger_df["DelayPD"])/len(passenger_df["DelayPD"])
    return score

def goal_RAWLSIAN1(vehicle_df, passenger_df):
    score = max(passenger_df["DelayPD"])
    return score

def goal_RAWLSIAN2(vehicle_df, passenger_df):
    score = np.percentile(passenger_df["DelayPD"], 95)
    return score

def goal_EGALITARIAN(vehicle_df, passenger_df):
    vals = passenger_df["DelayPD"].tolist()
    score = gini(vals, len(vals), np.nanmean(vals), np.sum(vals))
    return score

def gini(vals, n, av, sm):
    if n==0:
        return -1
    numerator = 0
    for i in range(0,n):
        for j in range(0,n):
            numerator += abs(vals[i]-vals[j])
    denominator = 2*n*sm
    if denominator==0:
        return -1
    else:
        return numerator/denominator




# *****************************************************************************
# ******* MAIN ****************************************************************
# *****************************************************************************
INIT_WEIGHTS = [1,1,1,1,1]
NUM_ITERATIONS = 1000  # Number of iterations to try
SEARCH_RADIUS = 0.1

# LOGNAME = "EFFICIENCY"
# goal_func = goal_EFFICIENCY

# LOGNAME = "EGALITARIAN"
# goal_func = goal_EGALITARIAN

LOGNAME = "UTILITARIAN"
goal_func = goal_UTILITARIAN

# LOGNAME = "HARSANYIAN"
# goal_func = goal_HARSANYIAN

# LOGNAME = "RAWLSIAN1"
# goal_func = goal_RAWLSIAN1

# LOGNAME = "RAWLSIAN2"
# goal_func = goal_RAWLSIAN2


# Check if Optim Log Exists
if os.path.exists("logs/optim_log_"+LOGNAME+".txt"):
    best_weights, best_score = loadLastOptim()
    print(f"Initial Solution 0: {best_weights} with score {best_score}")
else:
    best_weights = INIT_WEIGHTS
    score, std = evaluateScore(goal_function=goal_func, candidate_weights=best_weights)
    best_score = score
    print(f"Initial Solution 0: {best_weights} with score {best_score}")
    logProcess(LOGNAME, -1, best_weights, score, std)
    
# NASH-optimization
# Min. Optimization loop
for i in range(NUM_ITERATIONS):
    # Generate new candidate weights by slightly modifying the current best weights
    candidate_weights = [w + random.uniform(-SEARCH_RADIUS, SEARCH_RADIUS) for w in best_weights]  # Add small random perturbations
    candidate_weights = [w if w >= 0 else 0 for w in candidate_weights]
    candidate_weights = [w / candidate_weights[0] for w in candidate_weights]
    # Evaluate the candidate weights
    candidate_score, std = evaluateScore(goal_function=goal_func, candidate_weights=candidate_weights)
    print("\t", "Candidate", candidate_score, "["+str(std)+"]")
    # If the candidate is better, update the best weights and efficiency
    if candidate_score < best_score:  # Assuming lower efficiency is better
        best_weights = candidate_weights[:]
        best_score = candidate_score
        print(f"New best found at iteration {i}: {best_weights} with efficiency {best_score}")
        logProcess(LOGNAME, i, best_weights, best_score, std)
