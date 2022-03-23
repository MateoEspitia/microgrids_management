import pandas as pd
import csv
import matplotlib.pyplot as plt
import numpy as np


file_path = '../results/P_2.csv'

results_df = pd.read_csv(file_path, sep=',', header=0)

r = [0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3]

sol = {0:0, 0.05:0, 0.1:0, 0.15:0, 0.2:0, 0.25:0, 0.3:0 }
win = {0:0, 0.05:0, 0.1:0, 0.15:0, 0.2:0, 0.25:0, 0.3:0 }

for k in r:
    sol[k] = sum(results_df['p_sol'][i] for i in range(len(results_df)) if(results_df['Gs_max'][i] == k))/49
    win[k] = sum(results_df['p_win'][i] for i in range(len(results_df)) if(results_df['Gw_max'][i] == k))/49
    
for k in r:
    sol[k] = sum(results_df['Z_Value'][i] for i in range(len(results_df)) if(results_df['Gs_max'][i] == k))/49
    win[k] = sum(results_df['Z_Value'][i] for i in range(len(results_df)) if(results_df['Gw_max'][i] == k))/49

tot = {0:0, 0.05: 0,0.1: 0, 0.15: 0, 0.2: 0, 0.25: 0, 0.3: 0, 0.35: 0, 0.4: 0, 0.45: 0, 0.5: 0, 0.55: 0, 0.6: 0}

rr = [0, 0.05,0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6]#np.arange(0, 0.61, 0.05)
con = {0: 0, 0.05: 0,0.1: 0, 0.15: 0, 0.2: 0, 0.25: 0, 0.3: 0, 0.35: 0, 0.4: 0, 0.45: 0, 0.5: 0, 0.55: 0, 0.6: 0}

for k in rr:
    for i in range(len(results_df)):
        if k == results_df['Gs_max'][i]+results_df['Gw_max'][i]:
            tot[k] += results_df['p_clean'][i]
            con[k] += 1
    #tot[round(k,2)] = sum(results_df['p_clean'][i] for i in range(len(results_df)) if(results_df['Gs_max'][i]+results_df['Gw_max'][i] == round(k,2)))
    #con[round(k,2)] = sum(1 for i in range(len(results_df)) if(results_df['Gs_max'][i]+results_df['Gw_max'][i] == round(k,2)))

pr = {}
for i in rr:
    pr[round(i,2)] = tot[round(i,2)]/con[round(i,2)]

#plt.figure(figsize=(9,7))
#plt.bar(r, list(sol.values()), color="yellow",label="Charge", edgecolor='blue')