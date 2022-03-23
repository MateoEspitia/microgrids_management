import FuentesClass as FuentesClass
import opt as opt
import pandas as pd
import json
import sys
import pyomo.environ as pyo
from pyomo.core import value

import GestionMR as GestionMR

import os
import click

@click.command()
@click.option('--input_file', '-da', default=None, type=str, help='path of data .csv file')



if __name__ == "__main__":
    param_filepath = '../data/parameters.json'
    locations = ['P', 'SA', 'PN']
    days = ['01', '02', '03', '04', '05', '06', '07']
    #forecast_filepath = '../data/instances/'
    #demand_filepath = '../data/demand.csv'
    forecast_filepath = os.path.join('../data/instances', str(location+day+'FORECAST.csv'))
    demand_filepath = os.path.join('../data/instances', str(location+day+'DEMAND.csv'))
    forecast_df, demand = read_data(forecast_filepath, demand_filepath)
    generators_dict, battery = create_generators(param_filepath)
    
    
    model = opt.make_model(generators_dict, forecast_df, battery, demand)
    model.maxS.pprint()

    #model.EW.pprint()
    #model.maxG_diesel_rule.pprint()
    
    opt = pyo.SolverFactory('gurobi')
    results = opt.solve(model)
    term_cond = results.solver.termination_condition
    if term_cond != pyo.TerminationCondition.optimal:
        print ("Termination condition={}".format(term_cond))
        raise RuntimeError("Optimization failed.")
    model.G.pprint()
    G_df = export_results(model)
    print(G_df)
    #model.EL.pprint()
    #model.EB.pprint()
    #model.temp.pprint()