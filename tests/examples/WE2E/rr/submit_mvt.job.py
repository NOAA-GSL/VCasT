#!/usr/bin/env python
"""
-----------------------------------------------------------------------
 Description:  Example script to submit a job to run the MVT command
               using the HPC batch system.

 Assumptions:  For use on Hera or similar HPC systems.
               This script submits jobs via SLURM and assumes the MVT
               package is installed in a suitable environment.

 COMMAND line arguments: none

 Usage: ./submit_mvt_job.py   # Run from the working directory
-----------------------------------------------------------------------
"""

from subprocess import Popen, PIPE
import os
import time

# User information
USER = os.getenv('USER')
STRINGS = [USER, 'noaa.gov']
MY_EMAIL = '@'.join(STRINGS)

# Define the MVT configuration file and command
CONFIG_FILE = "/scratch2/BMC/fv3lam/Vanderlei.Vargas/verification_AIML/hands-on/VCasT/tests/examples/WE2E/rr/t2m.yaml"
VCAST_COMMAND = f"vcast {CONFIG_FILE}"

# SLURM job settings
PROC = Popen('sbatch', shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)

### User-editable section ###
JOB_NAME = "vcast_job"
ACCOUNT = "fv3lam"
WALLTIME = "05:00:00"
PROCESSORS = "8"
QUEUE = "batch"
MEMORY = "300GB"
EMAIL_ADDR = MY_EMAIL
EMAIL_OCCASION = "BEGIN,END,FAIL"
WORKING_DIR = os.path.dirname(os.path.abspath(__file__))
### End User-editable section ###

# SLURM batch script as a string
JOB_STRING = f"""#!/bin/bash
#SBATCH -J {JOB_NAME}
#SBATCH -A {ACCOUNT}
#SBATCH --time={WALLTIME}
#SBATCH -n {PROCESSORS}
#SBATCH -o ./{JOB_NAME}.out
#SBATCH -q {QUEUE}
#SBATCH --mail-user={EMAIL_ADDR}
#SBATCH --mail-type={EMAIL_OCCASION}
#SBATCH --mem={MEMORY}
#SBATCH -D {WORKING_DIR}

# Activate the Python environment
source /scratch2/BMC/fv3lam/Vanderlei.Vargas/verification_AIML/hands-on/venv/bin/activate
export PYTHONPATH="/scratch2/BMC/fv3lam/Vanderlei.Vargas/verification_AIML/hands-on/VCasT"

# Run the MVT command
{VCAST_COMMAND}
"""

# Submit the job
PROC.stdin.write(JOB_STRING.encode())
OUT, ERR = PROC.communicate()

# Print the job details and the system response
print("Submitting SLURM job with the following script:")
print(JOB_STRING)
print("SLURM Response:")
print(OUT.decode())
print(ERR.decode())

time.sleep(0.1)

PROC.stdin.close()

