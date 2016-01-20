#!/usr/bin/env python
import datetime 
import calendar 
import os
import tempfile

from ecmwfapi import ECMWFDataServer 
from ecmwfapi.api import APIException

import flatten_netcdf

# Parameters for the fetch.
params = ["121", "122", "176", "228228"]
short_names = ["NETrad", "tmax", "tmin", "precip"]

# startDate = datetime.date(2011, 11, 01)
startDate = datetime.date.today() - datetime.timedelta(90) #90 days
endDate = datetime.date.today() - datetime.timedelta(2) #2-day embargo on forecasts

print "Starting at: " + str(startDate)
print "Ending: at " + str(endDate)

# Server parameters - now found in $HOME/.ecmwfapi
server = ECMWFDataServer()

# By default, time step is daily.
timeStep = 1

# Loop through dates by month.
date = startDate
while(date <= endDate):

    # Code for monthly timestep (uncomment if required).
    #daysInMonth = calendar.monthrange(date.year, date.month)[1]
    #timeStep = daysInMonth
    #getDate = str(date) + "/to/" + str(date.replace(day=daysInMonth))

    # Code for daily timestep.
    getDate = str(date)
    if (not os.path.isdir('{0:%Y}'.format(date))):
        print("Make dir <{0:%Y}>".format(date))
        os.makedirs('{0:%Y}'.format(date))

    for param, short_name in zip(params, short_names):

        #target = str(date.year) + "/" + short_name + "-ecmwf-"+str(date)+".nc"
        target = "{date:%Y}/{shortname}-ecmwfc-{date:%Y%m%d}.nc".format(date=date, shortname=short_name)

        print ("Fetching date " + getDate + ", param " + param +
               " to " + target)

        if (os.path.exists(target) and os.path.getsize(target) == 0):
            print("Removing empty file -- " + target + " and trying again.")
            os.remove(target)

        if (not os.path.exists(target)):
            t_file = tempfile.NamedTemporaryFile(delete=False)
            temp_target = t_file.name
            t_file.close()
            try:
                server.retrieve({
                    'dataset' : "tigge",
                    'expver'  : "prod",
                    'grid'    : "1.5/1.5",
                    'time'    : "00:00:00/12:00:00",
                    'date'    : getDate,
                    'step'    : "12",
                    'origin'  : "ecmf",
                    'levtype' : "sfc",
                    'type'    : "cf",
                    'param'   : param,
                    'target'  : temp_target,
                    'format'  : "netcdf"
                    })
            except APIException, e:
                print 'APIException:', str(e)
            #Flatten file
            try:
                flatten_netcdf.flatten_netcdf(temp_target, target, shortname)
            except:
                pass
            os.remove(temp_target)
            if (os.path.exists(target) and os.path.getsize(target) == 0):
                os.remove(target)
        else:
            print("Skipping -- " + target + " already exists.")

    # Move to next time step.
    date = (date + datetime.timedelta(days=timeStep))

