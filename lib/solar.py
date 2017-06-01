import warnings
warnings.filterwarnings("ignore")

from openmdao.api import Component, Group, Problem, IndepVarComp
from openmdao.api import ScipyOptimizer

import numpy as np
import datetime

from lib.parser import get_data, get_nrel

# use the DC power value from the NREL data (instead of the AC)
power_idx = -2

class DataSource(Component):
    """Parses NREL data and provides associated transient outputs"""

    nrel_api_key = "DEMO_KEY"
    location = "Cleveland, OH USA"
    array_type = 0

    def __init__(self, fns=None):
        super(DataSource, self).__init__()

        # length of time series
        self.n = 8760

        # create array of corresponding dates
        next_year = datetime.datetime.now().year + 1
        start = datetime.datetime(next_year, 1, 1)
        h = datetime.timedelta(hours=1)
        self.dates = [start + i*h for i in range(self.n)]
        self.weekdays = np.array([i.weekday() for i in self.dates])
        
        # set efficiency from input
        self.start_time = 0
        self.end_time = 23
        self.efficiency = 0.96

        self.add_param("array_power", 100.0, units="W")
        self.add_param("array_tilt", 20.0, units="deg")
        self.add_param("azimuth", 180.0, units="deg")
        self.add_param("losses", 14.0)

        # Variables that will be outputted
        self.add_output("cell_temperature", np.zeros(self.n), units="degC")
        self.add_output("ambient_temperature", np.zeros(self.n), units="degC")
        self.add_output("hour", np.zeros(self.n), units="h")
        self.add_output("day", np.zeros(self.n), units="d")
        self.add_output("weekday", self.weekdays)
        self.add_output("month", np.zeros(self.n), units="mo")
        self.add_output("P_generated", np.zeros(self.n), units="W")
        self.add_output("wind", np.zeros(self.n), units="m/s")
        self.add_output("irradiance", np.zeros(self.n))

    def solve_nonlinear(self, p, u, r):
        # get data from NREL servers, scale low power array if necessary
        if p['array_power'] < 50.0:
            self.data = get_nrel(self.nrel_api_key, self.location, 50.0, 
                                 p['azimuth'], p['array_tilt'], p['losses'], 
                                 self.array_type)
            self.data[:,-2:] = self.data[:,-2:] * (p['array_power'] / 50.0)
        else:    
            self.data = get_nrel(self.nrel_api_key, self.location, 
                                 p['array_power'], p['azimuth'], 
                                 p['array_tilt'], p['losses'], 
                                 self.array_type)

        # usable PV power only between specified start and end times
        idx = np.where(self.data[:, 2] < self.start_time)
        self.data[idx, power_idx] = 0.0
        idx = np.where(self.data[:, 2] > self.end_time)
        self.data[idx, power_idx] = 0.0

        u['P_generated'] = self.data[:, power_idx]

        # parse and output other data values directly
        u['month'] = self.data[:,0]
        u['day'] = self.data[:,1]
        u['hour'] = self.data[:,2]
        u['cell_temperature'] = self.data[:,8]
        u['ambient_temperature'] = self.data[:,5]
        u['wind'] = self.data[:,6]
        u['irradiance'] = self.data[:,4]


class Batteries(Component):
    """Battery model, computed state of charge (SOC) over time"""
    
    def __init__(self, n):
        super(Batteries, self).__init__()
        self.n = n

        # inputs: battery power capacity, and PV generated power and load
        # consumptions over time
        self.add_param("power_capacity", 0.0, units="W*h")
        self.add_param("P_generated", np.zeros(self.n), units="W")
        self.add_param("P_consumption", np.zeros(self.n), units="W")

        # output: resulting state of charge
        self.add_output("SOC", np.ones(self.n), units="unitless")

    def solve_nonlinear(self, p, u, r):

        # initial state of charge at beginning of time series: 100%
        SOC = 1.0

        # Integrate SOC for each time point (hour by hour)
        for i in range(self.n):
            old_SOC = SOC

            # available energy in battery: Wh
            available = SOC * p['power_capacity']
            # PV energy generated during this hour: Wh
            generated = p['P_generated'][i]
            # Energy consumed by loads during this hour: Wh
            consumed = p['P_consumption'][i]

            # Power balance
            diff = available + generated - consumed

            # Base SOC calculation: Wh / Wh -> percentage
            SOC = (diff) / p['power_capacity'] 

            # Bound between 0 and 100 %
            if SOC > 1.0:
                SOC = 1.0
            elif SOC < 0:
                SOC = 0.0

            # trapezoid rule: integral(W * dt, t=hour_i..hour_i+1) = 1 * (W_i+1 - W_i)/2 [units: W*h]
            u['SOC'][i] = (SOC + u['SOC'][i-1])/2.0 

class Costs(Component):
    """Basic cost model"""

    def __init__(self):
        super(Costs, self).__init__()
        # inputs
        self.add_param("power_capacity", 50.0, units="W*h")
        self.add_param("array_power", 100.0, units="W")

        # output
        self.add_output("cost", 0.0)

    def solve_nonlinear(self, p, u, r):
        # cost estimate is $1.33 per panel watt, and $0.20 per battery Wh
        u['cost'] = 1.33 * p['array_power'] + 0.2 * p['power_capacity']




