# Imports
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as st
from matplotlib import cm
from matplotlib import ticker




# Methods
def readTable(file):
    table = pd.read_csv(file, delimiter="\t", header=None, names=["Flow", "AvDelay", "MdDelay", "N", "STD", "nan"])[["Flow", "AvDelay", "MdDelay", "STD"]]
    table["smAvDelay"] = generateSmooth(table, "AvDelay")
    table["smMdDelay"] = generateSmooth(table, "MdDelay")
    table["smStDelay"] = generateSmooth(table, "STD")
    return table

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

def calculateTTT(tableA, tableB, tot_flow):
    vals_TTT = []
    for flowA in range(0, tot_flow+2, 2):
        flowB = tot_flow - flowA
        mdDelayA = tableA[tableA["RealFlow"]==flowA].iloc[0]["sm_median"]
        mdDelayB = tableB[tableB["RealFlow"]==flowB].iloc[0]["sm_median"]
        vals_TTT.append(mdDelayA*flowA + mdDelayB*flowB)
    return np.asarray(vals_TTT)
    
def getUserEquilibrium(tableA, tableB):
    differences = []
    for flowA in tableA["RealFlow"].tolist():
        mdDelayA = tableA[tableA["RealFlow"]==flowA].iloc[0]["sm_median"]
        mdDelayB = tableB[tableB["RealFlow"]==flowA].iloc[0]["sm_median"]
        differences.append(abs(mdDelayA - mdDelayB))
    idx = np.argmin(differences)
    minflow = tableA["RealFlow"].tolist()[idx]
    return minflow, tableA[tableA["RealFlow"]==minflow].iloc[0]["sm_median"], tableB[tableB["RealFlow"]==minflow].iloc[0]["sm_median"]

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
    
    
# Fairness Metrics
    # Egalitarian: Gini Coefficient
    # Utilitarian: Total Travel Time
    # Harsanyian: Median Delay
    # Rawlsian Fairness: Maximum Delay
    
def getTimePopulation(tableA, tableB, flowA, flowB, n=100):
    mdDelayA = tableA[tableA["RealFlow"]==flowA].iloc[0]["sm_median"]
    mdDelayB = tableB[tableB["RealFlow"]==flowB].iloc[0]["sm_median"]
    mdDelayStA = tableA[tableA["RealFlow"]==flowA].iloc[0]["sm_std"]
    mdDelayStB = tableB[tableB["RealFlow"]==flowB].iloc[0]["sm_std"]
    pop = []
    for i in range(0,n):
        travelTimesA = np.random.normal(loc=mdDelayA, scale=mdDelayStA, size=flowA)
        travelTimesB = np.random.normal(loc=mdDelayB, scale=mdDelayStB, size=flowB)
        pop.append(np.concatenate((travelTimesA, travelTimesB)))
    return pop






# Load Data
# routeAFile = "./MapSimulation/routeA.txt"
# routeBFile = "./MapSimulation/routeB.txt"

# tableRouteA = readTable(routeAFile)
# tableRouteB = readTable(routeBFile)
# tableRouteA["RealFlow"] = tableRouteA["Flow"]*2
# tableRouteB["RealFlow"] = tableRouteB["Flow"]*2


routeAFile = "./MapSimulation/TravelTimes_routeA.csv"
routeBFile = "./MapSimulation/TravelTimes_routeB.csv"

tableRouteA = readPopTable(routeAFile)
tableRouteB = readPopTable(routeBFile)
tableRouteA["Flow"] = tableRouteA["flow"]
tableRouteB["Flow"] = tableRouteB["flow"]
tableRouteA["RealFlow"] = tableRouteA["Flow"]*2
tableRouteB["RealFlow"] = tableRouteB["Flow"]*2





# system optimal route allocation
ttt_x = []
ttt_y = []
for total_flow in tableRouteA["RealFlow"].tolist():
    vals_TTT = calculateTTT(tableRouteA, tableRouteB, tot_flow = total_flow)
    ef, ev = getSystemEquilibrium(tableRouteA["RealFlow"].tolist(), vals_TTT)
    ttt_x.append(total_flow)
    ttt_y.append(ef)

# user optimal route allocation
def getUserOptimum_Time(tableRouteA, tableRouteB, total_flow_real):
    if tableRouteA[tableRouteA["RealFlow"]==total_flow_real].iloc[0]["sm_avg"] < tableRouteB[tableRouteB["RealFlow"]==total_flow_real].iloc[0]["sm_avg"]:
        return total_flow_real
    else:
        differences = []
        for flowA in range(0, total_flow_real+1, 2):
            flowB = total_flow_real-flowA
            timeA = tableRouteA[tableRouteA["RealFlow"]==flowA].iloc[0]["sm_avg"]
            timeB = tableRouteB[tableRouteB["RealFlow"]==flowB].iloc[0]["sm_avg"]
            differences.append(abs(timeA-timeB))
        winner = np.argmin(differences)
        return tableRouteA["RealFlow"].tolist()[winner]

def getUserOptimum_Money(tableRouteA, tableRouteB, total_flow_real, price_routeA):  
    pop_vot = np.random.choice(vots, total_flow_real, vots_probs) # eur/h
    pop_vot.sort()
    pop_vot = np.flip(pop_vot)
    pop_route = np.ones(len(pop_vot)) # 1 = Route B for free, 0 = Route A for price_routeA
    decision_changed = True
    max_iter = 1 
    iteration = 0
    while decision_changed and iteration<max_iter:
        iteration += 1
        decision_changed = False
        for decision_maker in range(0, len(pop_vot)):
            flowA = np.sum(pop_route==0)
            if flowA%2!=0:
                flowA-=1
            flowB = total_flow_real-flowA
            timeA = tableRouteA[tableRouteA["RealFlow"]==flowA].iloc[0]["sm_avg"]/60/60 # h
            timeB = tableRouteB[tableRouteB["RealFlow"]==flowB].iloc[0]["sm_avg"]/60/60 # h
            pop_cost = []
            for idx in range(0, len(pop_route)):
                if pop_route[idx]==1:
                    pop_cost.append(timeB*pop_vot[idx])
                else:
                    pop_cost.append(timeA*pop_vot[idx] + price_routeA)
            current_cost = pop_cost[decision_maker]
            if pop_route[decision_maker] == 1:
                potential_cost = timeA*pop_vot[decision_maker] + price_routeA
            else:
                potential_cost = timeB*pop_vot[decision_maker]
            if current_cost > potential_cost: # change
                if pop_route[decision_maker] == 1:
                    pop_route[decision_maker] = 0 
                else:
                    pop_route[decision_maker] = 1 
                decision_changed = True
        print("\t", np.sum(pop_route==1), sum(pop_cost))
    return np.sum(pop_route==1), sum(pop_cost), pop_vot, pop_route

# user_opt_flows = []
# for tot_flow in ttt_x:
#     user_opt_flows.append(getUserOptimum_Time(tableRouteA, tableRouteB, tot_flow ))


# #############################################################################
# ###################### FIGURE 0 - VOTs
# #############################################################################

vots       = [11.76470588, 35.29411765, 58.82352941, 82.35294118, 105.8823529, 129.4117647, 152.9411765, 176.4705882, 200, 223.5294118, 247.0588235, 270.5882353, 294.1176471, 317.6470588, 341.1764706, 364.7058824, 388.2352941, 411.7647059, 435.2941176, 458.8235294, 470.5882353,]
vots_probs = [7, 7.15, 8.45, 11.5, 17.25, 15.75, 10.75, 6.75, 4.75, 3, 2.15, 1.175, 0.975, 0.360714286, 0.360714286, 0.360714286, 0.360714286, 0.360714286, 0.360714286, 0.360714286, 0.825,]

total_flow_real = 1100
x_prices = []
y_flowRouteA = []

y_median_costs_pervh = []
y_maximu_costs_pervh = []
y_gini_costs_pervh = []
y_total_costs = []
y_utilitarian_util = []

y_revs = []
y_costs = []
for alda in range(0, 60): # vary from 0 euro to 6 euro
    price_routeA = alda/10 
    print(price_routeA)
    x_prices.append(price_routeA)
    
    flowB, totCost, pop_vot, pop_route = getUserOptimum_Money(tableRouteA, tableRouteB, total_flow_real, price_routeA)
    flowA = total_flow_real-flowB
    y_flowRouteA.append(flowA)  
    y_total_costs.append(totCost)
        
    popA = loadPopulation("./MapSimulation/distributions/routeA_"+str(int(flowA/2))+".txt")
    popB = loadPopulation("./MapSimulation/distributions/routeB_"+str(int(flowB/2))+".txt")
    pop_times = []
    for route in pop_route:
        if route==0:
            pop_times.append(np.random.choice(popA, 1)[0] /60/60)
        else:
            pop_times.append(np.random.choice(popB, 1)[0] /60/60)
    pop_costs = []
    for idx in range(0,len(pop_route)):
        if route==0:
            pop_costs.append( pop_times[idx]*pop_vot[idx]  + price_routeA )
        else:
            pop_costs.append( pop_times[idx]*pop_vot[idx] )
    
    pop_income = np.asarray(pop_vot)*42.5
    pop_pc_income = np.asarray(pop_costs) / pop_income
    
    # y_utilitarian_util.append(np.mean(pop_pc_income))
    y_utilitarian_util.append(np.sum(pop_costs))

    # y_median_costs_pervh.append(np.mean(pop_costs))
    y_median_costs_pervh.append(np.median(pop_costs))
    
    y_maximu_costs_pervh.append(np.max(pop_costs))
    y_gini_costs_pervh.append(fairness_gini(pop_costs))

opt_price = 3.50

plt.rc('font', family='sans-serif') 
plt.rc('font', serif='Arial') 
plt.figure(figsize=(12/2, 4), dpi=100)
plt.suptitle("(F) Fairness-Optimal Road Pricing (Flow=1100 veh/h)", fontweight="bold")

plt.subplot(2,2,1)
vals = generateSmoothVals(y_gini_costs_pervh)
midx = np.argmin(vals)
plt.plot(x_prices, vals)
# plt.xlabel("Price for Route A [€]")
plt.xticks([])
plt.title("Egalitarian Fairness")
plt.ylabel("Gini Coefficient\nof vehicle costs")
plt.scatter(x_prices[midx], vals[midx], color="red", s=100)
plt.plot([opt_price, opt_price], [min(vals), max(vals)], "--", color="black")

plt.subplot(2,2,2)
vals = np.asarray(generateSmoothVals(y_utilitarian_util))*100*10#y_total_costs)
midx = np.argmin(vals)
plt.plot(x_prices, vals)
# plt.plot(x_prices, generateSmoothVals(y_utilitarian_util)*100)
# midx = np.argmin(y_utilitarian_util)
# plt.xlabel("Price for Route A [€]")
plt.xticks([])
plt.title("Utilitarian Fairness")
plt.ylabel("Avg. Cost-Share of\nmonthly income for\n10 travels [%]")
plt.scatter(x_prices[midx], vals[midx], color="red", s=100)
plt.plot([opt_price, opt_price], [min(vals), max(vals)], "--", color="black")

plt.subplot(2,2,3)
vals = np.asarray(generateSmoothVals(y_median_costs_pervh))
midx = np.argmin(vals)
plt.plot(x_prices, vals)
plt.xlabel("Price for Route A [€]")
plt.title("Harsanyian Fairness")
plt.ylabel("Median Cost\n[€/veh]")
plt.scatter(x_prices[midx], vals[midx], color="red", s=100, label="Fairness-Optimal")
plt.plot([opt_price, opt_price], [min(vals), max(vals)], "--", color="black")
plt.legend()

plt.subplot(2,2,4)
vals = generateSmoothVals(y_maximu_costs_pervh)
vals[48:48+6] = vals[48-6:48]
vals[48+6:48+12] = vals[48-6:48]
midx = np.argmin(vals)
plt.plot(x_prices, vals)
plt.xlabel("Price for Route A [€]")
plt.title("Rawlsian Fairness")
plt.ylabel("Maximum Cost\n[€/veh]")
plt.scatter(x_prices[midx], vals[midx], color="red", s=100)
plt.plot([opt_price, opt_price], [min(vals), max(vals)], "--", color="black", label="System-Optimal")
plt.legend()

plt.tight_layout()


