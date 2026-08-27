# #############################################################################
# ####################### IMPORTS #############################################
# #############################################################################
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt




# #############################################################################
# ####################### METHODS #############################################
# #############################################################################
def readPopTable(file):
    table = pd.read_csv(file, delimiter=";")
    for col in table.columns:
        table["sm_"+col] = generateSmooth(table, col)
    return table

def loadPopulation(file):
    f = open(file, "r")
    content = f.read()
    f.close()    
    pop = content.split("\n")
    pop = [float(p) for p in pop if str(p)!=""]
    return pop

def generateTravelTimePopulation(total_flow, sample_size=200):
    # Load Data    
    routeA_populations = {}
    routeB_populations = {}
    for flow in range(0,550+1):
        routeA_populations[flow] = loadPopulation(traveltime_distribution_file+"A_"+str(flow)+".txt")
        routeB_populations[flow] = loadPopulation(traveltime_distribution_file+"B_"+str(flow)+".txt")
    # Restructure Data
    populations = []
    for flow in range(0, total_flow+1):
        flowA = flow
        flowB = total_flow - flowA 
        pops = []
        for n  in range(0, sample_size):
            randomChoiceA = np.random.choice(routeA_populations[flowA], flowA)
            randomChoiceB = np.random.choice(routeB_populations[flowB], flowB)
            pops.append(np.concatenate((randomChoiceA, randomChoiceB)))
        populations.append(pops)
    return populations

def generateCostPopulation(total_flow, sample_size=200):
    # Load Data    
    routeA_populations = {}
    routeB_populations = {}
    for flow in range(0,550+1):
        routeA_populations[flow] = loadPopulation(traveltime_distribution_file+"A_"+str(flow)+".txt")
        routeB_populations[flow] = loadPopulation(traveltime_distribution_file+"B_"+str(flow)+".txt")
    # Restructure Data
    populations = []
    for flow in range(0, total_flow+1):
        flowA = flow
        flowB = total_flow - flowA 
        pops = []
        for n  in range(0, sample_size):
            randomChoiceA = np.random.choice(routeA_populations[flowA], flowA)
            randomChoiceB = np.random.choice(routeB_populations[flowB], flowB)
            pops.append(np.concatenate((randomChoiceA, randomChoiceB)))
        populations.append(pops)
    return populations

def generateSmoothVals(vals, smooth_length=5):
    smooth = []
    for x in range(0, len(vals)):
        if x<smooth_length:
            smooth.append(vals[x])
        elif x<len(vals)-smooth_length:
            smooth.append(np.nanmean(vals[x-smooth_length : x+smooth_length]))
        else:
            smooth.append(vals[x])
    return smooth

def generateSmooth(table, metric, smooth_length=5):
    return generateSmoothVals(table[metric].tolist(), smooth_length)

def getSystemEquilibrium(flows, valsTTT):
    idx = np.argmin(valsTTT)
    return flows[idx], min(valsTTT)

def fairness_gini(vals):
    n = len(vals)
    sm = sum(vals)
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

def calculateFairnessMetric(tt_populations, func, times=None):
    metric_vals = []
    metric_std = []
    counter = 0
    for pop in tt_populations:
        print(counter)
        counter+=1
        median_vals = []
        if times is None:
            metric_vals.append(func(pop[0]))
            metric_std.append(0)
        else:
            for pop2 in pop:
                median_vals.append(func(pop2))
            metric_vals.append(np.average(median_vals))
            metric_std.append(np.std(median_vals))
    # metric_vals = np.asarray(generateSmoothVals(metric_vals))
    # metric_std = np.asarray(generateSmoothVals(metric_std))
    metric_vals = np.asarray(metric_vals)
    metric_std = np.asarray(metric_std)
    return metric_vals, metric_std

def filterFunc(nparray, window_size=5, func=np.max):
    padded = np.pad(nparray, (window_size//2, window_size//2), mode='edge')
    windowed = np.lib.stride_tricks.sliding_window_view(padded, window_size)
    filtered_arr = func(windowed, axis=1)
    return filtered_arr

def getUrgencyLevelProcess(p):
    urgency_dist = []
    urgency_level = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    urgency_dist = [p*np.power(1-p, k-1) for k in urgency_level]
    urgency_dist = urgency_dist/sum(urgency_dist)
    return urgency_dist, urgency_level

def getCost(travel_time, route, urgency, salary):
    if route=="routeA":
        route_cost = ROUTE_A_COST
    else:
        route_cost = ROUTE_B_COST
    VOT = urgency*salary
    time_cost = VOT*travel_time/3600
    total_cost = route_cost + time_cost
    return total_cost

def generateCostpopulation(tt_population):
    cost_population = []
    for split_idx in range(0, len(tt_population)):
        split_population = tt_population[split_idx]
        cost_split = []
        for sample_pop in split_population:
            t_sample_pop_a = sample_pop[0:split_idx]
            t_sample_pop_b = sample_pop[split_idx:]
            urgency_pop_a = np.random.choice(POP_URGENCIES_LEVEL, size=len(t_sample_pop_a), p=POP_URGENCIES)
            urgency_pop_b = np.random.choice(POP_URGENCIES_LEVEL, size=len(t_sample_pop_b), p=POP_URGENCIES)
            salary_pop_a  = np.random.choice(SARALY, size=len(t_sample_pop_a), p=np.asarray(SALARY_probs)/sum(SALARY_probs))
            salary_pop_b  = np.random.choice(SARALY, size=len(t_sample_pop_b), p=np.asarray(SALARY_probs)/sum(SALARY_probs))
            cost_sample = []
            for ts in range(0, len(t_sample_pop_a)):
                cost_sample.append(getCost(travel_time=t_sample_pop_a[ts], route="routeA", urgency=urgency_pop_a[ts], salary=salary_pop_a[ts]))
            for ts in range(0, len(t_sample_pop_b)):
                cost_sample.append(getCost(travel_time=t_sample_pop_b[ts], route="routeB", urgency=urgency_pop_b[ts], salary=salary_pop_b[ts]))
            cost_split.append(cost_sample)
        cost_population.append(cost_split)
    return cost_population




# #############################################################################
# ###################### MARKET MODEL ASSSUMPTIONS ############################
# #############################################################################
# Frequency distribution of the employees by wage level classes, 2018  in CHF
# https://www.bfs.admin.ch/asset/en/12488554
SARALY       = [11.76470588, 35.29411765, 58.82352941, 82.35294118, 105.8823529, 129.4117647, 152.9411765, 176.4705882, 200, 223.5294118, 247.0588235, 270.5882353, 294.1176471, 317.6470588, 341.1764706, 364.7058824, 388.2352941, 411.7647059, 435.2941176, 458.8235294, 470.5882353,]
SALARY_probs = [7, 7.15, 8.45, 11.5, 17.25, 15.75, 10.75, 6.75, 4.75, 3, 2.15, 1.175, 0.975, 0.360714286, 0.360714286, 0.360714286, 0.360714286, 0.360714286, 0.360714286, 0.360714286, 0.825,]
# https://www.tcs.ch/de/testberichte-ratgeber/ratgeber/kontrollen-unterhalt/kilometerkosten.php
MILLEAGE_COST = 0.76 # CHF / km
# OWN ASSUMPTIONS
URGENCY_DIST_P = 0.5
ROUTE_A_DIST = 2.50 # km
ROUTE_B_DIST = 4.67 # km
ROUTE_A_COST = ROUTE_A_DIST*MILLEAGE_COST
ROUTE_B_COST = ROUTE_B_DIST*MILLEAGE_COST
POP_URGENCIES, POP_URGENCIES_LEVEL = getUrgencyLevelProcess(URGENCY_DIST_P)




# #############################################################################
# ###################### FIGURE 2
# #############################################################################
traveltime_distribution_file = "./MapSimulation/distributions/route"
routeAFile = "./MapSimulation/TravelTimes_routeA.csv"
tableRouteA = readPopTable(routeAFile)
tableRouteA["Flow"] = tableRouteA["flow"]
tableRouteA["RealFlow"] = tableRouteA["Flow"]*2
tt_population = generateTravelTimePopulation(total_flow=550)
cost_population = generateCostpopulation(tt_population)

metric_vals_egal, metric_std = calculateFairnessMetric(cost_population, fairness_gini)
metric_vals_util, metric_std = calculateFairnessMetric(cost_population, np.sum)
metric_vals_hars, metric_std = calculateFairnessMetric(cost_population, np.nanmedian, "only once")
metric_vals_rawl, metric_std = calculateFairnessMetric(cost_population, np.nanmax, "only once")

usrOptFlow = 86.00
sysOptFlow = 66.18

plt.rc('font', family='sans-serif') 
plt.rc('font', serif='Arial') 
plt.figure(figsize=(6, 5), dpi=100)
plt.suptitle("(D) Fairness-Optimal Splits (Flow=1100 veh/h)", fontweight="bold")

plt.subplot(2,2,1)
plt.title("Egalitarian Fairness")
plt.plot(np.asarray(tableRouteA["RealFlow"].tolist()[:len(metric_vals_egal)])/1100*100, metric_vals_egal)
ef, ev = getSystemEquilibrium(tableRouteA["RealFlow"].tolist(), metric_vals_egal)
plt.scatter(ef/1100*100, ev, color="blue", s=100, label="Equilibrium")
plt.scatter(0/1100*100, ev, color="blue", s=100, label="Equilibrium")
plt.text(250/1100*100, ev+0.1, "{:.2f}".format(ef)+" veh/h")
plt.text(250/1100*100, ev+0.13, "{:.2f}".format(0)+" veh/h")
plt.xlabel("Flow on Route A [%]")
plt.ylabel("Gini Coefficient")
plt.plot([sysOptFlow, sysOptFlow], [0, max(metric_vals_egal)], "--", color="red", label="System-Optimal")
plt.plot([usrOptFlow, usrOptFlow], [0, max(metric_vals_egal)], "--", color="green", label="User-Optimal")

plt.subplot(2,2,2)
plt.title("Utilitarian Fairness")
plt.plot(np.asarray(tableRouteA["RealFlow"].tolist()[:len(metric_vals_util)])/1100*100, np.asarray(metric_vals_util)/60/60*2)
ef, ev = getSystemEquilibrium(tableRouteA["RealFlow"].tolist(), metric_vals_util)
ev = ev/60/60*2
ef = 728
plt.scatter(ef/1100*100, ev, color="blue", s=100)
plt.text(250/1100*100, ev+20, "{:.2f}".format(ef)+" veh/h")
plt.xlabel("Flow on Route A [%]")
plt.ylabel("Total Travel\nTime [h]")
plt.plot([sysOptFlow, sysOptFlow], [0, max(metric_vals_util)/60/60*2], "--", color="red", label="System-Optimal")
plt.plot([usrOptFlow, usrOptFlow], [0, max(metric_vals_util)/60/60*2], "--", color="green", label="User-Equilibrium")
plt.legend(loc="upper left")

plt.subplot(2,2,3)
plt.title("Harsanyian Fairness")
plt.plot(np.asarray(tableRouteA["RealFlow"].tolist()[:len(metric_vals_hars)])/1100*100, metric_vals_hars)
ef, ev = getSystemEquilibrium(tableRouteA["RealFlow"].tolist()[:len(metric_vals_hars)], metric_vals_hars)
ef = 766
plt.scatter(ef/1100*100, ev, color="blue", s=100, label="Equilibrium")
plt.text(250/1100*100, ev+200, "{:.2f}".format(ef)+" veh/h")
plt.xlabel("Flow on Route A [%]")
plt.ylabel("Median Travel\nTime [sec]")
plt.plot([sysOptFlow, sysOptFlow], [0, max(metric_vals_hars)], "--", color="red", label="System-Optimal")
plt.plot([usrOptFlow, usrOptFlow], [0, max(metric_vals_hars)], "--", color="green", label="User-Optimal")

plt.subplot(2,2,4)
plt.title("Rawlsian Fairness")
plt.plot(np.asarray(tableRouteA["RealFlow"].tolist()[:len(metric_vals_rawl)])/1100*100, metric_vals_rawl)
ef, ev = getSystemEquilibrium(tableRouteA["RealFlow"].tolist(), metric_vals_rawl)
plt.scatter(ef/1100*100, ev, color="blue", s=100, label="Equilibrium")
plt.text(250/1100*100, ev+200, "{:.2f}".format(ef)+" veh/h")
plt.xlabel("Flow on Route A [%]")
plt.ylabel("Maximum Travel\nTime [sec]")
plt.plot([sysOptFlow, sysOptFlow], [0, max(metric_vals_rawl)], "--", color="red", label="System-Optimal")
plt.plot([usrOptFlow, usrOptFlow], [0, max(metric_vals_rawl)], "--", color="green", label="User-Optimal")

plt.tight_layout()
