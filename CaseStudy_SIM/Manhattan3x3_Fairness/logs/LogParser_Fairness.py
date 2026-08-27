# Imports
import os
import numpy as np




# Folder Parameter
# folder = "Manhattan3x3"
folder = "signalized_intersection_control_auction/src/Logs/Manhattan3x3/"
outputfile = "log_fixed_programme_fairness.csv"



# Methods
def parseFile(file):
    f = open(file, "r")
    f.readline()
    f.readline()
    f.readline()
    f.readline()
    f.readline()
    f.readline()
    relevant_line = f.readline()
    if len(relevant_line)!=0:
        mean = relevant_line.replace("\n", "").strip()
        f.close()
        try:
            parts = mean.split(" ")
            parts = [float(p) for p in parts]
        except:
            parts -1 # = [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan]
        return parts
    else:
        return -1

"""
33


1932.0 
8.189947236878645 
572.0 
1892.0 
9.745104895104896 
9.633333333333333 
4.02101213458883 
189244567.22744542 
4300144.129626225 
0.2948864913633828 
0.0005037239995520968 
0.2115604116632367 
4.7 
17.32500264533779 
0.1458346916678765 
-0.17159000589210688 
135.0 
37.0 
37.54545454545455 
35.92857142857143 
33.64912280701754 
0.2275058400511391 
0.00029816840548089 
0.15813313735885579 
4.378388530645463 
4.02101213458883 
0.08886835438141752 
-0.09707047753022922 
33.75 
9.716666666666667 
10.32878787878788 
9.891071428571431 
9.542397660818713
"""

# Files
files = os.listdir(folder)

# traffic_flows = [50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600]
traffic_flows = [50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600]
fW = open(outputfile, "w+")
fW.write("Flow,Parameter1,Parameter2,Errors,Mean,Mean,Mean,Mean,Mean,Mean,Mean,Mean,Mean,Mean,Mean,Mean,Mean,Mean,Mean,Mean,Mean,Mean,Mean,Mean,Mean,Mean,Mean,Mean,Mean,Mean,Mean,Mean,Mean,Mean,Mean,Mean,Mean,Median,Median,Median,Median,Median,Median,Median,Median,Median,Median,Median,Median,Median,Median,Median,Median,Median,Median,Median,Median,Median,Median,Median,Median,Median,Median,Median,Median,Median,Median,Median,Median,Median,Std,Std,Std,Std,Std,Std,Std,Std,Std,Std,Std,Std,Std,Std,Std,Std,Std,Std,Std,Std,Std,Std,Std,Std,Std,Std,Std,Std,Std,Std,Std,Std,Std,\n")
fW.write("Flow,Parameter1,Parameter2,Errors,Total_Throuput,Total_AvQueueLength,NumCompletedVeh,NumVehIntersectionPassages,VehAvDelay,VehMdDelay,VehStDelay,EmissionCO2,EmissionNoise,TotFairGini,TotFairHerf,TotFairHoov,TotFairPalm,TotFairStd,TotFairThlT,TotFairThlL,TotFairMax,TotFairTop01,TotFairTop02,TotFairTop05,TotFairTop10,DpiFairGini,DpiFairHerf,DpiFairHoov,DpiFairPalm,DpiFairStd,DpiFairThlT,DpiFairThlL,DpiFairMax,DpiFairTop01,DpiFairTop02,DpiFairTop05,DpiFairTop10,Total_Throuput,Total_AvQueueLength,NumCompletedVeh,NumVehIntersectionPassages,VehAvDelay,VehMdDelay,VehStDelay,EmissionCO2,EmissionNoise,TotFairGini,TotFairHerf,TotFairHoov,TotFairPalm,TotFairStd,TotFairThlT,TotFairThlL,TotFairMax,TotFairTop01,TotFairTop02,TotFairTop05,TotFairTop10,DpiFairGini,DpiFairHerf,DpiFairHoov,DpiFairPalm,DpiFairStd,DpiFairThlT,DpiFairThlL,DpiFairMax,DpiFairTop01,DpiFairTop02,DpiFairTop05,DpiFairTop10,Total_Throuput,Total_AvQueueLength,NumCompletedVeh,NumVehIntersectionPassages,VehAvDelay,VehMdDelay,VehStDelay,EmissionCO2,EmissionNoise,TotFairGini,TotFairHerf,TotFairHoov,TotFairPalm,TotFairStd,TotFairThlT,TotFairThlL,TotFairMax,TotFairTop01,TotFairTop02,TotFairTop05,TotFairTop10,DpiFairGini,DpiFairHerf,DpiFairHoov,DpiFairPalm,DpiFairStd,DpiFairThlT,DpiFairThlL,DpiFairMax,DpiFairTop01,DpiFairTop02,DpiFairTop05,DpiFairTop10,\n")
for flow in traffic_flows:
    for parameter1 in range(1, 41, 1):
        for parameter2 in range(1, 41, 1):
            print(flow, parameter1, parameter2)
            rel_files = []
            for file in files:
                if file.startswith("log_fixed_programme_"+str(flow)+"_"+str(parameter1)+"_"+str(parameter2)+"_"):
                    rel_files.append(file)
            results = []
            count_errors = 0
            for file in rel_files:
                res = parseFile(folder+"/"+file)
                if not res==-1:
                    if np.nan in res:
                        count_errors += 1
                    results.append(res)
            if len(results)==0:
                count_errors = 10
                mean = [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
                medi = [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
                std = [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
            else:
                results = np.asarray(results)
                mean = np.nanmean(results, axis=0)
                medi = np.nanmedian(results, axis=0)
                std = np.nanstd(results, axis=0)
            fW.write(str(flow))
            fW.write(",")
            fW.write(str(parameter1))
            fW.write(",")
            fW.write(str(parameter2))
            fW.write(",")
            fW.write(str(count_errors))
            fW.write(",")
            for r in mean:
                fW.write(str(r))
                fW.write(",")
            for r in medi:
                fW.write(str(r))
                fW.write(",")
            for r in std:
                fW.write(str(r))
                fW.write(",")
            fW.write("\n")
fW.close()
