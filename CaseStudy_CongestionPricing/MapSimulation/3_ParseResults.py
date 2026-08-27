# Imports
import numpy as np
import pandas as pd
import os




# Methods
def loadPopulation(file):
    f = open(file, "r")
    content = f.read()
    f.close()    
    pop = content.split("\n")
    pop = [float(p) for p in pop if str(p)!=""]
    return pop

# #############################################################################
def fairness_atkinson(vals, n, av, sm, epsilon):
    if epsilon==1:
        if 0 in vals:
            return 1
        else:
            return 1-(1/av)*np.power(np.prod(vals), 1/n)
    elif epsilon<1:
        return 1-(1/av)*np.power(1/n*sum([np.power(val, 1-epsilon) for val in vals]), 1/(1-epsilon))
    else:
        return 1-(1/av)*min(vals)

def fairness_gini(vals, n, av, sm):
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

def fairness_herfindahl(vals, n, av, sm):
    HH = 0
    if n==0:
        return -1
    HH = sum([(val/sm)*(val/sm) for val in vals])
    return (HH-1/n)/(1-1/n)

def fairness_hoover(vals, n, av, sm):
    if n==0:
        return -1
    return 0.5*(sum([abs(val-av) for val in vals]))/sm

def fairness_palma(vals, n, av, sm):
    vals_sort = vals.copy()
    vals_sort.sort()
    lower = sum(vals[0:int(0.4*n)])
    upper = sum(vals[int(0.9*n):])
    return lower/upper

def fairness_std(vals, n, av, sm):
    return np.nanstd(vals)

def fairness_theil_t(vals, n, av, sm):
    return (1/n)*sum([val/av*np.log(val/av) for val in vals if val!=0])

def fairness_theil_l(vals, n, av, sm):
    return (1/n)*sum([np.log(val/av) for val in vals if val!=0])

# #############################################################################

    # # Fairness Statistics for total delay
    #     # dispersion of O
    # vals = population_delay_time
    # n = len(vals)
    # av = np.nanmean(vals)
    # sm = sum(vals)
    # fairnessGini = fairness_gini(vals, n, av, sm)
    # fairnessHerf = fairness_herfindahl(vals, n, av, sm)
    # fairnessHoov = fairness_hoover(vals, n, av, sm)
    # fairnessPalm = fairness_palma(vals, n, av, sm)
    # fairnessStdv = fairness_std(vals, n, av, sm)
    # fairnessThlT = fairness_theil_t(vals, n, av, sm)
    # fairnessThlL = fairness_theil_l(vals, n, av, sm)
    #     # Rawlsian
    # fairnessMax = max(vals)
    # vals_sort = vals.copy()
    # vals_sort.sort()
    # vals_sort.reverse()
    # fairnessTop01 = np.nanmean(vals[0:int(0.01*n)])
    # fairnessTop02 = np.nanmean(vals[0:int(0.02*n)])
    # fairnessTop05 = np.nanmean(vals[0:int(0.05*n)])
    # fairnessTop10 = np.nanmean(vals[0:int(0.10*n)])   
    
    
route = "routeA"
files = os.listdir("distributions/")
rel_files = []
for file in files:
    if route in file:
        rel_files.append("distributions/"+file)

f = open("TravelTimes_"+route+".csv", "w+")
f.write("flow\tavg\tmedian\tstd\tgini\therf\thoov\tpalm\tthlt\tthll\tmax\ttop01\ttop02\ttop05\ttop10\tpc20\tpc50\tpc80\n")
for file in rel_files:
    print(file)
    flow = file.split("_")[-1].replace(".txt", "")
    vals = loadPopulation(file)
    
    n = len(vals)
    av = np.nanmean(vals)
    sm = sum(vals)
    
    veh_av_delay_time = np.nanmean(vals)
    veh_md_delay_time = np.nanmedian(vals)
    veh_st_delay_time = np.nanstd(vals)
    
    fairnessGini = fairness_gini(vals, n, av, sm)
    fairnessHerf = fairness_herfindahl(vals, n, av, sm)
    fairnessHoov = fairness_hoover(vals, n, av, sm)
    fairnessPalm = fairness_palma(vals, n, av, sm)
    fairnessStdv = fairness_std(vals, n, av, sm)
    fairnessThlT = fairness_theil_t(vals, n, av, sm)
    fairnessThlL = fairness_theil_l(vals, n, av, sm)
        # Rawlsian
    fairnessMax = max(vals)
    vals_sort = vals.copy()
    vals_sort.sort()
    vals_sort.reverse()
    fairnessTop01 = np.percentile(vals, 99) # np.nanmean(vals[0:int(0.01*n)])
    fairnessTop02 = np.percentile(vals, 98) # np.nanmean(vals[0:int(0.02*n)])
    fairnessTop05 = np.percentile(vals, 95) # np.nanmean(vals[0:int(0.05*n)])
    fairnessTop10 = np.percentile(vals, 90) # np.nanmean(vals[0:int(0.10*n)])  
    
    vals_sort.reverse()
    fairnessPc40 = np.percentile(vals, 20) #np.nanmean(vals[0:int(0.40*n)])  
    fairnessPc50 = np.percentile(vals, 50) #np.nanmean(vals[0:int(0.50*n)])  
    fairnessPc60 = np.percentile(vals, 80) #np.nanmean(vals[0:int(0.60*n)])  
    
    # veh_av_delay_time, veh_md_delay_time, veh_st_delay_time,
    # fairnessGini, fairnessHerf, fairnessHoov, fairnessPalm, fairnessStdv, fairnessThlT, fairnessThlL,
    # fairnessMax, fairnessTop01, fairnessTop02, fairnessTop05, fairnessTop10,

    f.write(str(flow))
    f.write("\t")
    f.write(str(veh_av_delay_time))
    f.write("\t")
    f.write(str(veh_md_delay_time))
    f.write("\t")
    f.write(str(veh_st_delay_time))
    f.write("\t")
    f.write(str(fairnessGini))
    f.write("\t")
    f.write(str(fairnessHerf))
    f.write("\t")
    f.write(str(fairnessHoov))
    f.write("\t")
    f.write(str(fairnessPalm))
    f.write("\t")
    f.write(str(fairnessThlT))
    f.write("\t")
    f.write(str(fairnessThlL))
    f.write("\t")
    f.write(str(fairnessMax))
    f.write("\t")
    f.write(str(fairnessTop01))
    f.write("\t")
    f.write(str(fairnessTop02))
    f.write("\t")
    f.write(str(fairnessTop05))
    f.write("\t")
    f.write(str(fairnessTop10))
    f.write("\t")
    f.write(str(fairnessPc40))
    f.write("\t")
    f.write(str(fairnessPc50))
    f.write("\t")
    f.write(str(fairnessPc60))
    f.write("\n")

f.close()