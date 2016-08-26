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


# JOBS maps each job to a list of jobs to complete first
# Most jobs run unconditionally on a daily schedule
JOBS = {
    'getTigge.qsub': [],
    'apwm.qsub': ['getTigge.qsub', 'getEraInt.qsub'],
    'upload.qsub': ['apwm.qsub'],
    }

# download ERA-Interim data on the first of the month only
if 1 or datetime.date.today().day == 1:
    JOBS['getEraInt.qsub'] = []

# scheduler.qsub is this script; runs after the midnight after all other jobs
    JOBS['scheduler.qsub'] = list(JOBS)



def schedule(jobfile, after_ids=None):
    """Schedule a job, with dependencies and log files."""
    logfile = '/g/data/xc0/user/HatfieldDodds/logs/{}_{}'.format(
        jobfile, datetime.date.today().isoformat())
    args = ['qsub',
            '-o', logfile + '.stdout',
            '-e', logfile + '.stderr',
            '-l', 'other=gdata1',
            '-P', 'xc0',
            '-W', 'umask=017']
    if after_ids:
        args[-1] += ',depend=afterany:' + ':'.join(after_ids)
    args.append('./' + jobfile)
    print('Scheduling:  ' + ' '.join(args))
    return subprocess.check_output(args).split('.')[0]


def do_schedule():
    """The main function."""
    def sub_order(job):
        """Sorting key for job submission based on depth of dependency tree."""
        after = JOBS.get(job)
        return 1 + max(sub_order(j) for j in after) if after else 0

    queue = sorted(JOBS, key=sub_order)
    job_ids = {}
    for job in queue:
        after = [job_ids[j] for j in JOBS[job] if j in JOBS]
        job_ids[job] = schedule(job, after)
    print('Finished all at ' + datetime.datetime.now().isoformat())


if __name__ == '__main__':
    do_schedule()
