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

def getUrgencyLevelProcess(p):
    urgency_dist = []
    urgency_level = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    urgency_dist = [p*np.power(1-p, k-1) for k in urgency_level]
    urgency_dist = urgency_dist/sum(urgency_dist)
    return urgency_dist, urgency_level



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









routeAFile = "./MapSimulation/TravelTimes_routeA.csv"
routeBFile = "./MapSimulation/TravelTimes_routeB.csv"

tableRouteA = readPopTable(routeAFile)
tableRouteB = readPopTable(routeBFile)
tableRouteA["Flow"] = tableRouteA["flow"]
tableRouteB["Flow"] = tableRouteB["flow"]
tableRouteA["RealFlow"] = tableRouteA["Flow"]*2
tableRouteB["RealFlow"] = tableRouteB["Flow"]*2


# #############################################################################
# ###################### FIGURE 0 - VOTs
# #############################################################################






plt.rc('font', family='sans-serif') 
plt.rc('font', serif='Arial') 
plt.figure(figsize=(6, 4), dpi=100)
plt.suptitle("(D) Market Model", fontweight="bold")


plt.subplot(2,1,1)
# Frequency distribution of the employees by wage level classes, 2018 
# https://www.bfs.admin.ch/asset/en/12488554
plt.gca().barh(SALARY, SALARY_probs, height=15.0, label=SALARY)
# plt.gca().set_xlabel('Share of Population [%]')
plt.gca().set_ylabel("Income [CHF/h]")
plt.gca().set_title('Income Distribution', x=0.5, y=0.8)

plt.subplot(2,1,2)
plt.gca().barh(POP_URGENCIES_LEVEL, POP_URGENCIES*100, height=0.5, label=POP_URGENCIES_LEVEL)
plt.gca().set_xlabel('Share of Population [%]')
plt.gca().set_ylabel("Urgency Level\n[N Times Salary]")
plt.gca().set_title('Urgency Distribution', x=0.5, y=0.8)

plt.tight_layout()
plt.show()