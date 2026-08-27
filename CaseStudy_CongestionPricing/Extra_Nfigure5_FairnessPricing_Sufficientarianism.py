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




cost_population = []
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
    cost_population.append(pop_cost)
    
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








import matplotlib.pyplot as plt
import numpy as np
from scipy import stats



# Assuming cost_population is your list of lists
cost_population2 = np.asarray(cost_population)

# Calculate the probability distribution for each price point
prob_distribution = np.zeros_like(cost_population2, dtype=float)
for i, population in enumerate(cost_population2):
    kde = stats.gaussian_kde(population)
    prob_distribution[i] = kde(np.arange(len(population)))
    prob_distribution[i] /= prob_distribution[i].sum()  # Normalize

# Create the plot
fig, ax = plt.figure(figsize=(14, 8)), plt.gca()

plt.subplot(1,2,1)
# Create the heatmap
im = ax.imshow(prob_distribution.T, cmap='viridis', aspect='auto', 
               extent=[0, 8, np.max(cost_population2), np.min(cost_population2)])

# Customize the plot
plt.colorbar(im, label='Probability')
plt.xlabel('Price')
plt.ylabel('Cost')
plt.title('Probability Distribution of Costs for Different Prices')

# Set x-axis ticks and labels
plt.xticks(np.arange(0, 8.1, 1), [f'{i:.1f}' for i in np.arange(0, 8.1, 1)])

# Set y-axis ticks and labels (adjust as needed based on your cost range)
max_cost = np.max(cost_population2)
plt.yticks(np.linspace(0, max_cost, 9), [f'{i:.0f}' for i in np.linspace(0, max_cost, 9)])
plt.ylim(0,20)

plt.subplot(1,2,2)

def population_share_below_threshold(population, threshold):
    return np.mean(np.array(population) < threshold)

# Define the price range and thresholds
prices = np.linspace(0, 8, len(cost_population2))
thresholds = [4, 6, 8, 10, 12, 14, 16, 20, 25, 30]  # Adjust these thresholds as needed
# Plot lines for different thresholds
for threshold in thresholds:
    shares = [population_share_below_threshold(pop, threshold) for pop in cost_population2]
    plt.plot(prices, shares, label=f'T = {threshold}')

# Customize the plot
plt.xlabel('Price')
plt.ylabel('Share of Population')
plt.title('Share of Population with Cost Below Threshold T')
plt.legend(title='Threshold', loc='best')
plt.grid(True, linestyle='--', alpha=0.7)

# Set x-axis ticks and labels
plt.xticks(np.arange(0, 8.1, 1), [f'{i:.1f}' for i in np.arange(0, 8.1, 1)])

# Set y-axis to percentage
plt.ylim(0, 1)
plt.yticks(np.arange(0, 1.1, 0.1), [f'{i*100:.0f}%' for i in np.arange(0, 1.1, 0.1)])



plt.show()












