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

def getSystemEquilibrium(flows, valsTTT):
    idx = np.argmin(valsTTT)
    return flows[idx], min(valsTTT)

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

def filterFunc(nparray, window_size=5, func=np.max):
    padded = np.pad(nparray, (window_size//2, window_size//2), mode='edge')
    windowed = np.lib.stride_tricks.sliding_window_view(padded, window_size)
    filtered_arr = func(windowed, axis=1)
    return filtered_arr


# #############################################################################
# ###################### FIGURE 0
# #############################################################################
routeAFile = "./MapSimulation/TravelTimes_routeA.csv"
routeBFile = "./MapSimulation/TravelTimes_routeB.csv"
tableRouteA = readPopTable(routeAFile)
tableRouteB = readPopTable(routeBFile)
tableRouteA["Flow"] = tableRouteA["flow"]
tableRouteB["Flow"] = tableRouteB["flow"]
tableRouteA["RealFlow"] = tableRouteA["Flow"]*2
tableRouteB["RealFlow"] = tableRouteB["Flow"]*2

total_flow = 1100

ttt_x = []
ttt_y = []
for total_flow in tableRouteA["RealFlow"].tolist():
    vals_TTT = calculateTTT(tableRouteA, tableRouteB, tot_flow = total_flow)
    ef, ev = getSystemEquilibrium(tableRouteA["RealFlow"].tolist(), vals_TTT)
    ttt_x.append(total_flow)
    ttt_y.append(ef)
user_opt_flows = []
for tot_flow in ttt_x:
    user_opt_flows.append(getUserOptimum(tableRouteA, tableRouteB, tot_flow ))






plt.rc('font', family='sans-serif') 
plt.rc('font', serif='Arial') 
plt.figure(figsize=(6, 4), dpi=100)
plt.suptitle("(C) Splits & Equlibria", fontweight="bold")

plt.subplot(2,1,1)
plt.title("System optimum (Flow="+str(total_flow)+" veh/h)")
plt.xlabel("Flow on Route A [%]")
plt.ylabel("Total Travel\nTime [h]")
vals_TTT = calculateTTT(tableRouteA, tableRouteB, tot_flow=total_flow)
ef, ev = getSystemEquilibrium(tableRouteA["RealFlow"].tolist(), vals_TTT)
yvals = np.asarray(vals_TTT)/60/60
filtered_yvals = filterFunc(yvals, window_size=21, func=np.mean)
plt.plot(tableRouteA["RealFlow"]/total_flow*100, filtered_yvals)
plt.scatter(ef/total_flow*100, ev/60/60, color="red", s=100)
plt.text(ef/total_flow*100-60, ev/60/60+35, "Flow: "+str(ef)+" veh/h\nTravel time: "+"{:.2f}".format(ev/60/60)+" h("+"{:.2f}".format(ev/60/60/total_flow)+" h/veh)")

plt.subplot(2,2,3)
plt.title("                                                System optimum & User equilibrium")
plt.xlabel("Flow [veh/hour]")
plt.ylabel("Av. Vehicle\nTravel Time [sec]")
flow = []
avtraveltime = []
for i in range(0, len(ttt_x)):
    tot_flow = ttt_x[i]
    flowA = user_opt_flows[i] 
    flowB = tot_flow-flowA
    timeA = tableRouteA[tableRouteA["RealFlow"]==flowA].iloc[0]["sm_avg"]
    timeB = tableRouteB[tableRouteB["RealFlow"]==flowB].iloc[0]["sm_avg"]
    avtime = (flowA*timeA + flowB*timeB) / tot_flow
    flow.append(tot_flow)
    avtraveltime.append(avtime)
avtraveltime = np.asarray(avtraveltime)
filtered_avtraveltime = filterFunc(avtraveltime, window_size=21, func=np.max)
filtered_avtraveltime2 = filterFunc(filtered_avtraveltime, window_size=21, func=np.mean)
filtered_avtraveltime2 = np.array([min(val, 258) for val in filtered_avtraveltime2])
plt.plot(flow, filtered_avtraveltime2, label="User", color="green")
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
avtraveltime = np.asarray(avtraveltime)
filtered_avtraveltime = filterFunc(avtraveltime, window_size=21, func=np.max)
filtered_avtraveltime2 = filterFunc(filtered_avtraveltime, window_size=21, func=np.mean)
plt.plot(flow, filtered_avtraveltime2, label="System", color="red")
plt.legend()

plt.subplot(2,2,4)
plt.title("")
plt.xlabel("Flow [veh/hour]")
plt.ylabel("Flow on\nRoute A [%]")
sys_optimum = np.asarray(user_opt_flows)/np.asarray(ttt_x)*100
filtered_sys = filterFunc(sys_optimum)
filtered_sys = filterFunc(filtered_sys, window_size=11, func=np.mean)
user_optim = np.asarray(ttt_y)/np.asarray(ttt_x)*100
filtered_usr = filterFunc(user_optim, window_size=11)
filtered_usr = filterFunc(filtered_usr, window_size=11, func=np.mean)
plt.plot(ttt_x, filtered_sys, label="User Optimum", color="green")
plt.plot(ttt_x, filtered_usr, label="System Optimum", color="red")
plt.ylim([50,110])


plt.tight_layout()
plt.show()