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
    for sample in range(0,n_reps):
        pop_salary  = np.random.choice(SALARY, total_flow_real, p=np.asarray(SALARY_probs)/sum(SALARY_probs))
        pop_urgency = np.random.choice(POP_URGENCIES_LEVEL, total_flow_real, p=POP_URGENCIES)
        pop_vot = np.asarray(pop_salary)*np.asarray(pop_urgency)
        pop_vot.sort()
        pop_vot = np.flip(pop_vot)
        synth_pops.append(pop_vot)
    return synth_pops

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
synth_pops = generateSyntheticPopulations(total_flow_real, n_reps=5)
x_prices = []
y_shares = []
y_delayC = []
y_totalC = []
for price_ctr in range(0, 80, 1): 
    price = price_ctr/10
    share, delay_cost, total_cost = getUserOptimum_Money(tableRouteA, tableRouteB, total_flow_real, price, synth_pops)
    x_prices.append(price)
    y_shares.append(share)
    y_delayC.append(delay_cost)
    y_totalC.append(total_cost)
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
y_delayC_f = smoothFilter(y_delayC, 19000)
y_finanC_f = y_shares_f*total_flow_real*x_prices
y_distaC_f = y_shares_f*total_flow_real*ROUTE_A_COST + (1-y_shares_f)*total_flow_real*ROUTE_B_COST
y_totalC_f = y_distaC_f + y_finanC_f + y_delayC_f


###############################################################################
# ################# FOR ALL FLOWS
###############################################################################

"""
tot_flows = []
opt_prices = []
opt_tot_costs = []
opt_del_costs = []
opt_shares = []
last_opt_price = 4.5
for tot_flow in range(1100, 500-1, -10):
    tidx = ttt_x.index(tot_flow)
    should_optimal_flowA = ttt_y[tidx]
    if tot_flow<=730:
        opt_price = 0
    else:
        flow_dist_optimal = []
        xf_prices = []
        y_costs = []
        for price_ctr in range(int(last_opt_price*10-10), int(last_opt_price*10+10)): # vary from minus to plus one euro (only 20 calculations)
            price_routeA = price_ctr/10 
            xf_prices.append(price_routeA)
            share, delay_cost, total_cost = getUserOptimum_Money(tableRouteA, tableRouteB, tot_flow, price_routeA, synth_pops)
            flowA = int(share*tot_flow)
            flowB = tot_flow - flowA
            y_costs.append(total_cost)
            flow_dist_optimal.append(abs(flowA-should_optimal_flowA))
        bestIdx = np.argmin(flow_dist_optimal)
        opt_price = np.max(xf_prices[bestIdx], 0)
    last_opt_price = opt_price
    opt_prices.append(opt_price)
    share, delay_cost, total_cost = getUserOptimum_Money(tableRouteA, tableRouteB, tot_flow, opt_price, synth_pops)
    opt_shares.append(share)
    opt_tot_costs.append(total_cost)
    opt_del_costs.append(delay_cost)
    tot_flows.append(tot_flow)
    print(tot_flow, opt_price)
"""
tot_flows  = [1100, 1090, 1080, 1070, 1060, 1050, 1040, 1030, 1020, 1010, 1000, 990, 980, 970, 960, 950, 940, 930, 920, 910, 900, 890, 880, 870, 860, 850, 840, 830, 820, 810, 800, 790, 780, 770, 760, 750, 740, 730, 720, 710, 700, 690, 680, 670, 660, 650, 640, 630, 620, 610, 600, 590, 580, 570, 560, 550, 540, 530, 520, 510, 500]
opt_prices = [4.5, 4.5, 4.3, 4.0, 3.8, 3.8, 3.7, 3.7, 3.7, 3.6, 3.6, 3.6, 3.5, 3.5, 3.5, 3.4, 3.4, 3.4, 3.3, 3.3, 3.3, 3.2, 2.9, 2.9, 2.8, 2.6, 2.6, 2.6, 2.4, 2.4, 2.1, 2.1, 2.1, 1.9, 1.9, 1.9, 0.9, 0.5, 0.1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
opt_shares = [0.62, 0.6912727272727273, 0.6912727272727273, 0.7123636363636364, 0.7352727272727273, 0.7352727272727273, 0.7352727272727273, 0.7352727272727273, 0.7352727272727273, 0.7352727272727273, 0.7352727272727273, 0.7352727272727273, 0.7352727272727273, 0.7352727272727273, 0.7352727272727273, 0.7503636363636363, 0.7503636363636363, 0.7656363636363637, 0.7794545454545455, 0.8101818181818181, 0.8101818181818181, 0.8227272727272726, 0.8227272727272726, 0.8227272727272726, 0.834, 0.8836363636363636, 0.8836363636363636, 0.8836363636363636, 0.8847272727272728, 0.8847272727272728, 0.9363636363636363, 0.9363636363636363, 0.9363636363636363, 0.9516363636363636, 0.9516363636363636, 0.9516363636363636, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
opt_del_costs = [10929.015273946627, 11127.85418412449, 11191.95405341371, 11036.217290327402, 11228.247161261703, 11183.823332828466, 11169.765001124433, 11140.053038702044, 11129.193218435605, 11047.972481506484, 11018.830666142536, 10969.113104047008, 10995.180512538134, 10981.822050114137, 10928.330731482287, 10978.729778872701, 10923.428592594068, 10977.741527238839, 10980.776862209375, 11026.735416143803, 10960.606394898696, 11001.728739671486, 10994.534721690621, 10968.913336064763, 10974.302785412781, 11092.90181974579, 11041.188053402488, 11002.822592612552, 10979.808684110705, 10981.427711882498, 11116.525481508452, 11013.960818107218, 10978.338468429964, 10988.382576274136, 10980.510322999418, 10956.972303385273, 11011.257386736253, 10978.610326273072, 10973.397007638727, 10943.51126743651, 10862.739550111562, 10837.815755987087, 10885.630407938781, 10883.368130160026, 10850.448319703433, 10842.044182448557, 10867.392515780713, 10860.346992904642, 10844.813757610504, 10825.979215126903, 10847.086943883998, 10868.55127394827, 10809.770097478828, 10785.620130158728, 10766.382548459394, 10747.787581139113, 10773.012528849853, 10751.503025589062, 10753.309515793113, 10841.946489654485, 10847.387966786619]

opt_shares_f = filterFunc(opt_shares, window_size=11, func=np.mean)
opt_prices_f = filterFunc(opt_prices, window_size=3, func=np.mean)
opt_prices_f[37:] = 0

opt_del_costs_f = smoothFilter(opt_del_costs, 19000)
opt_finanC_f = opt_shares_f*np.asarray(tot_flows)*np.asarray(opt_prices_f)
opt_distaC_f = opt_shares_f*np.asarray(tot_flows)*ROUTE_A_COST + (1-opt_shares_f)*np.asarray(tot_flows)*ROUTE_B_COST
opt_finanC_f = filterFunc(opt_finanC_f, window_size=11, func=np.mean)





plt.rc('font', family='sans-serif') 
plt.rc('font', serif='Arial') 
plt.figure(figsize=(12, 3.5), dpi=100)
plt.suptitle("(E) System-Optimal Road Pricing", fontweight="bold")

plt.subplot(1,4,1)
l1 = plt.gca().plot(x_prices, y_shares_f*100, label="User Equilibrium")
l2 = plt.gca().plot([0, 8], [optimal_flowA*100, optimal_flowA*100], "--", color="black", label="System Optimum")
plt.ylabel("Flow on Route A [%]")
plt.xlabel("Price for Route A [CHF]")
plt.title("Total Flow = 1100 veh/h")
price_index = np.argmin(np.abs(np.asarray(y_shares_f)-optimal_flowA))
optimal_price = x_prices[price_index]
optimal_flowA = y_shares_f[price_index]
plt.scatter([optimal_price], [optimal_flowA*100], color="red", label="Optimal Price", s=100)
plt.legend(loc="lower left")

plt.subplot(1,4,2)
plt.title("Total Flow = 1100 veh/h")
plt.ylabel("Average User Costs [CHF]")
plt.xlabel("Price for Route A [CHF]")
plt.stackplot(x_prices, [
        y_delayC_f/total_flow_real,
        y_distaC_f/total_flow_real,
        y_finanC_f/total_flow_real,
    ], colors = ["black", "gray", "blue"], labels=["Delay", "Distance", "Fees"])
plt.gca().legend(loc="lower left")

plt.subplot(1,4,3)
# l1 = plt.gca().plot(tot_flow, y_shares_f*100, label="User Equilibrium")
# l2 = plt.gca().plot([0, 8], [optimal_flowA*100, optimal_flowA*100], "--", color="black", label="System Optimum")
plt.plot(tot_flows, opt_prices_f)
plt.xlabel("Total Flow [veh/h]")
plt.ylabel("Price for Route A [CHF]")
plt.title("System Optimal Price")
# plt.legend(loc="lower left")

plt.subplot(1,4,4)
plt.title("System Optimal Costs")
plt.ylabel("Average User Costs [CHF]")
plt.xlabel("Total Flow [veh/h]")
plt.stackplot(tot_flows, [
        opt_del_costs_f/total_flow_real,
        opt_distaC_f/total_flow_real,
        opt_finanC_f/total_flow_real,
    ], colors = ["black", "gray", "blue"], labels=["Delay", "Distance", "Fees"])
plt.gca().legend(loc="lower left")

plt.tight_layout()
plt.tight_layout()

