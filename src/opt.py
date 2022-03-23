import pyomo.environ as pyo
import pandas as pd
import sys

def make_model(generators_dict=None, forecast_df=None, battery=None, demand=None,
    down_limit=None, up_limit=None, l_min=None, l_max=None, size=None):
    """
    Crea el modelo.
    
    Args:
        I (list) generadores instalados en la microred.
        times (int) numero de periodos de tiempo sobre los cuales se va a ejecutar el modelo.
        param (array) parametros propios para los generadores I.
        
    Returns:
        model (Pyomo ConcreteModel)
    """

    model = pyo.ConcreteModel(name="Gestion de Micro Redes")
    
    model.I = pyo.Set(initialize=[i for i in generators_dict.keys()])
    model.bat = pyo.Set(initialize=[battery.id_bat])
    model.calI = model.I | model.bat
    model.T = pyo.Set(initialize=[i for i in range(len(forecast_df))])

    model.D = pyo.Param(model.T, initialize=demand)

    model.P = pyo.Param(initialize=5)

    model.up_limit = pyo.Param(initialize=up_limit)
    model.down_limit = pyo.Param(initialize= down_limit)
    model.l_min = pyo.Param(initialize=l_min)
    model.l_max = pyo.Param(initialize=l_max)

    model.x = pyo.Var(model.I, model.T, within=pyo.Binary, initialize=0)

    model.G = pyo.Var(model.calI, model.T, within=pyo.NonNegativeReals, initialize=0)

    model.EB = pyo.Var(model.T, within=pyo.NonNegativeReals, initialize=0) #Power intended for charging the storage unit in time interval t.

    model.B = pyo.Var(model.T, within=pyo.NonNegativeReals) #Power level in battery unit over time period t.

    model.y = pyo.Var(model.T, within=pyo.Binary, initialize=0)

    model.Ic = pyo.Var(model.T, within=pyo.NonNegativeReals) #Numero de periodos de carga continua

    model.z = pyo.Var(model.T, within=pyo.NonNegativeReals)

    model.Sc = pyo.Var(within=pyo.NonNegativeReals)

    model.pmin = pyo.Var(model.T, within=pyo.Binary, initialize=0)

    model.pmax = pyo.Var(model.T, within=pyo.Binary, initialize=0)

    def B_rule(model, t):
        if t == 0:
            expr = battery.eb_zero * (1-battery.o)
            expr += model.EB[t] * battery.ef
            expr -= (model.G[battery.id_bat, t]/battery.ef_inv)
            return model.B[t] == expr
        else:
            expr = model.B[t-1] * (1-battery.o)
            expr += model.EB[t] * battery.ef
            expr -= (model.G[battery.id_bat, t]/battery.ef_inv)
            return model.B[t] == expr

    model.B_rule = pyo.Constraint(model.T, rule=B_rule)

    model.EL = pyo.Var(model.T, within=pyo.NonNegativeReals, initialize=0) #Power generated at t time from S and W technologies to satisfying the demand.
    
    model.EW = pyo.Var(model.T, within=pyo.NonNegativeReals, initialize=0) #Electric power discarded due to over generation in time interval t.

    def Bconstraint_rule(model, t):
        # for b in model.bat:
        #     return (0, model.G[b,t], 0)
        return model.B[t] <= battery.zb

    model.Bconstraint = pyo.Constraint(model.T, rule=Bconstraint_rule)
    
    def G_rule(model, i, t):
        gen = generators_dict[i]
        if gen.tec == 'S':
            return model.G[i,t] == size[gen.tec] * gen.G_test * (forecast_df['Rt'][t]/gen.R_test) * model.x[i,t]
        if gen.tec == 'W':
            if forecast_df['Wt'][t] < gen.w_min:
                return model.G[i,t] == 0
            elif forecast_df['Wt'][t] < gen.w_a:
                # return model.G[i,t] == 0
                return model.G[i,t] == (size[gen.tec] * (1/2) * gen.p * gen.s * (forecast_df['Wt'][t]**3) * gen.ef *gen.n* model.x[i,t])/1000
            elif forecast_df['Wt'][t] <= gen.w_max:
                return model.G[i,t] == (size[gen.tec] * (1/2) * gen.p * gen.s * (gen.w_a**3) * gen.ef *gen.n* model.x[i,t])/1000
            else:
                return model.G[i,t] == 0
        if gen.tec == 'H':
            #A Corregir
            return model.G[i,t] == gen.p * 9.8 * gen.ht * gen.ef * forecast_df['Qt'][t] * model.x[i,t]
        if gen.tec == 'D':
            return 0 <= model.G[i,t] - model.x[i,t]*gen.g_min
        if gen.tec == 'G':
            return model.G[i,t] <= model.x[i,t]*gen.g_max
        if gen.tec == 'NA':
            return pyo.Constraint.Skip
            
    
    model.G_rule = pyo.Constraint(model.I, model.T, rule=G_rule)

    def maxG_diesel_rule(model, i, t):
        gen = generators_dict[i]
        if gen.tec == 'D':
            return 0 <= model.x[i,t]*gen.g_max - model.G[i,t]
        else:
            return pyo.Constraint.Skip
        
    model.maxG_diesel_rule = pyo.Constraint(model.I, model.T, rule=maxG_diesel_rule)

    def Gconstraint_rule(model, t):
        ls = sum(model.G[i,t] for i in model.I if generators_dict[i].tec == 'S' or 
                    generators_dict[i].tec == 'W' or generators_dict[i].tec == 'H' or
                    generators_dict[i].tec == 'D')

        rs = model.EL[t] + model.EB[t] + model.EW[t]
        return ls == rs

    model.Gconstraint = pyo.Constraint(model.T, rule=Gconstraint_rule)
    
    def Dconstraint_rule(model, t):
        
        rs = model.EL[t]
        rs += sum(model.G[b,t] for b in model.bat)
        if 'Fict' in generators_dict.keys():
            rs += model.G['Fict', t]
        # rs += sum(model.G[i,t] for i in model.I if generators_dict[i].tec == 'H')
        # rs += sum(model.G[i,t] for i in model.I if generators_dict[i].tec == 'D')
        # rs -= model.temp[t] #Variable que guarda la energia desperdiciada en las fuentes H y D
        
        return model.D[t] == rs #(model.D[t], rs)

    model.Dconstraint = pyo.Constraint(model.T, rule=Dconstraint_rule)
    #sys.exit()

    
    #----------Nuevas restricciones control de baterías (SEGUNDA OPCIÓN)
    #Tasa máxima de carga y descarga
    def maxDescRate_rule(model, t):
        return model.G[battery.id_bat, t] <= battery.mdr

    model.maxDescRate_constraint = pyo.Constraint(model.T, rule=maxDescRate_rule)

    def maxChaRate_rule(model, t):
        return model.EB[t] <= battery.mcr

    model.maxChaRate_constraint = pyo.Constraint(model.T, rule=maxChaRate_rule)

    

    def DescargaConstraint_rule(model, t):
        return battery.zb * model.y[t] >= model.G[battery.id_bat, t]
    
    model.DescargaConstraint = pyo.Constraint(model.T, rule=DescargaConstraint_rule)

    def ndc_rule(model, t):
        return battery.epsilon * model.y[t] <= model.G[battery.id_bat, t]
    
    model.ndc = pyo.Constraint(model.T, rule=ndc_rule)

    def Sconstraint_rule(model):
        return model.Sc == sum(model.z[t] for t in model.T)

    model.Sconstraint = pyo.Constraint(rule=Sconstraint_rule)

    def aux1_rule(model, t):
        if t < 1:
            return pyo.Constraint.Skip
        else:
            return model.y[t]-model.y[t-1] <= model.z[t]
    
    model.aux1_constraint = pyo.Constraint(model.T, rule=aux1_rule)

    def maxS_rule(model):
        return model.Sc <= battery.M
    
    model.maxS = pyo.Constraint(rule=maxS_rule)

    #Descarga profunda

    def deepDesc1_rule(model, t):
        return (model.B[t]/battery.zb) + model.pmin[t] >= model.down_limit
    
    model.deepDesc1_constraint = pyo.Constraint(model.T, rule=deepDesc1_rule)

    def deepDesc2_rule(model, t):
        return (model.B[t]/battery.zb) - (1 - model.pmin[t]) <= model.down_limit
    
    model.deepDesc2_constraint = pyo.Constraint(model.T, rule=deepDesc2_rule)

    #Sobrecarga
    def overload1_rule(model, t):
        return (model.B[t]/battery.zb) - model.pmax[t] <= model.up_limit
    
    model.overload1_constraint = pyo.Constraint(model.T, rule=overload1_rule)

    def overload2_rule(model, t):
        return (model.B[t]/battery.zb) + (1 - model.pmax[t]) >= model.up_limit
    
    model.overload2_constraint = pyo.Constraint(model.T, rule=overload2_rule)

    # Numero de periodos máximos en los que se entra en descarga profunda

    def l_min_rule(model):
        return sum(model.pmin[t] for t in model.T) <= model.l_min
    model.l_min_constraint = pyo.Constraint(rule=l_min_rule)

    # Numero de periodos máximos en los que se entra en sobrecarga

    def l_max_rule(model):
        return sum(model.pmax[t] for t in model.T) <= model.l_max
    model.l_max_constraint = pyo.Constraint(rule=l_max_rule)
    
    
    #Funcion objetivo

    def obj_rule(model):

        return sum(sum(generators_dict[i].va_op * model.G[i,t] for t in model.T)for i in model.I) +0.1*sum(model.EW[t] for t in model.T)# Incluir temporal

    model.generation_cost = pyo.Objective(rule=obj_rule)

    return model

if __name__ == "__main__":
    filepath = 'parametros.csv'
    parametros = pd.read_csv(filepath, sep=',', header=None)#.sort_index(ascending=False)

    for i in parametros:
        print(parametros[i])

    # with open(filepath, 'r') as thecsv:
    #     for row in thecsv:
    #         print(row)


    I = [1, 3, 2]
    times = 24
    # model = make_model(I=I, times=times)
    # model.pprint()
