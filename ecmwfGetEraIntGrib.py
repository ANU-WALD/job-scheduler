#!/usr/bin/env python
from __future__ import print_function

import datetime
import os

# python bindings for their API
import ecmwfapi

# Parameters for the fetch.
params = ["169.128", "201.128", "202.128", "228.128"]
short_names = ["rad", "tmax", "tmin", "precip"]

startDate = datetime.date.today() - datetime.timedelta(200) #90 days
endDate = datetime.date.today()

print("Starting at: " + str(startDate))
print("Ending: at " + str(endDate))

# Server parameters - now found in $HOME/.ecmwfapirc
server = ecmwfapi.ECMWFDataServer()
# Timestep is daily
timeStep = 1

# Loop through dates by month.
date = startDate
while date <= endDate:
    getDate = str(date)
    for param, short_name in zip(params, short_names):
        #Filenames in the format:
        #<prodname>-eraint-<YYYYMMDD>.nc
        #   "precip-eraint-20140101.nc"
        target = "ecmwf."+str(date)+"."+param+".grib"
        print("Fetching date {}, param {} to {}.".format(
            getDate, param, target))
        if os.path.exists(target) and not os.path.getsize(target):
            print("Removing empty file -- " + target + " and trying again.")
            os.remove(target)
        if not os.path.exists(target):
            try:
                server.retrieve({
                    'grid' : "1.5/1.5",
                    'time' : "00:00:00/12:00:00",
                    'date' : getDate,
                    'stream' : "oper",
                    'dataset' : "interim",
                    'step' : "12",
                    'levtype' : "sfc",
                    'type' : "fc",
                    'class' : "ei",
                    'param' : param,
                    'target' : target
                    })
            except Exception, e:
                print(str(e))
            if os.path.exists(target) and not os.path.getsize(target):
                os.remove(target)
        else:
            print("Skipping -- " + target + " already exists.")
    # Move to next time step.
    date = date + datetime.timedelta(days=timeStep)

