import FuentesClass as FuentesClass
import opt as opt
import pyomo.environ as pyo
from pyomo.core import value

import pandas as pd
import string
import random
import csv
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.graph_objects as go
plt.rcParams['text.usetex'] = True
import numpy as np

import json
import sys
import os
import time


def read_data(forecast_filepath, demand_filepath, sepr=','):#, filepath_bat):

    #Identify delimiter
    with open(forecast_filepath, newline='') as forecast:
        dialect = csv.Sniffer().sniff(forecast.read(1024))
    forecast_df = pd.read_csv(forecast_filepath, sep=dialect.delimiter, header=0, index_col='t')

    with open(demand_filepath, newline='') as forecast:
        dialect = csv.Sniffer().sniff(forecast.read(1024))
    demand = pd.read_csv(demand_filepath, squeeze=True, sep=dialect.delimiter, header=0)['demand'].to_dict()
    
    return forecast_df, demand

def create_generators(param_filepath):
    with open(param_filepath) as parameters:
        data = json.load(parameters)
    
    generators = data['generators']
    battery = data['battery']

    battery = FuentesClass.Bateria(*battery.values())

    generators_dict = {}
    for i in generators:
        if i['tec'] == 'S':
            obj_aux = FuentesClass.Solar(*i.values())
        elif i['tec'] == 'W':
            obj_aux = FuentesClass.Eolica(*i.values())
        elif i['tec'] == 'H':
            obj_aux = FuentesClass.Hidraulica(*i.values())
        elif i['tec'] == 'D':
            obj_aux = FuentesClass.Diesel(*i.values())
        elif i['tec'] == 'NA':
            obj_aux = FuentesClass.Fict(*i.values())
        # else:
        #     raise RuntimeError('Generator ({}) with unknow tecnology ({}).'.format(i['id_gen'], i['tec'])

        generators_dict[i['id_gen']] = obj_aux
        
    return generators_dict, battery

def create_results(model):
    #results = {}
    G_data = {i: [0]*len(model.T) for i in model.calI}
    for (i,t), v in model.G.items():
        G_data[i][t] = value(v)
    
    G_df = pd.DataFrame(G_data, columns=[*G_data.keys()])

    x_data = {i: [0]*len(model.T) for i in model.I}
    for (i,t), v in model.x.items():
        x_data[i][t] = value(v)
    
    x_df = pd.DataFrame(x_data, columns=[*x_data.keys()])

    b_data = {i: [0]*len(model.T) for i in model.I}
    for t, v in model.B.items():
        b_data[t] = value(v)
    
    b_df = pd.DataFrame(b_data, columns=[*b_data.keys()])

    eb_data = [0]*len(model.T)
    for t in model.T:
        eb_data[t] = value(model.EB[t])
    
    eb_df = pd.DataFrame(eb_data)

    return G_df, x_df, b_df, eb_df

def export_results(model, location, day, x_df, G_df, b_df, execution_time,
    down_limit, up_limit, l_max, l_min, term_cond):
    
    #current_path = os.getcwd()
    y = False
    while not(y):
        folder_name = location+'_'+day+'_'+str(random.choice(string.ascii_letters))+str(random.randint(0, 10))
        new_path = '../results/'+folder_name
        if not os.path.exists(new_path):
            os.makedirs(new_path)
            y = True
    x_df.to_csv(new_path+'/x.csv')
    G_df.to_csv(new_path+'/G.csv')
    b_df.to_csv(new_path+'/b.csv')

    with open('../results/results.csv', 'a') as file:
        writer = csv.writer(file)
        writer.writerow([folder_name, down_limit, up_limit, l_min, l_max, 
            execution_time, pyo.value(model.generation_cost), term_cond])
    

    return folder_name

def visualize_results(g_df, x_df, d_df, eb_df, label=None, name=None):
    """
    ##INICIAL
    x_df.insert(0, "period", x_df.index)
    g_df.insert(0, "period", g_df.index)
    # b_df.insert(0, "period", b_df.index)
    
    #
    sns.set_style("whitegrid")
    ax = sns.lineplot(data=x_df.drop('period', axis=1))
    ax.set(xticks=x_df.period)
    ax.legend(loc='right', bbox_to_anchor=(1.25, 0.5), ncol=1)
    plt.show()
    #
    
    sns.set_style("whitegrid")
    ax = sns.lineplot(data=g_df.drop('period', axis=1), dashes=False)
    ax.set(xticks=g_df.period)
    ax.legend(loc='right', bbox_to_anchor=(1.25, 0.5), ncol=1)
    plt.show()
    
    #
    fig = go.Figure()
    # Create and style traces
    fig.add_trace(go.Scatter(x=g_df['period'], y=g_df['Solar1'], name='Solar1',
                            line=dict(color='firebrick', width=1)))
    fig.add_trace(go.Scatter(x=g_df['period'], y=g_df['Wind1'], name='Wind1',
                            line=dict(color='royalblue', width=1)))
    fig.add_trace(go.Scatter(x=g_df['period'], y=g_df['Hydro1'], name='Hydro1',
                            line=dict(color='green', width=1)))
    fig.add_trace(go.Scatter(x=g_df['period'], y=g_df['Diesel1'], name='Diesel1',
                            line=dict(color='red', width=1)))
    fig.add_trace(go.Scatter(x=g_df['period'], y=g_df['Diesel2'], name='Diesel2',
                            line=dict(color='black', width=1)))


    # Edit the layout
    fig.update_layout(title='Energy dispatch',
                    xaxis_title='period',
                    yaxis_title='generation (kw)')
    


    fig.show()
    
    """
    data_dem = list(d_df.values())
    
    data_s = g_df['Solar1'].to_numpy()
    data_w = g_df['Wind1'].to_numpy()
    data_d = g_df['Diesel1'].to_numpy()
    data_b = g_df['Battery1'].to_numpy()
    data_f = g_df['Fict'].to_numpy()
    data_eb = eb_df[0].to_numpy() * -1
    t = np.arange(len(data_s))
    
    
    

    plt.figure(figsize=(11,6))
    plt.ylim(min(data_eb)-50, max(data_w+data_s+data_b+data_d+data_f)+200)
    
    plt.bar(t,data_eb,color="black",label="Charge")
    plt.bar(t,data_w,color="limegreen",label="Wind")
    plt.bar(t,data_s,color="gold",bottom=data_w,label="Solar")
    plt.bar(t,data_d,color="saddlebrown",bottom=data_w+data_s,label="Diesel")
    plt.bar(t,data_b,color="royalblue",bottom=data_w+data_s+data_d,label="Battery")
    plt.bar(t,data_f,color="gray",bottom=data_w+data_s+data_d+data_b,label="Unattended demand")
    
    plt.plot(data_dem, color='red', marker='o', linestyle='dashed', linewidth=3, markersize=4, label="Demand")
    #plt.bar(t,data_eb,color="black",bottom=data_s+data_w+data_d+data_b+data_f,label="Charge")

    plt.xlabel("Time (hour)", fontsize=15)
    plt.ylabel("Generation (W)", fontsize=15)

    plt.legend(loc="best", ncol=len(g_df.columns)+2, fontsize=10.5)

    #loc = [0.5, 1]
    if label:
        plt.suptitle(label, fontsize=20)
    
    if name:
        plt.savefig(name+'.pdf', bbox_inches='tight')
    
    plt.show()
    
    return None


if __name__ == "__main__":
    
    locations = ['P', 'SA', 'PN']
    days = ['01', '02', '03', '04', '05', '06', '07']
    
    # Just Test conditions
    location = 'ME'
    day = '01'
    forecast_filepath = '../data/instances/P/P03FORECAST.csv'
    demand_filepath = '../data/instances/P/P03DEMAND.csv'
    param_filepath = '../data/parameters_P.json'
    

    # forecast_filepath = os.path.join('../data/instances', str(location+day+'FORECAST.csv'))
    # demand_filepath = os.path.join('../data/instances', str(location+day+'DEMAND.csv'))
    
    forecast_df, demand = read_data(forecast_filepath, demand_filepath, sepr=';')
    
    generators_dict, battery = create_generators(param_filepath)

    down_limit, up_limit, l_min, l_max = 0.2, 0.85, 4, 4

    
    
    model = opt.make_model(generators_dict, forecast_df, battery, demand,
                            down_limit, up_limit, l_min, l_max)

    opt = pyo.SolverFactory('gurobi')

    timea = time.time()
    results = opt.solve(model)
    execution_time = time.time() - timea

    term_cond = results.solver.termination_condition
    if term_cond != pyo.TerminationCondition.optimal:
        print ("Termination condition={}".format(term_cond))
        raise RuntimeError("Optimization failed.")
    

    G_df, x_df, b_df, eb_df = create_results(model)
    """
    folder_name = export_results(model, location, day, x_df, G_df, b_df,
        execution_time, down_limit, up_limit, l_max, l_min, term_cond)
    
    print("Resultados en la carpeta: "+folder_name)
    #model.EL.pprint()
    #model.EB.pprint()
    #model.temp.pprint()
    """
    visualize_results(G_df, x_df, b_df, eb_df)
    model.G.pprint()
    
    
    