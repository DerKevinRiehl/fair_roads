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

def drawPopulationPDF(file, color, label):
    x = loadPopulation(file)
    plt.hist(x, density=True, bins=82, label="Data", color="white")
    mn, mx = plt.xlim()
    plt.xlim(mn, mx)
    kde_xs = np.linspace(mn, mx, 300)
    kde = st.gaussian_kde(x)
    plt.plot(kde_xs, kde.pdf(kde_xs), color=color, label=label)




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
plt.legend(loc="upper left")
plt.xlabel("Flow [veh/h]")
plt.ylabel("Vehicle Travel Time [sec]")

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
plt.show()