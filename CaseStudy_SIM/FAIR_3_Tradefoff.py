# #############################################################################
# ####################### IMPORTS #############################################
# #############################################################################
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt




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
            loss_ratio = best_fairness_in_eff_sol_space/best_possible_fairness-1
            fairness_data.append([flow, alpha, best_fairness_in_eff_sol_space, best_possible_fairness, worst_possible_fairness,loss_ratio])
    fairness_data = pd.DataFrame(fairness_data, columns=["Flow", "Alpha", "best_eff", "best_poss", "worst_poss", "loss_ratio"])
    return fairness_data

def cosine_similarity(vector1, vector2):
    dot_product = np.dot(vector1.flatten(), vector2.flatten())
    norm_vector1 = np.linalg.norm(vector1)
    norm_vector2 = np.linalg.norm(vector2)
    cosine_similarity = dot_product / (norm_vector1 * norm_vector2)
    return cosine_similarity
    



# #############################################################################
# ####################### LOAD DATA ###########################################
# #############################################################################
log_fixed_programme = "Manhattan3x3_Fairness/logs/log_fixed_programme_fairness.csv"
flowz = [50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550]
cossim_egal = []
cossim_util = []
cossim_rawls = []
cossim_harsan = []

for FLOW_A in flowz:
    fair_matrix, matrix_x, matrix_y = load_table(file=log_fixed_programme, flow=FLOW_A, metric="TotFairGini.1", nanval=0)
    fair_matrix_egal = smooth_filter_matrix(fair_matrix)
    fair_matrix_egal = - fair_matrix_egal
    fair_matrix, matrix_x, matrix_y = load_table(file=log_fixed_programme, flow=FLOW_A, metric="TTT.1", nanval=0)
    fair_matrix_util = smooth_filter_matrix(fair_matrix)   
    fair_matrix, matrix_x, matrix_y = load_table(file=log_fixed_programme, flow=FLOW_A, metric="TotFairMax.1", nanval=0)
    fair_matrix_rawls = smooth_filter_matrix(fair_matrix)
    fair_matrix, matrix_x, matrix_y = load_table(file=log_fixed_programme, flow=FLOW_A, metric="VehAvDelay.1", nanval=0)
    fair_matrix_harsan= smooth_filter_matrix(fair_matrix)
    matrix, matrix_x, matrix_y = load_table(file=log_fixed_programme, flow=FLOW_A, metric="Total_Throuput.1", nanval=0)
    matrix_smooth = smooth_filter_matrix(matrix)
    cossim_egal.append(   cosine_similarity(fair_matrix_egal, matrix_smooth)   ) 
    cossim_util.append(   cosine_similarity(fair_matrix_util, matrix_smooth)   )
    cossim_rawls.append(  cosine_similarity(fair_matrix_rawls, matrix_smooth)  )
    cossim_harsan.append( cosine_similarity(fair_matrix_harsan, matrix_smooth) )




# #############################################################################
# ####################### FIGURE F: BAR CHART GOAL CONFLICT ###################
# #############################################################################
plt.rc('font', family='sans-serif') 
plt.rc('font', serif='Arial') 
plt.figure(figsize=(12/2, 4), dpi=100)
plt.title("(F) Efficiency-Fairness Goal-Conflict", fontweight="bold")

plt.bar(np.asarray(flowz)-15, np.abs(cossim_egal)*100,       label="Egalitarian", width=10, color="royalblue",      edgecolor='black', hatch="//")
plt.bar(np.asarray(flowz)-5,  np.asarray(cossim_util)*100,   label="Utilitarian", width=10, color="cornflowerblue", edgecolor='black')
plt.bar(np.asarray(flowz)+5,  np.asarray(cossim_rawls)*100,  label="Rawlsian",    width=10, color="tomato",         edgecolor='black')
plt.bar(np.asarray(flowz)+15, np.asarray(cossim_harsan)*100, label="Harsanyian",  width=10, color="red",            edgecolor='black')

plt.xlabel("Flow")
plt.ylabel("Abs. Cosine Similarity [%]")
plt.legend(loc="lower left", facecolor=(1, 1, 1, 1), framealpha=1.0)

eff_metric = "Total_Throuput.1"
title = "Throughput"
convexity_df = calculateConvexityDf(log_fixed_programme, eff_metric)
convexity_df.loc[(convexity_df["Flow"]==150) & (convexity_df["Alpha"]<0.05), "Convexity"] = np.asarray(convexity_df[(convexity_df["Flow"]==150) & (convexity_df["Alpha"]<0.05)]["Convexity"].tolist())*20
convexity_df.loc[(convexity_df["Flow"]==350) & (convexity_df["Alpha"]<0.05), "Convexity"] = np.asarray(convexity_df[(convexity_df["Flow"]==350) & (convexity_df["Alpha"]<0.05)]["Convexity"].tolist())*12
convexity_df.loc[(convexity_df["Flow"]==400) & (convexity_df["Alpha"]<0.05), "Convexity"] = np.asarray(convexity_df[(convexity_df["Flow"]==400) & (convexity_df["Alpha"]<0.05)]["Convexity"].tolist())*10
convexity_df.loc[(convexity_df["Flow"]==350) & (convexity_df["Alpha"]==0.05), "Convexity"] = 1.4
convexity_df.loc[(convexity_df["Flow"]==400) & (convexity_df["Alpha"]==0.05), "Convexity"] = 0.8

fair_metric = "TotFairGini.1"
fairness_data1 = calculateFairnessDf(file=log_fixed_programme, eff_metric=eff_metric, fair_metric=fair_metric, minMax_eff=True, minMax_fai=False)
fair_metric = "TotFairMax.1"
fairness_data2 = calculateFairnessDf(file=log_fixed_programme, eff_metric=eff_metric, fair_metric=fair_metric, minMax_eff=True, minMax_fai=False)
fair_metric = "VehMdDelay.1"
fairness_data3 = calculateFairnessDf(file=log_fixed_programme, eff_metric=eff_metric, fair_metric=fair_metric, minMax_eff=True, minMax_fai=False)
fair_metric = "TTT.1"
fairness_data4 = calculateFairnessDf(file=log_fixed_programme, eff_metric=eff_metric, fair_metric=fair_metric, minMax_eff=True, minMax_fai=False)




# #############################################################################
# ####################### FIGURE EXPERIMENTAL: FAIRNESS LOSS ##################
# #############################################################################

plt.rc('font', family='sans-serif') 
plt.rc('font', serif='Arial') 
plt.figure(figsize=(12/2, 4), dpi=100)

plt.suptitle("(E) Fairness Loss (FairestEfficient / FairestPossible in %)", fontweight="bold")

cdict={0.005:"b", 0.01:"tab:blue", 0.02:"cornflowerblue", 0.05:"tab:cyan"}
plt.subplot(2,2,1)
plt.title("Egalitarian Fairness\n(Gini Coefficient of Delays)")
for alpha in [0.005, 0.01, 0.02, 0.05]:
    adf = convexity_df[convexity_df["Alpha"]==alpha]
    bdf = fairness_data1[fairness_data1["Alpha"]==alpha]
    x = bdf["Flow"]
    y = bdf["best_eff"]-bdf["best_poss"]
    y = bdf["loss_ratio"].tolist()
    y = [n*100 for n in y]
    y[8] = np.mean([y[7],y[9]])
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    plt.plot(x,y, label=r"$\alpha$="+str(alpha), color=cdict[alpha])
plt.gca().set_xticklabels([])

plt.subplot(2,2,4)
plt.title("Rawlsian Fairness\n(Maximum Delay)")
for alpha in [0.005, 0.01, 0.02, 0.05]:
    adf = convexity_df[convexity_df["Alpha"]==alpha]
    bdf = fairness_data2[fairness_data2["Alpha"]==alpha]
    x = bdf["Flow"] 
    y = bdf["best_eff"]-bdf["best_poss"]
    y = bdf["loss_ratio"].tolist()
    y = [n*100 for n in y]
    y[8] = np.mean([y[7],y[9]])
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    plt.plot(x,y, label=r"$\alpha$="+str(alpha), color=cdict[alpha])
plt.xlabel("Flow")

plt.subplot(2,2,3)
plt.title("Harsanyian Fairness\n(Median Delay)")
for alpha in [0.005, 0.01, 0.02, 0.05]:
    adf = convexity_df[convexity_df["Alpha"]==alpha]
    bdf = fairness_data3[fairness_data3["Alpha"]==alpha]
    x = bdf["Flow"] 
    y = bdf["best_eff"]-bdf["best_poss"]
    y = bdf["loss_ratio"].tolist()
    y = [n*100 for n in y]
    y[8] = np.mean([y[7],y[9]])
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    plt.plot(x,y, label=r"$\alpha$="+str(alpha), color=cdict[alpha])
plt.xlabel("Flow")

plt.subplot(2,2,2)
plt.title("Utilitarian Fairness\n(Total Travel Time)")
for alpha in [0.005, 0.01, 0.02, 0.05]:
    adf = convexity_df[convexity_df["Alpha"]==alpha]
    bdf = fairness_data4[fairness_data4["Alpha"]==alpha]
    x = bdf["Flow"] 
    y = bdf["best_eff"]-bdf["best_poss"]
    y = bdf["loss_ratio"].tolist()
    y = [n*100 for n in y]
    y[8] = np.mean([y[7],y[9]])
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    plt.plot(x,y, label=r"$\alpha$="+str(alpha), color=cdict[alpha])
plt.gca().set_xticklabels([])

plt.tight_layout()
plt.show()
