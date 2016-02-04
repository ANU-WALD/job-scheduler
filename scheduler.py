#!/usr/bin/env python
"""
Schedules all other jobs to run, with dependancies.

Reschedules itself to run a minute past midnight tomorrow.

Notes:
  - the 'afterany' arg to qsub means "after all jobs complete with any status"
"""
#pylint:disable=invalid-name
from __future__ import division, print_function, unicode_literals

import datetime
import subprocess
import time


def schedule(jobfile, after_ids=None):
    """Schedule a job, with dependancies and log files."""
    logfile = '/g/data/xc0/user/HatfieldDodds/logs/{}_{}'.format(
        jobfile, datetime.date.today().isoformat())
    args = ['qsub',
            '-o', logfile + '.stdout',
            '-e', logfile + '.stderr',
            '-W', 'umask=017']
    if after_ids is not None:
        if not isinstance(after_ids, list):
            after_ids = [after_ids]
        args[-1] += ',depend=afterany:' + ':'.join([a.split('.')[0] for a in after_ids])
    args.append('./' + jobfile)
    print('Scheduling:  ' + ' '.join(args))
    return subprocess.check_output(args)

#Queue TIGGE, get job id
input_data_job_list = [schedule('getTigge.qsub')]

#If it is time for an ERA-Int check, do this as well
if datetime.date.today().day == 1:
    input_data_job_list.append(schedule('getEraInt.qsub'))

#Queue the APWM
apwm_job_id = schedule('apwm.qsub', input_data_job_list)

#Queue the map plot & transfer
maps_job_id = schedule('plotmap.qsub', apwm_job_id)

#Queue the published data appending
schedule('upload.qsub', maps_job_id)

#Reporting ideas
    #Create a JSON report
    #Upload to wenfo

# Finally, wait a minute so we're after scheduled time and reschedule.
time.sleep(60)

print('Finished all at ' + datetime.datetime.now().isoformat() + ', rescheduling...')
# scheduler.qsub reschedules itself.
