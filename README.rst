############
APWM Scripts
############

A collection of high-level scripts to manage data fetching and analysis
jobs on the National Conputational Infrastructure for the ANU Water and
Landscape Dnyamics Group (WALD, NCI group xc0).

They use the ``qsub`` job scheduler, and recurrence is acheived by having
the top-level job reschedule itself for the next day.


scheduler.py
============
This is the top-level job, and is the only script that needs to be run
manually - and that only if something goes wrong.

The tasks it schedules can be summarised as:

1. collect input data; Tigge and (monthly) ERA-int datasets
2. run the APWM model
3. run the python-map-maker
4. upload results
5. housekeeping (to be implemented)


Design Principles
=================
(TODO: bring implementation up to described standard)

* Each task should be run from a bash script with a ``.qsub`` file extension,
  which lists the job resource requirements (queue, RAM, CPU, walltime, etc).

* Complex tasks may simply delegate to an external script, though for simple
  ones I prefer to just put it in the .qsub file for simplicity.

* Tasks may schedule a followup task (eg an analysis script may schedule
  a data transfer task), but ONLY the top-level task may reschedule itself.

* Prefer to use qsub features over complex scripting.  It is easier to read
  or modify a top-level script with conditional scheduling, than long
  chains of scripts which schedule each other.

* Comments in each script should be detailed enough to serve as documentation
  for that task.

* Anyone using or modifying this system is assumed to have at least skimmed
  ``man qsub``.


Requirements to run
===================
This list is probably incomplete, but hopefully useful anyway.

- member of the matlab_anu group (to run model)
- read/write access to ``/short/user/adh157`` on Raijin
- ECMWF access key in ``~/.ecmwfapirc`` (see https://software.ecmwf.int/wiki/display/WEBAPI)
- A clone of this repo in your home dir on raijin

