from GestionMR import read_data, create_generators, create_results, export_results, visualize_results

import opt as op
import pyomo.environ as pyo
from pyomo.core import value
from pyomo.util.infeasible import log_infeasible_constraints

import csv
import random
import math

random.seed(1234)

import os
import time
import sys


locations = ['P', 'PN', 'SA']#, 'O']
days = ['01', '02', '03', '04', '05', '06', '07']

# Just Test conditions
# location = 'ME'
# day = '01'
# forecast_filepath = '../data/instances/P03FORECAST.csv'
# demand_filepath = '../data/instances/P03DEMAND.csv'
# param_filepath = '../data/parameters_P.json'

for location in locations:
    max_demand = 0
    max_rad = 0
    max_wind = 0
    for day in days:
        forecast_filepath = os.path.join('../data/instances',str(location), str(location+day+'FORECAST.csv'))
        demand_filepath = os.path.join('../data/instances',str(location), str(location+day+'DEMAND.csv'))
        forecast_df, demand = read_data(forecast_filepath, demand_filepath, sepr=';')
        if max(demand.values()) > max_demand:
            max_demand = max(demand.values())
        if max(forecast_df['Rt']) > max_rad:
            max_rad = max(forecast_df['Rt'])
        if max(forecast_df['Wt']) > max_wind:
            max_wind = max(forecast_df['Wt'])

    row_list = [["Day", "Ub","Eb_init", "Lmin", "Lmax",
                                         "EBmax", "Gb_max",
                                         "Gd_max","Gd_min",
                                         "Gs_max",
                                         "Gw_max",
                                         "Z_Value",
                                         "p_clean"]]

    for day in days:

        for a in [0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3]:

            for b in [0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3]:

                forecast_filepath = os.path.join('../data/instances',str(location), str(location+day+'FORECAST.csv'))
                demand_filepath = os.path.join('../data/instances',str(location), str(location+day+'DEMAND.csv'))
                param_filepath = os.path.join('../data/instances',str(location), str('parameters_P.json'))

                forecast_df, demand = read_data(forecast_filepath, demand_filepath, sepr=';')
                
                generators_dict, battery = create_generators(param_filepath)

                """
                
                #Batería
                battery.zb = a*max_demand

                battery.eb_zero = 0.5 * battery.zb

                l_min, l_max = b, c

                battery.mcr = battery.zb * d
                battery.mdr = battery.zb * e #Mayor a la tasa de descarga
                """
                l_min, l_max = 2, 2
                
                #Diesel
                generators_dict['Diesel1'].g_max = 1.1*max_demand
                generators_dict['Diesel1'].g_min = 0.3*max_demand
                
                #Solar
                generators_dict['Solar1'].A = math.ceil((a*max_demand)/(generators_dict['Solar1'].ef * max_rad))
                
                #Wind
                generators_dict['Wind1'].s = math.ceil((b*2*max_demand)/(generators_dict['Wind1'].ef 
                                                                            *(max_wind**3)*generators_dict['Wind1'].p))
                
                
                down_limit, up_limit = 0.2, 0.9

                model = op.make_model(generators_dict, forecast_df, battery, demand,
                                        down_limit, up_limit, l_min, l_max)

                opt = pyo.SolverFactory('gurobi')

                timea = time.time()
                results = opt.solve(model)
                execution_time = time.time() - timea

                term_cond = results.solver.termination_condition
                if term_cond != pyo.TerminationCondition.optimal:
                    print ("Termination condition={}".format(term_cond))
                    print(log_infeasible_constraints(model))
                    raise RuntimeError("Optimization failed.")


                G_df, x_df, b_df = create_results(model)

                s_clean = sum(sum(value(model.G[i,t]) for i in model.I if (generators_dict[i].tec != "D" and generators_dict[i].tec != "NA")) for t in model.T)
                t_gen = sum(sum(value(model.G[i,t]) for i in model.I) for t in model.T)
                p_clean = s_clean/t_gen


                
                row_list.append([day, str(battery.zb), str(battery.eb_zero), str(l_min), 
                                    str(l_max), str(battery.mcr), str(battery.mdr),
                                    generators_dict['Diesel1'].g_max, generators_dict['Diesel1'].g_min,
                                    a*max_demand,
                                    b*max_demand,
                                    value(model.generation_cost),
                                    p_clean])


                """
                folder_name = export_results(model, location, day, x_df, G_df, b_df,
                    execution_time, down_limit, up_limit, l_max, l_min, term_cond)

                print("Resultados en la carpeta: "+folder_name)
                #model.EL.pprint()
                #model.EB.pprint()
                #model.temp.pprint()
                """
                
                #visualize_results(G_df, x_df, b_df)
                #model.G.pprint()
                #del model
                print('Ok')
    with open(os.path.join('../results/', str(location)+'_2'+'.csv'), 'w', newline='') as file:
                                writer = csv.writer(file)
                                writer.writerows(row_list)
    file.close()
            