import sys
py_ver = 2
if (sys.version_info > (3, 0)):
    py_ver = 3

import numpy as np

import requests
import os

fpath = os.path.dirname(os.path.realpath(__file__))

def get_nrel(key, address, panel_watts, tilt=20.0, losses=14.0, use_cache=True):

    capacity = panel_watts / 1000.0

    url = "https://developer.nrel.gov/api/pvwatts/v5.json?api_key=%s&address=%s&system_capacity=%f&azimuth=180&tilt=%f&array_type=0&module_type=0&losses=%f&timeframe=hourly" % (key, address, capacity, tilt, losses)

    r = requests.get(url) 

    nrel_data = r.json()['outputs']

    dates = np.load(fpath + "/data/dates.npy")
    n = dates.shape[0]
    data = np.zeros((n, 11))

    data[:, 0:3] = dates
    data[:, 3] = nrel_data['dn']
    data[:, 4] = nrel_data['df']
    data[:, 5] = nrel_data['tamb']
    data[:, 6] = nrel_data['wspd']
    data[:, 7] = nrel_data['poa']
    data[:, 8] = nrel_data['tcell']
    data[:, 9] = nrel_data['dc']
    data[:, 10] = nrel_data['ac']

    return data

def get_data(files):
    """Parses data from multiple files, and concatenates them"""
    data = []
    for fn in files:
        data += parse_data(fn).tolist()
    return np.array(data)

def parse_data(fn):
    """
    NREL csv data parser
    """
    data = []
    with open(fn, "rb") as f:
        for line in f:
            if py_ver == 3:
                # Python 3 code in this block
                dline = "".join(filter(lambda char: char != '"', line.decode())).split(",")
            else:
                # Python 2 code in this block
                dline = line.translate(None, '"').split(",")
            
            if len(dline) == 11 and dline[0].isdigit():
                data.append([float(i) for i in dline])

    return np.array(data)