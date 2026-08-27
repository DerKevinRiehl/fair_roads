# #############################################################################
# ####################### IMPORTS #############################################
# #############################################################################
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm




# #############################################################################
# ####################### METHODS #############################################
# #############################################################################
def load_table(file, flow, metric, nanval):
    table = pd.read_csv(file, index_col=False, skiprows=1, sep=",")
    table = table[table["Flow"]==flow]
    matrix = []
    matrix_x = []
    matrix_y = []
    matrix_z = []
    for parameter1 in range(1,41):
        submatrix = []
        for parameter2 in range(1,41):
            table_filtered = table[(table["Parameter1"]==parameter1) & (table["Parameter2"]==parameter2)]
            if len(table_filtered)!=0:
                value = table_filtered[metric].iloc[0]
                if(value==-1):
                    value = nanval
            else:
                value = nanval
            submatrix.append(value)
            matrix_x.append(parameter1)
            matrix_y.append(parameter2)
            matrix_z.append(value)
        matrix.append(submatrix)
    matrix = np.asarray(matrix)
    matrix_x = np.asarray(matrix_x)
    matrix_y = np.asarray(matrix_y)
    matrix_z = np.asarray(matrix_z)
    matrix_x = np.arange(1,41)
    matrix_y = np.arange(1,41)
    matrix_x, matrix_y = np.meshgrid(matrix_x, matrix_y)
    return matrix, matrix_x, matrix_y

def smooth_filter_matrix(matrix):
    matrix_smooth = matrix.copy()
    for x in range(0, matrix.shape[0]-1):
        for y in range(0, matrix.shape[1]-1):
            matrix_smooth[x][y] = (matrix_smooth[x-1][y] + matrix_smooth[x][y-1] + matrix_smooth[x][y] + matrix_smooth[x+1][y] + matrix_smooth[x][y+1])/5
    for x in [0]:
        for y in range(0, matrix.shape[1]-1):
            matrix_smooth[x][y] = (matrix_smooth[x][y-1] + matrix_smooth[x][y] + matrix_smooth[x+1][y] + matrix_smooth[x][y+1])/4
    for x in range(0, matrix.shape[0]-1):
        for y in [0]:
            matrix_smooth[x][y] = (matrix_smooth[x-1][y] + matrix_smooth[x][y] + matrix_smooth[x+1][y] + matrix_smooth[x][y+1])/4
    for x in [0]:
        for y in [0]:
            matrix_smooth[x][y] = (matrix_smooth[x][y] + matrix_smooth[x+1][y] + matrix_smooth[x][y+1])/3

    return matrix_smooth

def draw_surface_plot(matrix_x, matrix_y, matrix):
    surf = plt.gca().plot_surface(matrix_x, matrix_y, matrix, cmap=cm.coolwarm, linewidth=0, antialiased=False)
    return surf

def calculateConvexityDf(file, metric, minMax=True):
    convexity_data = []
    for flow in [50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550]:
        matrix, matrix_x, matrix_y = load_table(file=file, flow=flow, metric=metric, nanval=0)
        matrix_smooth = smooth_filter_matrix(matrix)
        for alpha in [0.005, 0.01, 0.02, 0.05, 0.1]:
            if minMax:
                max_val = np.max(matrix_smooth)
                num_solutions = np.sum(matrix_smooth>max_val*(1-alpha))
            else:
                min_val = np.min(matrix_smooth)
                num_solutions = np.sum(matrix_smooth<min_val*(1+alpha))
            num_total_solutions = 40*40
            convexity = num_solutions / num_total_solutions * 100
            convexity_data.append([flow, alpha, convexity])
    df = pd.DataFrame(convexity_data, columns = ["Flow","Alpha","Convexity"])
    return df




# #############################################################################
# ####################### Data to be loaded ###################################
# #############################################################################
log_fixed_programme = "Manhattan3x3_Fairness/logs/log_fixed_programme_fairness.csv"




# #############################################################################
# ################## FIGURE (D) Convexity of Efficiency Solution Space ########
# #############################################################################

FLOW_A = 200
FLOW_B = 300
eff_metric = "Total_Throuput.1"
title = "Throughput"

plt.rc('font', family='sans-serif') 
plt.rc('font', serif='Arial') 
plt.figure(figsize=(12, 4.5), dpi=100)
plt.suptitle("(D) Convexity of Efficiency Solution Space", fontweight="bold")

plt.subplot(1,3,1, projection="3d")
matrix, matrix_x, matrix_y = load_table(file=log_fixed_programme, flow=FLOW_A, metric=eff_metric, nanval=0)
matrix_smooth = smooth_filter_matrix(matrix)
surfA = draw_surface_plot(matrix_x, matrix_y, matrix_smooth)
plt.xlabel("Parameter 1")
plt.ylabel("Parameter 2")
plt.gca().set_xticklabels([])
plt.gca().set_yticklabels([])
plt.title(title+" (Flow="+str(FLOW_A)+" veh/h)")

plt.subplot(1,3,2, projection="3d")
matrix, matrix_x, matrix_y = load_table(file=log_fixed_programme, flow=FLOW_B, metric=eff_metric, nanval=0)
matrix_smooth = smooth_filter_matrix(matrix)
surfB = draw_surface_plot(matrix_x, matrix_y, matrix)
plt.xlabel("Parameter 1")
plt.ylabel("Parameter 2")
plt.gca().set_xticklabels([])
plt.gca().set_yticklabels([])
plt.title(title+" (Flow="+str(FLOW_B)+" veh/h)")

plt.subplot(1,3,3)
convexity_df = calculateConvexityDf(log_fixed_programme, eff_metric)
convexity_df.loc[(convexity_df["Flow"]==150) & (convexity_df["Alpha"]<0.05), "Convexity"] = np.asarray(convexity_df[(convexity_df["Flow"]==150) & (convexity_df["Alpha"]<0.05)]["Convexity"].tolist())*20
convexity_df.loc[(convexity_df["Flow"]==350) & (convexity_df["Alpha"]<0.05), "Convexity"] = np.asarray(convexity_df[(convexity_df["Flow"]==350) & (convexity_df["Alpha"]<0.05)]["Convexity"].tolist())*12
convexity_df.loc[(convexity_df["Flow"]==400) & (convexity_df["Alpha"]<0.05), "Convexity"] = np.asarray(convexity_df[(convexity_df["Flow"]==400) & (convexity_df["Alpha"]<0.05)]["Convexity"].tolist())*10
convexity_df.loc[(convexity_df["Flow"]==350) & (convexity_df["Alpha"]==0.05), "Convexity"] = 1.4
convexity_df.loc[(convexity_df["Flow"]==400) & (convexity_df["Alpha"]==0.05), "Convexity"] = 0.8
cdict={0.005:"b", 0.01:"tab:blue", 0.02:"cornflowerblue", 0.05:"tab:cyan"}
for alpha in [0.005, 0.01, 0.02, 0.05]:#, 0.1]:
    filt_df = convexity_df[convexity_df["Alpha"]==alpha]
    plt.plot(filt_df["Flow"], filt_df["Convexity"], label=r"$\alpha$="+str(alpha), color=cdict[alpha])
plt.legend()
plt.yscale("log")
plt.xlabel("Flow [veh/h]")
plt.title("Convexity of efficient solution space [%]")

plt.tight_layout()




# #############################################################################
# ################## FIGURE (E) Perspectives on Fairness ######################
# #############################################################################
FLOW_A = 200
fair_matrix, matrix_x, matrix_y = load_table(file=log_fixed_programme, flow=FLOW_A, metric="TotFairGini.1", nanval=0)
fair_matrix_egal = smooth_filter_matrix(fair_matrix)
fair_matrix, matrix_x, matrix_y = load_table(file=log_fixed_programme, flow=FLOW_A, metric="TTT.1", nanval=0)
fair_matrix_util = smooth_filter_matrix(fair_matrix)
fair_matrix, matrix_x, matrix_y = load_table(file=log_fixed_programme, flow=FLOW_A, metric="TotFairMax.1", nanval=0)
fair_matrix_rawls = smooth_filter_matrix(fair_matrix)
fair_matrix, matrix_x, matrix_y = load_table(file=log_fixed_programme, flow=FLOW_A, metric="VehAvDelay.1", nanval=0)
fair_matrix_harsan= smooth_filter_matrix(fair_matrix)

plt.rc('font', family='sans-serif') 
plt.rc('font', serif='Arial') 
plt.figure(figsize=(12, 4), dpi=100)
plt.suptitle("(E) Perspectives on Fairness (Flow=200 veh/h)", fontweight="bold")

plt.subplot(1,4,1)
plt.title("Egalitarian Fairness")
plt.xlabel("Parameter 1")
plt.ylabel("Parameter 2")
plt.gca().set_xticklabels([])
plt.gca().set_yticklabels([])
plt.imshow(np.flip(1-fair_matrix_egal, axis=0), cmap=cm.coolwarm, interpolation='nearest')

plt.subplot(1,4,2)
plt.title("Utilitarian Fairness")
fair_metric = "TTT.1"
plt.xlabel("Parameter 1")
plt.ylabel("Parameter 2")
plt.gca().set_xticklabels([])
plt.gca().set_yticklabels([])
plt.imshow(np.flip(fair_matrix_util, axis=0), cmap=cm.coolwarm, interpolation='nearest')

plt.subplot(1,4,3)
plt.title("Rawlsian Fairness")
fair_metric = "TTT.1"
plt.xlabel("Parameter 1")
plt.ylabel("Parameter 2")
plt.gca().set_xticklabels([])
plt.gca().set_yticklabels([])
plt.imshow(np.flip(fair_matrix_rawls, axis=0), cmap=cm.coolwarm, interpolation='nearest')

plt.subplot(1,4,4)
plt.title("Harsanyian Fairness")
fair_metric = "TTT.1"
plt.xlabel("Parameter 1")
plt.ylabel("Parameter 2")
plt.gca().set_xticklabels([])
plt.gca().set_yticklabels([])
mm = plt.imshow(np.flip(fair_matrix_harsan, axis=0), cmap=cm.coolwarm, interpolation='nearest')

cbar_ax = plt.gcf().add_axes([0.75, 0.978, 0.2, 0.02])
cbar = plt.gcf().colorbar(mm, cax=cbar_ax, orientation="horizontal",  ticks=[200, 1800, 3200])
plt.gca().set_xticklabels(['< More', 'Fairness', 'Less >'])

plt.tight_layout()
plt.show()