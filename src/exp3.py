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
import numpy as np
import pandas as pd
import sys


locations = ['P']#, 'PN', 'SA']#, 'O']
days = ['01', '02', '03', '04', '05', '06', '07']

# Just Test conditions
# location = 'ME'
# day = '01'
# forecast_filepath = '../data/instances/P03FORECAST.csv'
# demand_filepath = '../data/instances/P03DEMAND.csv'
# param_filepath = '../data/parameters_P.json'

for location in locations:
    max_demand = 0
    demand_d = np.zeros(24)
    rad_p = np.zeros(24)
    wind_p = 0
    for day in days:
        forecast_filepath = os.path.join('../data/instances',str(location), str(location+day+'FORECAST.csv'))
        demand_filepath = os.path.join('../data/instances',str(location), str(location+day+'DEMAND.csv'))
        forecast_df, demand = read_data(forecast_filepath, demand_filepath, sepr=';')
        wind_p += pd.DataFrame.mean(forecast_df['Wt'])
        for keys, values in demand.items():
            demand_d[keys] += values
            rad_p[keys] += forecast_df['Rt'][keys]

            if values > max_demand:
                max_demand = values
    
    rad_p = np.true_divide(rad_p, len(days))
    rad_s = sum(i for i in rad_p)
    h_p = rad_s/1000 #Horas pico de funcionamiento de sistema solar
    
    wind_p = wind_p/len(days)
    demand_d = demand_d//len(days)

    row_list = [["Day", "Ub","Eb_init", "Lmin", "Lmax",
                                         "EBmax", "Gb_max",
                                         "Gd_max","Gd_min",
                                         "Gs_max",
                                         "Gw_max",
                                         "Z_Value",
                                         "p_bat",
                                         "p_nonatt"]]

    for day in days:

        for a in [0.3, 0.2, 0.3]: #Battery Cap

            for b in [2, 1, 2]: #

                for c in [2, 1, 2]:

                    for d in [0.35, 0.35, 0.45]: #Tasa de carga

                        for e in [0.3, 0.3, 0.6]: #Tasa de descarga

                            forecast_filepath = os.path.join('../data/instances',str(location), str(location+day+'FORECAST.csv'))
                            demand_filepath = os.path.join('../data/instances',str(location), str(location+day+'DEMAND.csv'))
                            param_filepath = os.path.join('../data/instances',str(location), str('parameters_P.json'))

                            forecast_df, demand = read_data(forecast_filepath, demand_filepath, sepr=';')
                            
                            generators_dict, battery = create_generators(param_filepath)

                            size = {}
                            
                            #Batería
                            battery.zb = a*max_demand

                            battery.eb_zero = 0.5 * battery.zb

                            l_min, l_max = b, c

                            battery.mcr = battery.zb * d
                            battery.mdr = battery.zb * e #Mayor a la tasa de carga
                            
                            #Diesel
                            generators_dict['Diesel1'].g_max = 0.8*max_demand #REVISAR!!!!!
                            generators_dict['Diesel1'].g_min = 0.2*max_demand
                            
                            #Solar
                            size['S'] = math.ceil((0.2*sum(i for i in demand_d))/(generators_dict['Solar1'].G_test * h_p))
                            
                            #Wind
                            f_plan = wind_p/generators_dict['Wind1'].w_a
                            # size['W'] = math.ceil((0.3*2*1000*sum(i for i in demand_d))/(generators_dict['Wind1'].ef 
                            #                                                             *(generators_dict['Wind1'].w_a**3)*generators_dict['Wind1'].p
                            #                                                             *generators_dict['Wind1'].s*24*f_plan))
                            
                            size['W'] = math.ceil((0.10*sum(i for i in demand_d))/(24*f_plan*20))
                            down_limit, up_limit = 0.1, 0.9

                            model = op.make_model(generators_dict, forecast_df, battery, demand,
                                                    down_limit, up_limit, l_min, l_max, size)

                            opt = pyo.SolverFactory('gurobi')

                            timea = time.time()
                            results = opt.solve(model)
                            execution_time = time.time() - timea

                            term_cond = results.solver.termination_condition
                            if term_cond != pyo.TerminationCondition.optimal:
                                print ("Termination condition={}".format(term_cond))
                                print(log_infeasible_constraints(model))
                                raise RuntimeError("Optimization failed.")


                            G_df, x_df, b_df, eb_df = create_results(model)

                            #s_bat = sum(sum(value(model.G[i,t]) for i in model.bat if (generators_dict[i].tec != "D" and generators_dict[i].tec != "NA")) for t in model.T)
                            s_bat = sum(sum(value(model.G[i,t]) for i in model.bat) for t in model.T)
                            t_gen = sum(sum(value(model.G[i,t]) for i in model.I) for t in model.T)
                            p_bat = s_bat/t_gen
                            
                            s_nonatt = sum(value(model.G['Fict',t]) for t in model.T)
                            s_dem = sum(i for i in demand_d)
                            p_nonatt = s_nonatt/s_dem


                            
                            row_list.append([day, str(a), str(battery.eb_zero), str(l_min), 
                                                str(l_max), str(battery.mcr), str(battery.mdr),
                                                generators_dict['Diesel1'].g_max, generators_dict['Diesel1'].g_min,
                                                0.2,
                                                0.2,
                                                value(model.generation_cost),
                                                p_bat,
                                                p_nonatt])


                            """
                            folder_name = export_results(model, location, day, x_df, G_df, b_df,
                                execution_time, down_limit, up_limit, l_max, l_min, term_cond)

                            print("Resultados en la carpeta: "+folder_name)
                            #model.EL.pprint()
                            #model.EB.pprint()
                            #model.temp.pprint()
                            """
                            #label = 'Battery capacity '+str(a)+' d_max'
                            name="microgrid_management"
                            visualize_results(G_df, x_df, demand, eb_df, name=name)#, label)
                            #model.G.pprint()
                            #del model
                            print('Ok')
                            #print(value(model.generation_cost))
                            sys.exit()
    with open(os.path.join('../results/', str(location)+'_3_11'+'.csv'), 'w', newline='') as file:
                                writer = csv.writer(file)
                                writer.writerows(row_list)
    file.close()
            