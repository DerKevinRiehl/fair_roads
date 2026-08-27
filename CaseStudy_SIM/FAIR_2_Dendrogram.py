# #############################################################################
# ####################### IMPORTS #############################################
# #############################################################################
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns




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




# #############################################################################
# ####################### Available Fairness Measures From DataSet ############
# #############################################################################

log_fixed_programme = "Manhattan3x3_Fairness/logs/log_fixed_programme_fairness.csv"
table = pd.read_csv(log_fixed_programme, index_col=False, skiprows=1, sep=",")

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



# #############################################################################
# ####################### Figure (G): Fairness Measure Dendrogram #############
# #############################################################################
selected_features = ["Total_Throuput.1", "Total_AvQueueLength.1", "NumCompletedVeh.1", 
                     # "NumVehIntersectionPassages.1", 
                     "TTT.1", "VehAvDelay.1", "VehMdDelay.1",
                     "EmissionCO2.1", "EmissionNoise.1", "TotFairGini.1", 'TotFairHerf.1',
                     'TotFairHoov.1', 'TotFairPalm.1', 'TotFairStd.1', 'TotFairThlT.1',
                     'TotFairThlL.1', 'TotFairMax.1', 'TotFairTop01.1', 'TotFairTop02.1',
                     'TotFairTop05.1', 'TotFairTop10.1',]
table = table[selected_features]
table = table.rename(columns={"Total_Throuput.1": "Throughput", 
                      "Total_AvQueueLength.1":"Av. Queue Length", 
                      "NumCompletedVeh.1": "Completed Vehicles", 
                      "TTT.1": "Total Travel Time", 
                      "VehAvDelay.1": "Average Vehicle Delay", 
                      "VehMdDelay.1" : "Median Vehicle Delay",
                      "EmissionCO2.1": "Emission (CO2)", 
                      "EmissionNoise.1": "Emission (Noise)", 
                      "TotFairGini.1": "Gini Coefficient", 
                      'TotFairHerf.1': "Herfindahl Index",
                      'TotFairHoov.1': "Hoover Index", 
                      'TotFairPalm.1': "Palma Index", 
                      'TotFairStd.1': "Standard Deviation Delay", 
                      'TotFairThlT.1': "Theil T Index",
                      'TotFairThlL.1': "Theil L Index", 
                      'TotFairMax.1': "Maximum Vehicle Delay", 
                      'TotFairTop01.1': "1% Percentile Delay", 
                      'TotFairTop02.1': "2% Percentile Delay",
                      'TotFairTop05.1': "5% Percentile Delay", 
                      'TotFairTop10.1': "10% Percentile Delay"})

plt.rc('font', family='sans-serif') 
plt.rc('font', serif='Arial') 

correlations = table.corr()
cg = sns.clustermap(round(correlations,2), 
                    cmap='coolwarm', 
                    figsize=(12/2,4),
                    annot=False, 
                    vmin=-1, 
                    vmax=1,
                    xticklabels=False,
                    yticklabels=1,
                    cbar_kws= dict(location="bottom", orientation="horizontal", ticks=[-1, 0, 1]),
                    cbar_pos=(0.3, 0.88, 0.4, 0.02)                    
                    );
cg.fig.suptitle('(G) Metric Dendrogram', fontweight="bold") 
cg.ax_col_dendrogram.set_visible(False) 
