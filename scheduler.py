#!/usr/bin/env python
"""
Schedules all other jobs to run, with dependancies.

Reschedules itself to run a minute past midnight tomorrow.
"""

import datetime
import os
import subprocess


# JOBS maps each job to a list of jobs to complete first
# Most jobs run unconditionally on a daily schedule
JOBS = {
    'getTigge.qsub': [],
    'apwm.qsub': ['getTigge.qsub', 'getEraInt.qsub'],
    'upload.qsub': ['apwm.qsub'],
    }

# download ERA-Interim data on the first of the month only
if datetime.date.today().day == 1:
    JOBS['getEraInt.qsub'] = []


def schedule(jobfile, after_ids=None):
    """Schedule a job, with dependencies and log files."""
    logfile = '/g/data/xc0/user/HatfieldDodds/logs/{}_{}'.format(
        datetime.date.today().isoformat(), jobfile.rstrip('.qsub'))
    args = ['qsub',
            '-o', logfile + '.out',
            '-e', logfile + '.err',
            '-l', 'other=gdata1',
            '-P', 'xc0',
            # On error or abort, mail a report to $USER and Albert Van Dijk
            '-M', os.environ['USER'] + ',albert.vandijk@anu.edu.au',
            '-W', 'umask=017']
    if after_ids:
        # 'afterany' means "after all jobs complete with any status"
        args[-1] += ',depend=afterany:' + ':'.join(after_ids)
    args.append('./' + jobfile)
    print('Scheduling:  ' + ' '.join(args))
    output = subprocess.check_output(args)
    if isinstance(output, bytes):
        output = output.decode()
    return output.split('.')[0]


def do_schedule():
    """The main function."""
    def sub_order(job):
        """Sorting key for job submission based on depth of dependency tree."""
        after = JOBS.get(job, [])
        return 1 + max([sub_order(j) for j in after] + [0])

    job_ids = dict()
    for job in sorted(JOBS, key=sub_order):
        after = [job_ids[j] for j in JOBS[job] if j in JOBS]
        job_ids[job] = schedule(job, after)

    # schedule the scheduler after midnight and all other jobs have finished
    schedule('scheduler.qsub', list(job_ids.values()))
    print('Finished all at ' + datetime.datetime.now().isoformat())


if __name__ == '__main__':
    do_schedule()
