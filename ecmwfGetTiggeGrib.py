#!/usr/bin/env python
import datetime 
import calendar 
import os
import tempfile

from ecmwfapi import ECMWFDataServer 
from ecmwfapi.api import APIException

# Parameters for the fetch.
params = [ "176", "121", "122","228228"]
short_names = ["NETrad", "tmax", "tmin", "precip"]

#startDate = datetime.date(2011, 11, 01)
startDate = datetime.date.today() - datetime.timedelta(120) #days
endDate = datetime.date.today() - datetime.timedelta(1) #days - ECWMF has a 2-day embargo

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
    #if (not os.path.isdir('{0:%Y}'.format(date))):
    #    print("Make dir <{0:%Y}>".format(date))
    #    os.makedirs('{0:%Y}'.format(date))

    for param, short_name in zip(params, short_names):

        target = "ecmwf.{date:%Y-%m-%d}.{param}.grib".format(date=date, param=param)
        #target = "{date:%Y}/{shortname}-ecmwfc-{date:%Y%m%d}.nc".format(date=date, shortname=short_name)

        print ("Fetching date " + getDate + ", param " + param +
               " to " + target)

        if (os.path.exists(target) and os.path.getsize(target) == 0):
            print("Removing empty file -- " + target + " and trying again.")
            os.remove(target)

        if (not os.path.exists(target)):
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
                    'target'  : target
                    })
            except APIException, e:
                print 'APIException:', str(e)
            if (os.path.exists(target) and os.path.getsize(target) == 0):
                os.remove(target)
        else:
            print("Skipping -- " + target + " already exists.")

    # Move to next time step.
    date = (date + datetime.timedelta(days=timeStep))

