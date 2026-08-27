# *****************************************************************************
# ******* IMPORTS *************************************************************
# *****************************************************************************
import matplotlib.pyplot as plt
import ast
import pandas as pd
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
import matplotlib.patheffects as PathEffects
import matplotlib.gridspec as gridspec
import warnings
warnings.filterwarnings("ignore")




# *****************************************************************************
# ******* METHODS *************************************************************
# *****************************************************************************
SEEDS = [41, 42, 43, 44, 45, 46, 47, 48, 49, 50]
PASSENGER_COUNTS = {"car": 1.5, "truck": 10, "bus": 20, "bicycle": 1, "pedestrian": 1}
LOG_FOLDER = "logs"

def loadLastOptim(LOGNAME):
    f = open(LOG_FOLDER+"/optim_log_"+LOGNAME+".txt", "r")
    content = f.read()
    f.close()
    lines = content.split("\n")
    line = lines[-2]
    best_weights = ast.literal_eval(line.split("\t")[3].replace("\n", ""))
    best_score = float(line.split("\t")[1])
    return best_weights, best_score

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

"""
def loadDelayByMode(LOGNAME):
    vehicle_df, passenger_df = loadLogFile(LOG_FOLDER+"/LOG_tripinfo_"+LOGNAME+".xml")
    stats = passenger_df.groupby('Mode')['DelayPD'].agg(['mean', 'std', 'count']).reset_index()
    stats['Mode'] = stats['Mode'].str.capitalize()
    stats['Mode'] = pd.Categorical(stats['Mode'], categories=modes, ordered=True)
    stats = stats.sort_values('Mode').reset_index(drop=True)
    return stats
"""


def loadDelayByMode(LOGNAME):
    all_passenger_dfs = []
    # Load data for each seed
    for seed in SEEDS:
        _, passenger_df = loadLogFile(f"{LOG_FOLDER}/LOG_tripinfo_{LOGNAME}_{seed}.xml")
        all_passenger_dfs.append(passenger_df)
    # Concatenate all passenger dataframes
    combined_passenger_df = pd.concat(all_passenger_dfs, ignore_index=True)
    # Calculate statistics across all seeds
    stats = combined_passenger_df.groupby('Mode')['DelayPD'].agg(['mean', "median", 'std', 'count']).reset_index()
    # Calculate standard error of the mean
    stats['sem'] = stats['std'] / np.sqrt(stats['count'])
    # Format the Mode column
    stats['Mode'] = stats['Mode'].str.capitalize()
    stats['Mode'] = pd.Categorical(stats['Mode'], categories=modes, ordered=True)
    stats = stats.sort_values('Mode').reset_index(drop=True)
    return stats

def loadDelays(LOGNAME):
    vehicle_df, passenger_df = loadLogFile(LOG_FOLDER+"/LOG_tripinfo_"+LOGNAME+"_"+str(SEEDS[0])+".xml")
    vehicle_df = vehicle_df.dropna()
    passenger_df = passenger_df.dropna()
    return passenger_df

def goal_EFFICIENCY(vehicle_df, passenger_df):
    score = np.nansum(vehicle_df["TTT"])
    return score

def goal_UTILITARIAN(vehicle_df, passenger_df):
    score = np.nansum(passenger_df["TTT"])
    return score

def goal_HARSANYIAN(vehicle_df, passenger_df):
    score = np.nansum(passenger_df["DelayPD"])/len(passenger_df["DelayPD"])
    return score

def goal_RAWLSIAN1(vehicle_df, passenger_df):
    score = np.nanmax(passenger_df["DelayPD"])
    return score

def goal_RAWLSIAN2(vehicle_df, passenger_df):
    score = np.percentile(passenger_df["DelayPD"], 95)
    return score

def goal_EGALITARIAN(vehicle_df, passenger_df):
    vals = passenger_df["DelayPD"].tolist()
    score = gini(vals, len(vals), np.nanmean(vals), np.sum(vals))
    return score

def goal_AVVEHDEL(vehicle_df, passenger_df):
    score = sum(vehicle_df["DelayPD"])/len(vehicle_df["DelayPD"])
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

"""
def loadPerformances(LOGNAME):
    vehicle_df, passenger_df = loadLogFile(LOG_FOLDER+"/LOG_tripinfo_"+LOGNAME+".xml")
    vehicle_df = vehicle_df.dropna()
    passenger_df = passenger_df.dropna()
    return [goal_EFFICIENCY(vehicle_df, passenger_df),
            goal_UTILITARIAN(vehicle_df, passenger_df),
            goal_HARSANYIAN(vehicle_df, passenger_df),
            goal_RAWLSIAN2(vehicle_df, passenger_df),
            goal_EGALITARIAN(vehicle_df, passenger_df),
            goal_AVVEHDEL(vehicle_df, passenger_df)]
"""

def loadPerformances(LOGNAME):
    all_vehicle_dfs = []
    all_passenger_dfs = []
    # Load data for each seed
    for seed in SEEDS:
        vehicle_df, passenger_df = loadLogFile(f"{LOG_FOLDER}/LOG_tripinfo_{LOGNAME}_{seed}.xml")
        all_vehicle_dfs.append(vehicle_df.dropna())
        all_passenger_dfs.append(passenger_df.dropna())
    # Calculate performances for each seed
    performances = []
    for vehicle_df, passenger_df in zip(all_vehicle_dfs, all_passenger_dfs):
        seed_performance = [
            goal_EFFICIENCY(vehicle_df, passenger_df),
            goal_UTILITARIAN(vehicle_df, passenger_df),
            goal_HARSANYIAN(vehicle_df, passenger_df),
            goal_RAWLSIAN2(vehicle_df, passenger_df),
            goal_EGALITARIAN(vehicle_df, passenger_df),
            goal_AVVEHDEL(vehicle_df, passenger_df)
        ]
        performances.append(seed_performance)
    # Convert to numpy array for easier calculations
    performances_array = np.array(performances)
    # Calculate mean and standard error across seeds
    mean_performances = np.mean(performances_array, axis=0)
    median_performances = np.median(performances_array, axis=0)
    sem_performances = np.std(performances_array, axis=0) / np.sqrt(len(SEEDS))
    # Combine mean and standard error
    result = [(mean, med, sem) for mean, med, sem in zip(mean_performances, median_performances, sem_performances)]
    return result


# *****************************************************************************
# ******* MAIN ****************************************************************
# *****************************************************************************

modes = ["Car", "Truck", "Bus", "Bicycle", "Pedestrian"]

# LOAD OPTIMAL WEIGHTS
weights_eff, s = loadLastOptim("EFFICIENCY")
weights_ega, s = loadLastOptim("EGALITARIAN")
weights_har, s = loadLastOptim("HARSANYIAN")
weights_raw, s = loadLastOptim("RAWLSIAN2")
weights_uti, s = loadLastOptim("UTILITARIAN")
weight_sets = {
    "Efficiency": weights_eff,
    "Egalitarian": weights_ega,
    "Harsanyian": weights_har,
    "Utilitarian": weights_uti,
    "Rawlsian": weights_raw,
}

# Load AVERAGE AND STD DELAY PER MODE
stats_bm_eff = loadDelayByMode("EFFICIENCY")
stats_bm_ega = loadDelayByMode("EGALITARIAN")
stats_bm_har = loadDelayByMode("HARSANYIAN")
stats_bm_raw = loadDelayByMode("RAWLSIAN2")
stats_bm_uti = loadDelayByMode("UTILITARIAN")
stats_dataframes = {
    "Efficiency": stats_bm_eff,
    "Egalitarian": stats_bm_ega,
    "Harsanyian": stats_bm_har,
    "Utilitarian": stats_bm_uti,
    "Rawlsian": stats_bm_raw,
}
cmap = LinearSegmentedColormap.from_list("RedBlue", ["red", "blue"], N=len(modes))

# Load Delays
delays_eff = loadDelays("EFFICIENCY")
delays_ega = loadDelays("EGALITARIAN")
delays_har = loadDelays("HARSANYIAN")
delays_raw = loadDelays("RAWLSIAN2")
delays_uti = loadDelays("UTILITARIAN")
delays_df = {
    "Efficiency": delays_eff,
    "Egalitarian": delays_ega,
    "Harsanyian": delays_har,
    "Utilitarian": delays_raw,
    "Rawlsian": delays_raw,
}

# Load Performances
performance_eff = loadPerformances("EFFICIENCY")
performance_ega = loadPerformances("EGALITARIAN")
performance_har = loadPerformances("HARSANYIAN")
performance_raw = loadPerformances("RAWLSIAN2")
performance_uti = loadPerformances("UTILITARIAN")
performances = {
    "Efficiency": performance_eff,
    "Egalitarian": performance_ega,
    "Harsanyian": performance_har,
    "Utilitarian": performance_uti,
    "Rawlsian": performance_raw,
}





# *****************************************************************************
# ******* PLOTTING ************************************************************
# *****************************************************************************
# FIGURE 
plt.rc('font', family='sans-serif') 
plt.rc('font', serif='Arial') 
fig = plt.figure(LOG_FOLDER, figsize=(12, 7), dpi=100, constrained_layout=True)
gs = gridspec.GridSpec(3, 4, figure=fig, width_ratios=[2,2,1,1], height_ratios=[1,1,1])


ax1 = fig.add_subplot(gs[0, :2])
ax2 = fig.add_subplot(gs[0, 2:])
ax3 = fig.add_subplot(gs[1, 0:1])
ax4 = fig.add_subplot(gs[1, 1:2])
ax5 = fig.add_subplot(gs[2, 0:1])
ax6 = fig.add_subplot(gs[2, 1:2])
ax7 = fig.add_subplot(gs[1, 2:])
ax8 = fig.add_subplot(gs[2, 2:])


ax1.set_title("(D) Optimal Weights", fontweight="bold")
bar_width = 0.15
r = np.arange(len(modes))
for i, (label, weights) in enumerate(weight_sets.items()):
    color = cmap(i / (len(modes) - 1))
    position = [x + bar_width*i for x in r]
    ax1.bar(position, weights, width=bar_width, label=label, color=color)
ax1.set_ylabel('Pressure Weights')
ax1.set_xticks([r + bar_width*2 for r in range(len(modes))])
ax1.set_xticklabels(modes)
ax1.legend(title="Optimization Strategies", ncol=2, fontsize='small')
ax1.axhline(y=1, color='black', linestyle='--', linewidth=1)
ax1.set_yscale("symlog")


ax2.set_title("(E) Passenger Delay Change\n(Relative To Efficiency-Optimum)", fontweight="bold")
means = []
medians = []
labels = list(stats_dataframes.keys())
for label, df in stats_dataframes.items():
    means.append(df['mean'].values)
    medians.append(df["median"].values)
means = np.array(means)  # Shape: (num_stats, num_modes)
medians = np.array(medians)
x = np.arange(len(modes))  # Positions for modes on x-axis
differences = means - means[0]  # Subtract the first row (Efficiency) from all rows
differences = medians - medians[0]
bar_width = 0.15           # Width of each bar
for i in range(len(labels)):
    color = cmap(i / (len(modes) - 1))
    if i!=0:
        ax2.bar(x + i * bar_width, differences[i],  width=bar_width, label=labels[i], capsize=5, color=color)
ax2.set_ylabel("Median Passenger Delay [s/km]")
ax2.set_xticks(x + bar_width * (len(labels) - 1) / 2)
ax2.set_xticklabels(modes)
group_width = bar_width * (len(labels))
# Draw dashed lines for each group of bars
for i in range(len(modes)):
    # Start of the group
    ax2.axhline(y=0, xmin=(i * len(modes) + i) / (len(modes) * (len(modes) + 1)) -0.05,
                xmax=(i * len(modes) + i + group_width/1.7) / (len(modes) * (len(modes) + 1)) -0.05,
                color='red', linestyle='--', linewidth=1)
    # # End of the group
    ax2.axhline(y=0, xmin=(i * len(modes) + i + group_width/0.3) / (len(modes) * (len(modes) + 1)) -0.05,
                xmax=((i+1) * len(modes) + i + 1) / (len(modes) * (len(modes) + 1)) - 0.05,
                color='red', linestyle='--', linewidth=1)
    baseline_value = round(medians[0][i], 2)  # Round to 2 decimal places
    txt = ax2.text(x[i] + group_width/2, 0, f'{baseline_value}', 
             ha='center', va='top', fontsize=8, fontweight="bold", color="red")
    txt.set_path_effects([PathEffects.withStroke(linewidth=3, foreground='white')])
ax2.set_yscale("symlog")
ax2.axhline(y=0, color='black', linestyle='--', linewidth=1)


ax3.set_title("                                                       (F) Fairness Efficiency Tradeoff", fontweight="bold")
optims = ["Efficiency", "Egalitarian", "Harsanyian", "Utilitarian", "Rawlsian"]
i_mapper = {0:0, 1:4, 2:2, 3:3, 4:1}
for i in range(0, len(optims)): 
    x = performances[optims[i]][4][1]
    y = performances[optims[i_mapper[i]]][0][1]
    c = cmap(i_mapper[i] / (len(modes) - 1))
    s = performances[optims[i_mapper[i]]][5][1]
    print(optims[i_mapper[i]], x, y, c, s)
    ax3.scatter([x], [y], color=c, s=s/10)
    ax3.text(x, y, optims[i_mapper[i]], horizontalalignment='center')
ax3.set_xlabel("Egalitarian", fontweight="bold")
ax3.set_ylabel("Efficiency")
ax3.ticklabel_format(axis='y', style='sci', scilimits=(0,0))
ax3.ticklabel_format(axis='x', style='sci', scilimits=(0,0))


optims = ["Efficiency", "Egalitarian", "Harsanyian", "Utilitarian", "Rawlsian"]
i_mapper = {0:0, 1:2, 2:1, 3:3, 4:4}
for i in range(0, len(optims)): 
    x = performances[optims[i]][2][1]
    y = performances[optims[i_mapper[i]]][0][1]
    c = cmap(i_mapper[i] / (len(modes) - 1))
    s = performances[optims[i_mapper[i]]][5][1]
    ax4.scatter([x], [y], color=c, s=s/10)
    ax4.text(x, y, optims[i_mapper[i]], horizontalalignment='center')
ax4.set_xlabel("Harsanyian", fontweight="bold")
ax4.ticklabel_format(axis='y', style='sci', scilimits=(0,0))
ax4.ticklabel_format(axis='x', style='sci', scilimits=(0,0))


optims = ["Efficiency", "Egalitarian", "Harsanyian", "Utilitarian", "Rawlsian"]
for i in range(0, len(optims)): 
    x = performances[optims[i]][1][1]
    y = performances[optims[i]][0][1]
    c = cmap(i / (len(modes) - 1))
    s = performances[optims[i]][5][1]
    ax5.scatter([x], [y], color=c, s=s/10)
    ax5.text(x, y, optims[i], horizontalalignment='center')
ax5.set_xlabel("Utilitarian", fontweight="bold")
ax5.set_ylabel("Efficiency")
ax5.ticklabel_format(axis='y', style='sci', scilimits=(0,0))
ax5.ticklabel_format(axis='x', style='sci', scilimits=(0,0))


optims = ["Efficiency", "Egalitarian", "Harsanyian", "Utilitarian", "Rawlsian"]
for i in range(0, len(optims)): 
    x = performances[optims[i]][3][1]
    y = performances[optims[i]][0][1]
    c = cmap(i / (len(modes) - 1))
    s = performances[optims[i]][5][1]
    ax6.scatter([x], [y], color=c, s=s/10)
    ax6.text(x, y, optims[i], horizontalalignment='center', )
ax6.set_xlabel("Rawlsian", fontweight="bold")
ax6.ticklabel_format(axis='y', style='sci', scilimits=(0,0))
ax6.ticklabel_format(axis='x', style='sci', scilimits=(0,0))


ax7.set_title("(G) Passenger Delay Distribution (All Modes)", fontweight="bold")
optims = ["Efficiency", "Egalitarian", "Harsanyian", "Utilitarian", "Rawlsian"]
for i in range(0, len(optims)): 
    c = cmap(i / (len(modes) - 1))
    sns.kdeplot(data=delays_df[optims[i]]['DelayPD'], label=optims[i], color=c, shade=False, bw_adjust=0.5, ax = ax7,)
ax7.set_xlim(0,3000)
ax7.legend(title="Optimization Strategies", ncol=2, fontsize='small')
ax7.ticklabel_format(axis='y', style='sci', scilimits=(0,0))
ax7.ticklabel_format(axis='x', style='sci', scilimits=(0,0))
ax7.set_xlabel("Pasenger Delay [s/km]")



# delay_df = delays_df["Efficiency"]
# delay_df['Mode'] = delay_df['Mode'].str.capitalize()
# all_df = delay_df.copy()
# all_df['Mode'] = 'All'
# combined_df = pd.concat([delay_df, all_df])
# modes = ["All", "Car", "Truck", "Bus", "Bicycle", "Pedestrian"]
# sns.boxplot(x='Mode', y='DelayPD', data=combined_df, order=modes, ax=ax8)
# ax8.set_ylim(0,3000)


colors = [cmap(0 / (len(modes) - 1)), cmap(1 / (len(modes) - 1)), cmap(3 / (len(modes) - 1))]
strategies = ["Efficiency", "Egalitarian", "Utilitarian"]
dfs = []
for strategy in strategies:
    df = delays_df[strategy].copy()
    df['Mode'] = df['Mode'].str.capitalize()
    df['Strategy'] = strategy  # Add a column to identify the strategy
    all_df = df.copy()
    all_df['Mode'] = 'All'
    dfs.append(df)
    dfs.append(all_df)
combined_df = pd.concat(dfs, ignore_index=True)
modes = ["All", "Car", "Truck", "Bus", "Bicycle", "Pedestrian"]
sns.boxplot(x='Mode', y='DelayPD', hue='Strategy', data=combined_df, 
            order=modes, ax=ax8, palette=colors)
ax8.set_title("(H) Delay Distribution by Mode and Strategy", fontweight="bold")
ax8.set_ylabel("Passenger Delay [s/km]")
ax8.set_xlabel("")
# ax8.set_yscale('log')  # Set y-axis to log scale if the range is large
ax8.set_xticklabels(ax8.get_xticklabels())
ax8.set_ylim(0,3000)
ax8.legend(ncol=3, bbox_to_anchor=(0.5, -0.15), loc='upper center')

plt.tight_layout()
plt.subplots_adjust(wspace=0.5, hspace=0.3)
