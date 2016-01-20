#!/usr/bin/env python
from ecmwfapi import ECMWFDataServer 
from ecmwfapi.api import APIException
import datetime 
import calendar 
import os

# Parameters for the fetch.
params = ["169.128", "201.128", "202.128", "228.128"]
short_names = ["rad", "tmax", "tmin", "precip"]

startDate = datetime.date.today() - datetime.timedelta(200) #90 days
endDate = datetime.date.today()

print "Starting at: " + str(startDate) 
print "Ending: at " + str(endDate)

# Server parameters - now found in $HOME/.ecmwfapi
server = ECMWFDataServer()
# Timestep is daily
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
#    if (not os.path.isdir('{0:%Y}'.format(date))):
#        print("Make dir <{0:%Y}>".format(date))
#        os.makedirs('{0:%Y}'.format(date))

    for param, short_name in zip(params, short_names):
        #Filenames in the format:
        #<prodname>-eraint-<YYYYMMDD>.nc
        #   "precip-eraint-20140101.nc"
#        target = "{date:%Y}/{shortname}-eraint-{date:%Y%m%d}.nc".format(
#            date=date, 
#            shortname=short_name)
        target = "ecmwf."+str(date)+"."+param+".grib"
        print ("Fetching date {}, param {} to {}.").format(
            getDate, param, target)
        if (os.path.exists(target) and os.path.getsize(target) == 0):
            print("Removing empty file -- " + target + " and trying again.")
            os.remove(target)
        if (not os.path.exists(target)):
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
            except APIException, e:
                print str(e)
            if (os.path.exists(target) and os.path.getsize(target) == 0):
                os.remove(target)
        else:
            print("Skipping -- " + target + " already exists.")
    # Move to next time step.
    date = (date + datetime.timedelta(days=timeStep))

