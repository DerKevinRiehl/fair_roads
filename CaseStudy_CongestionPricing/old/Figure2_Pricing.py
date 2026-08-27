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
    return np.sum(pop_route==1), sum(pop_cost)

user_opt_flows = []
for tot_flow in ttt_x:
    user_opt_flows.append(getUserOptimum_Time(tableRouteA, tableRouteB, tot_flow ))


# #############################################################################
# ###################### FIGURE 0 - VOTs
# #############################################################################

plt.rc('font', family='sans-serif') 
plt.rc('font', serif='Arial') 
plt.figure(figsize=(12, 3.5), dpi=100)
plt.suptitle("(E) System-Optimal Road Pricing", fontweight="bold")


plt.subplot(1,3,1)
# Frequency distribution of the employees by wage level classes, 2018 
# https://www.bfs.admin.ch/asset/en/12488554
vots       = [11.76470588, 35.29411765, 58.82352941, 82.35294118, 105.8823529, 129.4117647, 152.9411765, 176.4705882, 200, 223.5294118, 247.0588235, 270.5882353, 294.1176471, 317.6470588, 341.1764706, 364.7058824, 388.2352941, 411.7647059, 435.2941176, 458.8235294, 470.5882353,]
vots_probs = [7, 7.15, 8.45, 11.5, 17.25, 15.75, 10.75, 6.75, 4.75, 3, 2.15, 1.175, 0.975, 0.360714286, 0.360714286, 0.360714286, 0.360714286, 0.360714286, 0.360714286, 0.360714286, 0.825,]
plt.gca().bar(vots, vots_probs, width=10.0, label=vots)
plt.gca().set_ylabel('Share of Population [%]')
plt.gca().set_xlabel("Value of Time [€/h]")
plt.gca().set_title('Value of Time Distribution')





plt.subplot(1,3,2)

total_flow_real = 1100
x_prices = []
y_flowRouteA = []
y_revs = []
y_costs = []
for alda in range(0, 60): # vary from 0 euro to 6 euro
    price_routeA = alda/10 
    print(price_routeA)
    x_prices.append(price_routeA)
    flowB, totCost = getUserOptimum_Money(tableRouteA, tableRouteB, total_flow_real, price_routeA)
    flowA = total_flow_real-flowB
    rev = flowA*price_routeA
    y_flowRouteA.append(total_flow_real-flowB)  
    y_revs.append(rev)
    y_costs.append(totCost)
y_flowRouteA = generateSmoothVals(y_flowRouteA)
y_flowRouteA = np.asarray(y_flowRouteA)/1100*100
y_revs = generateSmoothVals(y_revs)
y_costs = generateSmoothVals(y_costs)
l1 = plt.gca().plot(x_prices, y_flowRouteA, label="User Equilibrium")
l2 = plt.gca().plot([0, 6], [ttt_y[-1]/1100*100, ttt_y[-1]/1100*100], "--", color="black", label="System Optimum")
plt.ylabel("Flow on Route A [%]")
plt.xlabel("Price for Route A [€]")
plt.title("Total Flow = 1100 veh/h")
optimal_flowA = ttt_y[-1]/1100*100
price_index = np.argmin(np.abs(np.asarray(y_flowRouteA)-optimal_flowA))
optimal_price = x_prices[price_index]
optimal_flowA = y_flowRouteA[price_index]
plt.scatter([optimal_price], [optimal_flowA], color="red", label="Optimal Price", s=100)
plt.legend(loc="upper right")

axs = plt.gca().twinx()
axs.set_ylabel("Monetary Costs [€]")
l3 = axs.plot(x_prices, (np.asarray(y_costs)-np.asarray(y_revs)), label="Delay Costs", color="green", zorder=99)
l4 = axs.plot(x_prices, np.asarray(y_costs), label="Total Costs", color="gray", zorder=99)
axs.set_ylim([13000, 20000])
plt.gca().legend(loc="lower left")
# lns = l1+l2+l3+l4
# labs = [l.get_label() for l in lns]
# ax.legend(lns, labs, loc="lower left")





plt.subplot(1,3,3)

# tot_flows = []
# for tot_flow in range(1100, 500-1, -2):
#     tot_flows.append(tot_flow)
# tot_flows = []

# opt_prices = []
# opt_tot_costs = []
# opt_del_costs = []
# last_opt_price = 3.5
# for tot_flow in range(1100, 500-1, -2):
#     tidx = ttt_x.index(tot_flow)
#     should_optimal_flowA = ttt_y[tidx]
    
#     if tot_flow<=730:
#         opt_price = 0
#     else:
#         flow_dist_optimal = []
#         x_prices = []
#         y_revs = []
#         y_costs = []
#         for alda in range(int(last_opt_price*10-10), int(last_opt_price*10+10)): # vary from minus to plus one euro (only 20 calculations)
#             price_routeA = alda/10 
#             x_prices.append(price_routeA)
#             flowB, totCost = getUserOptimum_Money(tableRouteA, tableRouteB, tot_flow, price_routeA)
#             flowA = tot_flow-flowB
#             rev = flowA*price_routeA
#             # y_flowRouteA.append(tot_flow-flowB)  
#             y_revs.append(rev)
#             y_costs.append(totCost)
#             flow_dist_optimal.append(abs(flowA-should_optimal_flowA))
#         bestIdx = np.argmin(flow_dist_optimal)
#         opt_price = np.max(x_prices[bestIdx], 0)
        
#     last_opt_price = opt_price
#     opt_prices.append(opt_price)
    
#     flowB, totCost = getUserOptimum_Money(tableRouteA, tableRouteB, tot_flow, opt_price)
#     flowA = tot_flow-flowB
#     rev = flowA*opt_price
#     opt_tot_costs.append(totCost)
#     opt_del_costs.append(totCost-rev)
    
#     tot_flows.append(tot_flow)
#     print(tot_flow, opt_price)
    
# opt_prices_sm = generateSmoothVals(opt_prices)
# opt_tot_costs_sm = generateSmoothVals(opt_tot_costs)
# opt_del_costs_sm = generateSmoothVals(opt_del_costs)

# def saveTXT(file, lst):
#     f = open(file, "w+")
#     for l in lst:
#         f.write(str(l))
#         f.write("\n")
#     f.close()
# saveTXT("opt_prices_sm.txt", opt_prices_sm)
# saveTXT("opt_tot_costs_sm.txt", opt_tot_costs_sm)
# saveTXT("opt_del_costs_sm.txt", opt_del_costs_sm)
# saveTXT("tot_flows.txt", tot_flows)

opt_prices_sm = loadPopulation("opt_prices_sm.txt")
opt_tot_costs_sm = loadPopulation("opt_tot_costs_sm.txt")
opt_del_costs_sm = loadPopulation("opt_del_costs_sm.txt")
tot_flows = loadPopulation("tot_flows.txt")

ax_first = plt.gca()
ax_first.set_ylim([-3,4])
plt.plot(tot_flows, opt_prices_sm, color="red", label="Optimal Price")
plt.legend(loc="upper left")
plt.xlabel("Flow [veh/h]")
plt.ylabel("Price [€]")
plt.title("System Optimal Price & Costs")

ax = plt.gca().twinx()
ax.set_ylim([min(opt_tot_costs_sm), 19000])
ax.set_ylabel("Monetary Costs [€]")
ax.plot(tot_flows, np.asarray(opt_del_costs_sm), label="Delay Costs", color="green", zorder=99)
ax.plot(tot_flows, np.asarray(opt_tot_costs_sm), label="Total Costs", color="gray", zorder=99)
ax.legend(loc="lower right")
ax.set_ylim([5000,20000])
# 730 vehicles per hour is knackpunkt wo sie sich trennen

plt.tight_layout()
