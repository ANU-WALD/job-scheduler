#!/usr/bin/env python
"""
Schedules all other jobs to run, with dependancies.

Reschedules itself to run a minute past midnight tomorrow.

Notes:
  - the 'afterany' arg to qsub means "after all jobs complete with any status"
"""
from __future__ import division, print_function, unicode_literals

from datetime import date
import subprocess
import time


def schedule(jobfile, after_ids=None):
    """Schedule a job, with dependancies and log files."""
    args = ['qsub', jobfile,
            '-o', 'logs/'+jobfile+'.stdout',
            '-e', 'logs/'+jobfile+'.stderr']
    if after_id is not None:
        if not isinstance(after_ids, list):
            after_ids = [after_ids]
        args.extend(['-W', 'depend=afterany:'+':'.join(after_ids)])
    return subprocess.check_output(args)

#Queue TIGGE, get job id
input_data_job_list = [schedule('getTigge.qsub')]

#If it is time for an ERA-Int check, do this as well
day_of_month = date.today().day
if day_of_month == 1:
    input_data_job_list.append(schedule('getEraInt.qsub'))    

#Queue the APWM
apwm_job_id = schedule('apwm.qsub', input_data_job_list)

#Queue the map plot & transfer
maps_job_id = schedule('plotmap.qsub', apwm_job_id)

#Queue the published data appending
schedule('upload.qsub', maps_job_id)

'''
#Run MODSI 8-day tasks
# TODO - check if we want this, update paths etc.
day_number = date.today().toOrdinal()
eight_day_number = day_number % 8

if eight_day_number == 0:
    subprocess.check_output(['qsub', 'getMCD15A2.qsub'])
elif eight_day_number == 1:
    subprocess.check_output(['qsub', 'getMCD43A4.qsub'])
elif eight_day_number == 2:
    subprocess.check_output(['qsub', 'getMOD09A1.qsub'])
elif eight_day_number == 3:
    subprocess.check_output(['qsub', 'getMOD15A2.qsub'])
'''
#Reporting ideas
    #Create a JSON report
    #Upload to wenfo

# Finally, wait a minute so we're after scheduled time and reschedule.
time.sleep(60)

print('Finished all at ' + datetime.datetime.now().isoformat() + ', rescheduling...')
# scheduler.qsub reschedules itself.


