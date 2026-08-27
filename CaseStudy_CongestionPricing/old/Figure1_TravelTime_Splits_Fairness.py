# #############################################################################
# ####################### IMPORTS #############################################
# #############################################################################
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as st




# #############################################################################
# ####################### METHODS #############################################
# #############################################################################
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






# #############################################################################
# ###################### FIGURE 0
# #############################################################################

# system optimal route allocation
ttt_x = []
ttt_y = []
for total_flow in tableRouteA["RealFlow"].tolist():
    vals_TTT = calculateTTT(tableRouteA, tableRouteB, tot_flow = total_flow)
    # plt.plot(tableRouteA["RealFlow"], vals_TTT)
    ef, ev = getSystemEquilibrium(tableRouteA["RealFlow"].tolist(), vals_TTT)
    ttt_x.append(total_flow)
    ttt_y.append(ef)

# user optimal route allocation
def getUserOptimum(tableRouteA, tableRouteB, total_flow_real):
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

user_opt_flows = []
for tot_flow in ttt_x:
    user_opt_flows.append(getUserOptimum(tableRouteA, tableRouteB, tot_flow ))


plt.rc('font', family='sans-serif') 
plt.rc('font', serif='Arial') 
plt.figure(figsize=(6, 5), dpi=100)
plt.suptitle("(C) Splits & Equlibria", fontweight="bold")

plt.subplot(2,1,1)
plt.title("System optimum (Flow=1100 veh/h)")
plt.xlabel("Flow on Route A [%]")
plt.ylabel("Total Travel\nTime [h]")
vals_TTT = calculateTTT(tableRouteA, tableRouteB, tot_flow = 550*2)
ef, ev = getSystemEquilibrium(tableRouteA["RealFlow"].tolist(), vals_TTT)
plt.plot(tableRouteA["RealFlow"]/1100*100, np.asarray(vals_TTT)/60/60)
plt.scatter(ef/1100*100, ev/60/60, color="red", s=100)
plt.text(ef/1100*100-60, ev/60/60+35, "Flow: "+str(ef)+" veh/h\nTravel time: "+"{:.2f}".format(ev/60/60)+" h("+"{:.2f}".format(ev/60/60/1100)+" h/veh)")

plt.subplot(2,2,3)
plt.title("System optimum & User equilibrium")
plt.xlabel("Flow [veh/hour]")
plt.ylabel("Av. Vehicle\nTravel Time [sec]")
flow = []
avtraveltime = []
for i in range(0, len(ttt_x)):
    tot_flow = ttt_x[i]
    flowA = user_opt_flows[i] # getUserOptimum(tableRouteA, tableRouteB, tot_flow )
    flowB = tot_flow-flowA
    timeA = tableRouteA[tableRouteA["RealFlow"]==flowA].iloc[0]["sm_avg"]
    timeB = tableRouteB[tableRouteB["RealFlow"]==flowB].iloc[0]["sm_avg"]
    avtime = (flowA*timeA + flowB*timeB) / tot_flow
    flow.append(tot_flow)
    avtraveltime.append(avtime)
plt.plot(flow,avtraveltime, label="User", color="green")
flow = []
avtraveltime = []
for i in range(0, len(ttt_x)):
    tot_flow = ttt_x[i]
    flowA = ttt_y[i]
    flowB = tot_flow-flowA
    timeA = tableRouteA[tableRouteA["RealFlow"]==flowA].iloc[0]["sm_avg"]
    timeB = tableRouteB[tableRouteB["RealFlow"]==flowB].iloc[0]["sm_avg"]
    avtime = (flowA*timeA + flowB*timeB) / tot_flow
    flow.append(tot_flow)
    avtraveltime.append(avtime)
plt.plot(flow,avtraveltime, label="System", color="red")
plt.legend()

plt.subplot(2,2,4)
plt.title("")
plt.xlabel("Flow [veh/hour]")
plt.ylabel("Flow on\nRoute A [%]")
plt.plot(ttt_x, np.asarray(user_opt_flows)/np.asarray(ttt_x)*100, label="User Optimum", color="green")
plt.plot(ttt_x, np.asarray(ttt_y)/np.asarray(ttt_x)*100, label="System Optimum", color="red")
plt.ylim([50,110])
plt.tight_layout()

import sys
sys.exit(0)







# #############################################################################
# ###################### FIGURE 1
# #############################################################################

plt.rc('font', family='sans-serif') 
plt.rc('font', serif='Arial') 
plt.figure(figsize=(12/2, 3), dpi=100)
plt.suptitle("(B) Travel Time Distribution", fontweight="bold")

plt.subplot(1,3,1)
plt.title("Route A & B")
plt.plot(tableRouteA["RealFlow"], tableRouteA["sm_median"], label="Route A")
plt.fill_between(tableRouteA["RealFlow"], tableRouteA["sm_pc20"], tableRouteA["sm_pc80"], alpha=0.5)
plt.plot(tableRouteB["RealFlow"], tableRouteB["sm_median"], label="Route B")
plt.fill_between(tableRouteB["RealFlow"], tableRouteB["sm_pc20"], tableRouteB["sm_pc80"], alpha=0.5)
flow, mdA, mdB = getUserEquilibrium(tableRouteA, tableRouteB)
# plt.scatter(flow, mdA, color="red", s=100, label="Equilibrium")
plt.legend(loc="upper left")
plt.xlabel("Flow [veh/h]")
plt.ylabel("Vehicle Travel Time [sec]")

def drawPopulationPDF(file, color, label):
    x = loadPopulation(file)
    plt.hist(x, density=True, bins=82, label="Data", color="white")
    mn, mx = plt.xlim()
    plt.xlim(mn, mx)
    kde_xs = np.linspace(mn, mx, 300)
    kde = st.gaussian_kde(x)
    plt.plot(kde_xs, kde.pdf(kde_xs), color=color, label=label)

plt.subplot(1,3,2)
plt.title("Flow = 900 veh/h")
drawPopulationPDF("./MapSimulation/distributions/routeA_450.txt", '#1f77b4', "Route A")
drawPopulationPDF("./MapSimulation/distributions/routeB_450.txt", "orange", "Route B")
plt.ylabel("Probability [%]")
plt.xlabel("Vehicle Travel Time [sec]")
plt.gca().set_yticklabels([])
plt.ylim([0, 0.018])

plt.subplot(1,3,3)
plt.title("Flow = 1000 veh/h")
drawPopulationPDF("./MapSimulation/distributions/routeA_500.txt", '#1f77b4', "Route A")
drawPopulationPDF("./MapSimulation/distributions/routeB_500.txt", "orange", "Route B")
plt.ylabel("Probability [%]")
plt.xlabel("Vehicle Travel Time [sec]")
plt.gca().set_yticklabels([])
plt.ylim([0, 0.018])


plt.tight_layout()








# #############################################################################
# ###################### FIGURE 2
# #############################################################################

routeA_populations = {}
routeB_populations = {}
for flow in range(0,550+1):
    routeA_populations[flow] = loadPopulation("./MapSimulation/distributions/routeA_"+str(flow)+".txt")
    routeB_populations[flow] = loadPopulation("./MapSimulation/distributions/routeB_"+str(flow)+".txt")

def generatePopulation(total_flow, sample_size=200):
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

def calculateFairnessMetric(populations, func, times=None):
    metric_vals = []
    metric_std = []
    counter = 0
    for pop in populations:
        print(counter)
        counter+=1
        median_vals = []
        if times is  None:
            metric_vals.append(func(pop[0]))
            metric_std.append(0)
        else:
            for pop2 in pop:
                median_vals.append(func(pop2))
            metric_vals.append(np.average(median_vals))
            metric_std.append(np.std(median_vals))
    metric_vals = np.asarray(generateSmoothVals(metric_vals))
    metric_std = np.asarray(generateSmoothVals(metric_std))
    return metric_vals, metric_std


populationsA = generatePopulation(total_flow=550)
populationsB = generatePopulation(total_flow=300)
populationsC = generatePopulation(total_flow=400)
populationsD = generatePopulation(total_flow=500)

metric_vals_egal, metric_std = calculateFairnessMetric(populationsA, fairness_gini)
metric_vals_util, metric_std = calculateFairnessMetric(populationsA, np.sum)
metric_vals_hars, metric_std = calculateFairnessMetric(populationsA, np.nanmedian, "only once")
metric_vals_rawl, metric_std = calculateFairnessMetric(populationsA, np.nanmax, "only once") #


usrOptFlow = 86.00
sysOptFlow = 66.18

plt.rc('font', family='sans-serif') 
plt.rc('font', serif='Arial') 
plt.figure(figsize=(6, 5), dpi=100)
plt.suptitle("(D) Fairness-Optimal Splits (Flow=1100 veh/h)", fontweight="bold")

plt.subplot(2,2,1)
plt.title("Egalitarian Fairness")
plt.plot(np.asarray(tableRouteA["RealFlow"].tolist()[:len(metric_vals_egal)])/1100*100, metric_vals_egal)
# plt.fill_between(tableRouteA["RealFlow"].tolist(), metric_vals-metric_std, metric_vals+metric_std, alpha=0.5)
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
# plt.fill_between(tableRouteA["RealFlow"].tolist(), metric_vals-metric_std, metric_vals+metric_std, alpha=0.5)
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
# plt.fill_between(tableRouteA["RealFlow"].tolist()[:len(metric_vals)], metric_vals-metric_std, metric_vals+metric_std, alpha=0.5)
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
# plt.fill_between(tableRouteA["RealFlow"].tolist(), metric_vals-metric_std, metric_vals+metric_std, alpha=0.5)
ef, ev = getSystemEquilibrium(tableRouteA["RealFlow"].tolist(), metric_vals_rawl)
plt.scatter(ef/1100*100, ev, color="blue", s=100, label="Equilibrium")
plt.text(250/1100*100, ev+200, "{:.2f}".format(ef)+" veh/h")
plt.xlabel("Flow on Route A [%]")
plt.ylabel("Maximum Travel\nTime [sec]")
plt.plot([sysOptFlow, sysOptFlow], [0, max(metric_vals_rawl)], "--", color="red", label="System-Optimal")
plt.plot([usrOptFlow, usrOptFlow], [0, max(metric_vals_rawl)], "--", color="green", label="User-Optimal")

plt.tight_layout()
