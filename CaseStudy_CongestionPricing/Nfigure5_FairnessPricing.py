# #############################################################################
# ####################### IMPORTS #############################################
# #############################################################################
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt




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

def getCost(travel_time, route, VOT):
    if route=="routeA":
        route_cost = ROUTE_A_COST
    else:
        route_cost = ROUTE_B_COST
    time_cost = VOT*travel_time
    total_cost = route_cost + time_cost
    return total_cost

def generateSyntheticPopulations(total_flow_real, n_reps=5):
    synth_pops = []
    synth_pops_u = []
    for sample in range(0,n_reps):
        pop_salary  = np.random.choice(SALARY, total_flow_real, p=np.asarray(SALARY_probs)/sum(SALARY_probs))
        pop_urgency = np.random.choice(POP_URGENCIES_LEVEL, total_flow_real, p=POP_URGENCIES)
        pop_vot = np.asarray(pop_salary)*np.asarray(pop_urgency)
        sort_indices = np.argsort(pop_vot)[::-1] 
        pop_vot = pop_vot[sort_indices]
        pop_urgency = pop_urgency[sort_indices]
        synth_pops.append(pop_vot)
        synth_pops_u.append(pop_urgency)
    return synth_pops, synth_pops_u

def getUserOptimum_Money(tableRouteA, tableRouteB, total_flow_real, price_routeA, synth_pops):   
    # determine share
    shares = []
    for pop_vot in synth_pops:      
        flows_tried = [flowA for flowA in range(0, total_flow_real+1, 2)]
        fit = []
        fit_shares = []
        for flowA in flows_tried:
            flowB = total_flow_real-flowA
            exp_timeA = tableRouteA[tableRouteA["RealFlow"]==flowA].iloc[0]["sm_avg"]/60/60 # h
            exp_timeB = tableRouteB[tableRouteB["RealFlow"]==flowB].iloc[0]["sm_avg"]/60/60 # h
            pop_cost_a = price_routeA + ROUTE_A_COST  + pop_vot*exp_timeA
            pop_cost_b = ROUTE_B_COST                 + pop_vot*exp_timeB
            pop_benefit = pop_cost_b-pop_cost_a
            share_going_a = sum(pop_benefit>0)/len(pop_benefit)
            assumed_share_going_a = flowA/total_flow_real
            if len(fit)==0 or abs(assumed_share_going_a-share_going_a)<fit[-1]:
                fit.append(abs(assumed_share_going_a-share_going_a))
                fit_shares.append(share_going_a)
            else:
                break
        fit_share = fit_shares[np.argmin(fit)]
        shares.append(fit_share)
    share = np.mean(shares)
    # determine cost
    flowA = int(total_flow_real*share)
    if flowA%2!=0:
        flowA-=1
    flowB = total_flow_real-int(flowA)
    exp_timeA = tableRouteA[tableRouteA["RealFlow"]==flowA].iloc[0]["sm_avg"]/60/60 # h
    exp_timeB = tableRouteB[tableRouteB["RealFlow"]==flowB].iloc[0]["sm_avg"]/60/60 # h
    delay_cost = np.sum(pop_vot[0:flowA]*exp_timeA) + np.sum(pop_vot[flowA+1:]*exp_timeB)
    pop_cost_a = price_routeA + ROUTE_A_COST  + pop_vot*exp_timeA
    pop_cost_b = ROUTE_B_COST                 + pop_vot*exp_timeB
    pop_cost = np.concatenate((np.asarray(pop_cost_a[:flowA]), np.asarray(pop_cost_b[flowA:])))
    total_cost = np.sum(pop_cost)        
    # return
    return share, delay_cost, total_cost

def getUrgencyLevelProcess(p):
    urgency_dist = []
    urgency_level = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    urgency_dist = [p*np.power(1-p, k-1) for k in urgency_level]
    urgency_dist = urgency_dist/sum(urgency_dist)
    return urgency_dist, urgency_level

def filterFunc(nparray, window_size=5, func=np.max):
    padded = np.pad(nparray, (window_size//2, window_size//2), mode='edge')
    windowed = np.lib.stride_tricks.sliding_window_view(padded, window_size)
    filtered_arr = func(windowed, axis=1)
    return filtered_arr




# #############################################################################
# ###################### MARKET MODEL ASSSUMPTIONS ############################
# #############################################################################
# Frequency distribution of the employees by wage level classes, 2018  in CHF
# https://www.bfs.admin.ch/asset/en/12488554
SALARY       = [11.76470588, 35.29411765, 58.82352941, 82.35294118, 105.8823529, 129.4117647, 152.9411765, 176.4705882, 200, 223.5294118, 247.0588235, 270.5882353, 294.1176471, 317.6470588, 341.1764706, 364.7058824, 388.2352941, 411.7647059, 435.2941176, 458.8235294, 470.5882353,]
SALARY_probs = [7, 7.15, 8.45, 11.5, 17.25, 15.75, 10.75, 6.75, 4.75, 3, 2.15, 1.175, 0.975, 0.360714286, 0.360714286, 0.360714286, 0.360714286, 0.360714286, 0.360714286, 0.360714286, 0.825,]
# https://www.tcs.ch/de/testberichte-ratgeber/ratgeber/kontrollen-unterhalt/kilometerkosten.php
MILLEAGE_COST = 0.76 # CHF / km
# OWN ASSUMPTIONS
URGENCY_DIST_P = 0.7
ROUTE_A_DIST = 2.50 # km
ROUTE_B_DIST = 4.67 # km
ROUTE_A_COST = ROUTE_A_DIST*MILLEAGE_COST
ROUTE_B_COST = ROUTE_B_DIST*MILLEAGE_COST
POP_URGENCIES, POP_URGENCIES_LEVEL = getUrgencyLevelProcess(URGENCY_DIST_P)




# #############################################################################
# ###################### Load Data
# #############################################################################

routeAFile = "./MapSimulation/TravelTimes_routeA.csv"
routeBFile = "./MapSimulation/TravelTimes_routeB.csv"

tableRouteA = readPopTable(routeAFile)
tableRouteB = readPopTable(routeBFile)
tableRouteA["Flow"] = tableRouteA["flow"]
tableRouteB["Flow"] = tableRouteB["flow"]
tableRouteA["RealFlow"] = tableRouteA["Flow"]*2
tableRouteB["RealFlow"] = tableRouteB["Flow"]*2

ttt_x = []
ttt_y = []
for total_flow in tableRouteA["RealFlow"].tolist():
    vals_TTT = calculateTTT(tableRouteA, tableRouteB, tot_flow = total_flow)
    ef, ev = getSystemEquilibrium(tableRouteA["RealFlow"].tolist(), vals_TTT)
    ttt_x.append(total_flow)
    ttt_y.append(ef)
    


# #############################################################################
# ###################### FIGURE ROAD PRICING MECHANISM FOR FLOW = 1100 ########
# #############################################################################

###############################################################################
# ################# FOR TOTAL FLOW 1100
###############################################################################
total_flow_real = 1100
optimal_flowA = 0.6618
synth_pops, synth_pops_u = generateSyntheticPopulations(total_flow_real, n_reps=5)
x_prices = []
y_shares = []
for price_ctr in range(0, 80, 1): 
    price = price_ctr/10
    share, delay_cost, total_cost = getUserOptimum_Money(tableRouteA, tableRouteB, total_flow_real, price, synth_pops)
    x_prices.append(price)
    y_shares.append(share)
    print(price, share, delay_cost, total_cost)
def smoothFilter(y_vals, x):
    y_shares_f = filterFunc(y_vals, window_size=11, func=np.mean)
    y_shares_f = filterFunc(y_shares_f, window_size=11, func=np.median)
    y_shares_f = filterFunc(y_shares_f, window_size=3, func=np.mean)
    thr = y_shares_f[0]
    y_shares_f = [min(val, thr) for val in y_shares_f]
    y_shares_f = filterFunc(y_shares_f, window_size=5, func=np.mean)
    return y_shares_f
y_shares_f = smoothFilter(y_shares, 0.84)





y_fairness_eg = []
y_fairness_ut = []
y_fairness_ra = []
y_fairness_hs = []
y_fairness_ar = []
y_fairness_ce = []

y_deccost = []
y_delcost = []

y1 = []
y2 = []
y3 = []
y4 = []
y5 = []
y6 = []
y7 = []
y8 = []
y9 = []
y10 = []
for itx in range(0, len(y_shares_f)):
    flowA = int(total_flow_real*y_shares_f[itx])
    if flowA%2!=0:
        flowA-=1
    flowB = total_flow_real-flowA
    pop_vot = synth_pops[0]
    pop_urgency = synth_pops_u[0]
    pop_income = pop_vot/pop_urgency
    
    exp_timeA = tableRouteA[tableRouteA["RealFlow"]==flowA].iloc[0]["sm_avg"]/60/60 # h
    exp_timeB = tableRouteB[tableRouteB["RealFlow"]==flowB].iloc[0]["sm_avg"]/60/60 # h
    price_routeA = x_prices[itx]
    
    pop_deccost_a = (price_routeA + ROUTE_A_COST) * np.ones(len(pop_vot))
    pop_deccost_b = (               ROUTE_B_COST) * np.ones(len(pop_vot))
    pop_delcost_a = pop_vot*exp_timeA
    pop_delcost_b = pop_vot*exp_timeB

    pop_cost_a = pop_deccost_a + pop_delcost_a
    pop_cost_b = pop_deccost_b + pop_delcost_b
    pop_benefit = pop_cost_b-pop_cost_a
    share_going_a = sum(pop_benefit>0)/len(pop_benefit)
    
    pop_cost = np.concatenate((pop_cost_a[0:flowA], pop_cost_b[flowA:]))

    pop_deccost = np.concatenate((pop_deccost_a[0:flowA], pop_deccost_b[flowA:]))
    pop_delcost = np.concatenate((pop_delcost_a[0:flowA], pop_delcost_b[flowA:]))
    
    ce_measure = pop_delcost / pop_vot
    y_fairness_ce.append(fairness_gini(ce_measure))
    
    y_deccost.append(pop_deccost)
    y_delcost.append(pop_delcost)
    
    y_fairness_eg.append(fairness_gini(pop_cost))
    y_fairness_ut.append(np.sum(pop_cost))
    y_fairness_ra.append(np.max(pop_cost))
    y_fairness_hs.append(np.mean(pop_cost))
    
    pop_a_cost = pop_cost_a[0:flowA]
    pop_b_cost = pop_cost_b[flowA:]
    pop_a_dvot = pop_vot[0:flowA]
    pop_b_dvot = pop_vot[flowA:]
    pop_a_durg = pop_urgency[0:flowA]
    pop_b_durg = pop_urgency[flowA:]
    
    y1.append(np.mean(pop_a_cost))
    y2.append(np.mean(pop_b_cost))
    y3.append(np.mean(pop_a_dvot))
    y4.append(np.mean(pop_b_dvot))
    y5.append(np.mean(pop_a_durg))
    y6.append(np.mean(pop_b_durg))
    y7.append(np.mean(pop_deccost_a))
    y8.append(np.mean(pop_deccost_b))
    y9.append(np.mean(pop_delcost_a))
    y10.append(np.mean(pop_delcost_b))
    
    print(itx, len(y_shares_f))

y5_f = filterFunc(y5, window_size=11, func=np.median)
y6_f = filterFunc(y6, window_size=11, func=np.median)

y1 = np.asarray(y1)
y2 = np.asarray(y2)
y3 = np.asarray(y3)
y4 = np.asarray(y4)

y7 = np.asarray(y7)
y8 = np.asarray(y8)
y9 = np.asarray(y9)
y10 = np.asarray(y10)

y7_f = filterFunc(y7, window_size=11, func=np.median)
y8_f = filterFunc(y8, window_size=11, func=np.median)
y9_f = filterFunc(y9, window_size=11, func=np.median)
y10_f = filterFunc(y10, window_size=11, func=np.median)

y_fairness_ar = []
for it in range(0,len(y_delcost)):
    y_fairness_ar.append(fairness_gini(y_deccost[it]/y_delcost[it]))









plt.rc('font', family='sans-serif') 
plt.rc('font', serif='Arial') 
plt.figure(figsize=(12, 4), dpi=100)

plt.subplot(2,3,1)
plt.title("Average VOT")
plt.plot(x_prices, y3, label="Route A")
plt.plot(x_prices, y4, label="Route B")
plt.legend()

plt.subplot(2,3,4)
plt.title("Average Urgency")
plt.plot(x_prices, y5_f, label="Route A")
plt.plot(x_prices, y6_f, label="Route B")
plt.legend()

plt.subplot(2,3,2)
plt.title("Average Cost")
plt.plot(x_prices, y1, label="Route A")
plt.plot(x_prices, y2, label="Route B")
plt.legend()

plt.subplot(2,3,3)
plt.title("Average Decision Cost")
plt.plot(x_prices, y7, label="Route A")
plt.plot(x_prices, y8, label="Route B")
plt.legend()

plt.subplot(2,3,6)
plt.title("Average Delay Cost")
plt.plot(x_prices, y9, label="Route A")
plt.plot(x_prices, y10, label="Route B")
plt.legend()









winsize_filter = 3
optimal_price = 4.5

def drawRedMinimumDot(fairness_vals, mr=False, label="Fairness-Optimal"):
    vals = filterFunc(fairness_vals, window_size=winsize_filter, func=np.mean)
    midx = np.argmin(vals)
    if mr:
        midx = len(vals)-1
    plt.scatter(x_prices[midx], vals[midx], color="red", s=100, label=label)

plt.rc('font', family='sans-serif') 
plt.rc('font', serif='Arial') 
plt.figure(figsize=(12, 4.5), dpi=100)
plt.suptitle("(F) Fairness-Optimal Road Pricing", fontweight="bold")

plt.subplot(2,5,1)
plt.title("Egalitarian Fairness")
plt.plot(x_prices, filterFunc(y_fairness_eg, window_size=winsize_filter, func=np.mean))
plt.plot([optimal_price, optimal_price], [min(y_fairness_eg), max(y_fairness_eg)], "--", label="System-Optimal", color="black")
drawRedMinimumDot(y_fairness_eg)
plt.legend()

plt.subplot(2,5,2)
plt.title("Rawlsian Fairness")
plt.plot(x_prices, filterFunc(y_fairness_ra, window_size=winsize_filter, func=np.mean))
plt.plot([optimal_price, optimal_price], [min(y_fairness_ra), max(y_fairness_ra)], "--", color="black")
drawRedMinimumDot(y_fairness_ra, mr=True)

plt.subplot(2,5,3)
plt.title("Aristotelian Fairness")
plt.plot(x_prices, filterFunc(y_fairness_ar, window_size=winsize_filter, func=np.mean))
plt.plot([optimal_price, optimal_price], [min(y_fairness_ar), max(y_fairness_ar)], "--", color="black")
drawRedMinimumDot(y_fairness_ar)

plt.subplot(2,5,4)
plt.title("Average VOT")
plt.plot(x_prices, y3, label="Route A")
plt.plot(x_prices, y4, label="Route B")
# plt.legend()

plt.subplot(2,5,6)
plt.title("Utilitarian Fairness")
plt.plot(x_prices, filterFunc(y_fairness_ut, window_size=winsize_filter, func=np.mean))
plt.plot([optimal_price, optimal_price], [min(y_fairness_ut), max(y_fairness_ut)], "--", color="black")
drawRedMinimumDot(y_fairness_ut)

plt.subplot(2,5,7)
plt.title("Harsanyian Fairness")
plt.plot(x_prices, filterFunc(y_fairness_hs, window_size=winsize_filter, func=np.mean))
plt.plot([optimal_price, optimal_price], [min(y_fairness_hs), max(y_fairness_hs)], "--", color="black")
drawRedMinimumDot(y_fairness_hs)

plt.subplot(2,5,8)
plt.title("Luck-Egalitarian Fairness")
plt.plot(x_prices, filterFunc(y_fairness_ce, window_size=winsize_filter, func=np.mean))
plt.plot([optimal_price, optimal_price], [min(y_fairness_ce), max(y_fairness_ce)], "--", color="black")
drawRedMinimumDot(y_fairness_ce)

plt.subplot(2,5,9)
plt.title("Average Urgency Level")
plt.plot(x_prices, y5_f, label="Route A")
plt.plot(x_prices, y6_f, label="Route B")
plt.legend()

plt.subplot(2,5,5)
plt.title("Costs Route A")
plt.fill_between(x_prices, y9+y7, color="blue", label="active")
plt.fill_between(x_prices, y9, color="gray", label="passive")
plt.ylim(0, 22)
plt.legend(loc="lower left")

plt.subplot(2,5,10)
plt.title("Costs Route B")
plt.fill_between(x_prices, y10+y8, color="blue", label="active")
plt.fill_between(x_prices, y10, color="gray", label="passive")
plt.ylim(0, 22)

plt.tight_layout()
