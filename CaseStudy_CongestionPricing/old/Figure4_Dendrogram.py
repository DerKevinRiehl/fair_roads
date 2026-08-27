# 3D Plots

# Imports
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm

# Paths
log_fixed_programme = "Manhattan3x3_Fairness/logs/log_fixed_programme_fairness.csv"
# table = pd.read_csv(log_fixed_programme, index_col=False, skiprows=1, sep=",")

# Methods
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

def calculateFairnessDf(file, eff_metric, fair_metric, minMax_eff=True, minMax_fai=False):
    # minMax_eff=True  # maximize throughput
    # minMax_fai=False # minimize gini
    # eff_metric = "Total_Throuput.1"
    # fair_metric = "TotFairGini.1"
    fairness_data = []
    for flow in [50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550]:
        matrix_eff, _, _ = load_table(file=file, flow=flow, metric=eff_metric, nanval=0)
        matrix_eff = smooth_filter_matrix(matrix_eff)
        matrix_fair, _, _ = load_table(file=file, flow=flow, metric=fair_metric, nanval=0)
        matrix_fair = smooth_filter_matrix(matrix_fair)
        for alpha in [0.005, 0.01, 0.02, 0.05, 0.1]:
            if minMax_eff:
                eff_solution_space = matrix_eff>np.max(matrix_eff)*(1-alpha)
            else:
                eff_solution_space = matrix_eff<np.min(matrix_eff)*(1+alpha)
            matrix_fair_masked = matrix_fair.copy()
            if not minMax_fai:
                matrix_fair_masked[np.logical_not(eff_solution_space)] = np.max(matrix_fair)*1000
                best_possible_fairness = np.min(matrix_fair)
                worst_possible_fairness = np.max(matrix_fair)
                best_fairness_in_eff_sol_space = np.min(matrix_fair_masked)
            else:
                matrix_fair_masked[np.logical_not(eff_solution_space)] = np.min(matrix_fair)/1000
                best_possible_fairness = np.max(matrix_fair)
                worst_possible_fairness = np.min(matrix_fair)
                best_fairness_in_eff_sol_space = np.max(matrix_fair_masked)
            fairness_data.append([flow, alpha, best_fairness_in_eff_sol_space, best_possible_fairness, worst_possible_fairness])
    fairness_data = pd.DataFrame(fairness_data, columns=["Flow", "Alpha", "best_eff", "best_poss", "worst_poss"])
    return fairness_data

#  'Flow',
#  'Parameter1',
#  'Parameter2',
#  'Errors',
#  'Total_Throuput',
#  'Total_AvQueueLength',
#  'NumCompletedVeh',
#  'NumVehIntersectionPassages',
#  'N_TTT',
#  'TTT',
#  'VehAvDelay',
#  'VehMdDelay',
#  'VehStDelay',
#  'EmissionCO2',
#  'EmissionNoise',
#  'TotFairGini',
#  'TotFairHerf',
#  'TotFairHoov',
#  'TotFairPalm',
#  'TotFairStd',
#  'TotFairThlT',
#  'TotFairThlL',
#  'TotFairMax',
#  'TotFairTop01',
#  'TotFairTop02',
#  'TotFairTop05',
#  'TotFairTop10',
#  'DpiFairGini',
#  'DpiFairHerf',
#  'DpiFairHoov',
#  'DpiFairPalm',
#  'DpiFairStd',
#  'DpiFairThlT',
#  'DpiFairThlL',
#  'DpiFairMax',
#  'DpiFairTop01',
#  'DpiFairTop02',
#  'DpiFairTop05',
#  'DpiFairTop10',


table = pd.read_csv("./MapSimulation/TravelTimes_routeA.csv", index_col=False, sep=";")
selected_features = ['avg', 'median', 'std', 'gini', 'herf', 'hoov', 'palm', 'thlt', 'thll', 'max', 'top01', 'top02', 'top05', 'top10',]

table = table[selected_features]
table = table.rename(columns={
                      "avg": "Average Vehicle Delay", 
                      "median" : "Median Vehicle Delay",
                      "gini": "Gini Coefficient", 
                      'herf': "Herfindahl Index",
                      'hoov': "Hoover Index", 
                      'palm': "Palma Index", 
                      'std': "Standard Deviation Delay", 
                      'thlt': "Theil T Index",
                      'thll': "Theil L Index", 
                      'max': "Maximum Vehicle Delay", 
                      'top01': "1% Percentile Delay", 
                      'top02': "2% Percentile Delay",
                      'top05': "5% Percentile Delay", 
                      'top10': "10% Percentile Delay"})

import seaborn as sns
plt.rc('font', family='sans-serif') 
plt.rc('font', serif='Arial') 
# plt.figure(figsize=(12/2,4), dpi=100)
correlations = table.corr()
# plt.title("(F) Fairness Measure Dendrogram", fontweight="bold")

# sns.set(rc={'figure.figsize':(12/2,4)})
# sns.suptitle(title="(F) Fairness Measure Dendrogram")

# sns.heatmap(round(correlations,2), cmap='RdBu', annot=False, 
#             annot_kws={"size": 7}, vmin=-1, vmax=1);
cg = sns.clustermap(round(correlations,2), 
                    cmap='coolwarm', 
                    figsize=(12/2,4),
                    annot=False, 
                    # annot_kws={"size": 7}, 
                    vmin=-1, 
                    vmax=1,
                    xticklabels=False,
                    yticklabels=1,
                    # cbar_kws={"orientation": "horizontal", "use_gridspec": "False", "location": "bottom"}
                    cbar_kws= dict(location="bottom", orientation="horizontal"),
                    cbar_pos=(0.2, 0.85, 0.6, 0.05)
                    
                    );
cg.fig.suptitle('(G) Fairness Measure Dendrogram', fontweight="bold") 
cg.ax_col_dendrogram.set_visible(False) #suppress row dendrogram
# cg.ax_cbar.set_title("Correlation")

# from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
# from scipy.spatial.distance import squareform
# dissimilarity = 1 - abs(correlations)
# Z = linkage(squareform(dissimilarity), 'complete')
# # dendrogram(Z, labels=table.columns, orientation='left', 
# #            leaf_rotation=0);
# dendrogram(Z, labels=table.columns);
# plt.xlabel("Dissimilarity (%)")

# plt.tight_layout()