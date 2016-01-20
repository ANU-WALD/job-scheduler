#!/usr/bin/env python
#PBS -q normal
#PBS -l walltime=05:00
#PBS -l mem=50MB
#PBS -l ncpus=1
#PBS -a 0001
#PBS -o scheduler.output.log
#PBS -e scheduler.error.log

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

base_dir = '/g/data/xc0/projects/apwm'

#Queue TIGGE, get job id
tigge_job_id = subprocess.check_output(['qsub', 'ECMWF/tigge/getTiggeGribNow.qsub'])

input_data_job_list = [tigge_job_id]

#If it is time for an ERA-Int check, do this as well
day_of_month = date.today().day
if day_of_month == 1:
    eraint_job_id = subprocess.check_output(['qsub', 'ECMWF/eraint/getEraIntNow.qsub'])
    input_data_job_list.append(eraint_job_id)    

#Queue the APWM
depend_arg = 'depend=afterany:'+':'.join(input_data_job_list)
apwm_job_id = subprocess.check_output(['qsub', 'scripts3/apwm_run_only.qsub', '-W', depend_arg])

#Queue the map plot & transfer
depend_arg = 'depend=afterany:{}'.format(apwm_job_id)
map_plot_job_id = subprocess.check_output(['qsub', 'pythonmaps/runmap.qsub', '-W', depend_arg])

#Queue the published data appending


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

# Finally, wait a two minutes so we're after scheduled time and reschedule.
time.sleep(120)
subprocess.check_output(['qsub', 'scheduler.qsub.py'])datetime.datetime.now().isoformat()

print('Finished rescheduling all at ' + datetime.datetime.now().isoformat()


