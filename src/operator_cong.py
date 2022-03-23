#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import scen_creator as sc

import numpy as np
import statistics as stat


if __name__ == "__main__":
    #random.seed(1234)
    demand_df = sc.read_data('../data/dias_PN.csv')
    
    #Hora pico promedio - opc1
    x = np.amax(demand_df, 1)
    ma = stat.mean(x)
    m = stat.mean(demand_df.mean())
    dist = (ma -m)/ma
    
    #Distancia de hora pico promedio - opc2
    x = np.amax(demand_df, 1)
    ma = max(x)
    mi = min(x)
    m = stat.mean(demand_df.mean())
    dist_max = (ma -m)/m
    dist_min = (mi-m)/m
    
    
    
    
    
