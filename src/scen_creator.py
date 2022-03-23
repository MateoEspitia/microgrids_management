#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import string
import random
import csv
import datetime
import seaborn as sns
import numpy as np

import json
import sys
import os
import time
import holidays
       

def read_data(demand_filepath):
    #Identify delimiter
    # with open(demand_filepath, newline='') as demand:
    #     dialect = csv.Sniffer().sniff(demand.read(1024))
    demand_df = pd.read_csv(demand_filepath, header=None)
    return demand_df


def split_days(demand_df, year=2019):
    start_date = datetime.date(year, 1, 1)
    end_date = datetime.date(year, 12, 31)
    
    days_n = []
    
    delta = end_date - start_date   # returns timedelta

    for i in range(delta.days + 1):
        day = start_date + datetime.timedelta(days=i)
        days_n.append(day.weekday())
    weekdays = []
    for i in days_n:
        if i < 5:
            weekdays.append(1)
        else:
            weekdays.append(0)
    
    n_weekdays = sum(i for i in weekdays)
    n_weekend = len(weekdays)-n_weekdays
    week_prob = n_weekdays/365
    
    return weekdays, week_prob

def select_day(weekdays, week_prob):
    rnd = random.random()
    print(rnd)
    if rnd < week_prob:
        select = 1
    else:
        select = 0
    print(select)
    day = random.randint(0, len(weekdays))
    while weekdays[day] != select:
        day = random.randint(0, len(weekdays))
    return day


def op1(day, demand_df, li, ls):
    #Aplica la tasa de aumento a la hora pico
    
    scen = demand_df.iloc[day].to_list()
    rnd = random.randint(li, ls) + random.random()
    tmp = scen.index(max(scen))
    
    scen[tmp] = scen[tmp]*(1 + rnd/100)
    
    return scen, tmp, rnd

def op2(day, demand, li, ls):
    scen = demand_df.iloc[day].to_list()
    rnd = random.randint(li, ls) + random.random()
    scen = [i * (1+(rnd/100)) for i in scen]
    
    return scen, rnd
    
    


if __name__ == "__main__":
    #random.seed(1234)
    demand_df = read_data('../data/dias_PN.csv')
    weekdays, week_prob = split_days(demand_df)
    fest_prob = 18/365
    
    day = select_day(weekdays, week_prob)
    
    scen, tmp, rnd = op1(day, demand_df, 2, 30)
    
    scen, rnd = op2(day, demand_df, 2, 10)
    
        
    
    