# *****************************************************************************
# ******* IMPORTS *************************************************************
# *****************************************************************************
import pandas as pd
import numpy as np
import subprocess
from concurrent.futures import ThreadPoolExecutor
import ast



# *****************************************************************************
# ******* METHODS *************************************************************
# *****************************************************************************
PASSENGER_COUNTS = {"car": 1.5, "truck": 10, "bus": 20, "bicycle": 1, "pedestrian": 1}
SEEDS = [41, 42, 43, 44, 45, 46, 47, 48, 49, 50]
LOGFOLDER = "logs_run2"

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

def createLogs(candidate_weights):
    # Run Simulations in parallel
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(run_simulation, candidate_weights, seed) for seed in SEEDS]    
    for future in futures:
        stdout, stderr = future.result()

def loadLastOptim():
    f = open(LOGFOLDER+"/optim_log_"+LOGNAME+".txt", "r")
    content = f.read()
    f.close()
    lines = content.split("\n")
    line = lines[-2]
    best_weights = ast.literal_eval(line.split("\t")[3].replace("\n", ""))
    best_score = float(line.split("\t")[1])
    return best_weights, best_score




# *****************************************************************************
# ******* MAIN ****************************************************************
# *****************************************************************************
# goal_func = goal_EFFICIENCY

# Check if Optim Log Exists
for log in ["EFFICIENCY", "EGALITARIAN", "UTILITARIAN", "HARSANYIAN", "RAWLSIAN2"]:
    LOGNAME = log
    best_weights, best_score = loadLastOptim()
    createLogs(candidate_weights=best_weights)
    
        