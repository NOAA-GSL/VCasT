#!/usr/bin/env python
"""
-----------------------------------------------------------------------
 Description:  Submit a vcast job via SLURM.
                              
 Assumptions:  For use on Hera or similar HPC systems.
               This script submits a job via SLURM and assumes that the vcast
               command is available in the activated environment.
               
 Usage: ./slurm-job.py   # Run from the working directory
-----------------------------------------------------------------------
"""

import os
from subprocess import Popen, PIPE

def submit_job(config_file):
    """
    Submit a SLURM job that runs the vcast command with the given configuration file.
    
    Parameters:
      config_file (Path): Path to the configuration file.
    """
    USER = os.getenv('USER')
    MY_EMAIL = f"{USER}@noaa.gov"
    ACCOUNT = "fv3lam"
    WALLTIME = "05:00:00"
    PROCESSORS = "4"
    QUEUE = "batch"
    MEMORY = "300GB"
    WORKING_DIR = os.path.dirname(os.path.abspath(__file__))
    VENV_ACTIVATE = "source /path/to/venv/bin/activate"    
    # Create a unique job name based on the parameters.
    JOB_NAME = f"vcast_job"
    VCAST_COMMAND = f"vcast {config_file}"

    JOB_STRING = f"""#!/bin/bash
#SBATCH -J {JOB_NAME}
#SBATCH -A {ACCOUNT}
#SBATCH --time={WALLTIME}
#SBATCH -n {PROCESSORS}
#SBATCH -o ./{JOB_NAME}.out
#SBATCH -q {QUEUE}
#SBATCH --mail-user={MY_EMAIL}
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mem={MEMORY}
#SBATCH -D {WORKING_DIR}

# Activate the Python environment
{VENV_ACTIVATE}

# Run the vcast command with configuration file {config_file}
{VCAST_COMMAND}
"""
    proc = Popen('sbatch', shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
    out, err = proc.communicate(JOB_STRING.encode())
    print(f"Submitting SLURM job for {config_file}")
    print(JOB_STRING)
    print("SLURM Response:")
    print(out.decode())
    print(err.decode())

if __name__ == "__main__":

    config_file = "config.yaml"    
    
    submit_job(config_file)

