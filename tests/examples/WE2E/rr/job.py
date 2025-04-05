#!/usr/bin/env python
"""
-----------------------------------------------------------------------
 Description:  Create configuration files and submit multiple vcast jobs
               via SLURM. This script creates configuration files for each
               combination of parameters:
                 - job_time: 1,2,3,4,5,6
                 - var_threshold: 20, 30, 40
                 - var_radius: 1, 5, 9, 15
               Then, it submits a job for each config file.
               
 Assumptions:  For use on Hera or similar HPC systems.
               This script submits jobs via SLURM and assumes that the vcast
               command is available in the activated environment.
               
 Usage: ./submit_vcast_jobs.py   # Run from the working directory
-----------------------------------------------------------------------
"""

import os
import time
from pathlib import Path
from subprocess import Popen, PIPE

def create_config_file(file_path, job_time, var_threshold, var_radius):
    """
    Write a YAML configuration file with the desired settings.
    
    Parameters:
      file_path (Path): Path to the configuration file.
      job_time (int): An integer (1 to 6) representing the job time setting.
      var_threshold (int): Threshold value for analysis (e.g., 20, 30, 40).
      var_radius (int): Influence radius for calculations (e.g., 1, 5, 9, 15 grid points).
    """
    rr = job_time - 1
    config_content = f"""\
# Date and Time Settings
start_date: "2024-04-01_02:00:00"  # Start date of the data processing
end_date: "2024-04-30_00:00:00"      # End date of the data processing
interval_hours: "1"                # Interval for processing (e.g., hourly, 6-hourly)
job_time: {rr}              # Custom job time setting

# Forecast Configuration
fcst_file_template: "/scratch1/BMC/hmtb/Daniel.Abdi/forecasts-graphhrrr/graphhrrr_predictions.zarr"
fcst_var: "REFC"                   # Forecast variable name
fcst_level: 2
fcst_type_of_level: "heightAboveGround"
shift: 0                          # Time shift (if any)

# Reference Configuration
ref_file_template: "/scratch1/BMC/hmtb/Daniel.Abdi/forecasts-graphhrrr/graphhrrr_targets.zarr"
ref_var: "REFC"
ref_level: 2
ref_type_of_level: "heightAboveGround"

# Output Configuration
output_dir: "."                   # Directory to save outputs
output_filename: "fss-REFC_{var_threshold}dbz_{var_radius}r_{job_time}h.data"  # Output file template

# Statistical Metrics
stat_name:
  - "rmse"
  - "bias"
  - "fss"

threshold: 20

# Variable Threshold and Radius
var_threshold: {var_threshold}    # Threshold value for analysis
var_radius: {var_radius}          # Influence radius for calculations (grid points)

# Grid and Interpolation Settings
interpolation: true               # Whether to interpolate data
target_grid: "/scratch1/BMC/hmtb/Daniel.Abdi/forecasts-graphhrrr/graphhrrr_predictions.zarr"

# Parallel Processing
processes: 1                      # Number of processes to run in parallel
"""
    print(config_content)
    with open(file_path, "w") as f:
        f.write(config_content)

def submit_job(config_file, job_time, var_threshold, var_radius):
    """
    Submit a SLURM job that runs the vcast command with the given configuration file.
    
    Parameters:
      config_file (Path): Path to the configuration file.
      job_time (int): The job_time value for this job.
      var_threshold (int): The var_threshold value for this job.
      var_radius (int): The var_radius value for this job.
    """
    USER = os.getenv('USER')
    MY_EMAIL = f"{USER}@noaa.gov"
    ACCOUNT = "fv3lam"
    WALLTIME = "05:00:00"
    PROCESSORS = "4"
    QUEUE = "batch"
    MEMORY = "1GB"
    WORKING_DIR = os.path.dirname(os.path.abspath(__file__))
    VENV_ACTIVATE = "source /scratch2/BMC/fv3lam/Vanderlei.Vargas/verification_AIML/hands-on/venv/bin/activate"
    PYTHONPATH_EXPORT = 'export PYTHONPATH="/scratch2/BMC/fv3lam/Vanderlei.Vargas/verification_AIML/hands-on/VCasT"'
    # Create a unique job name based on the parameters.
    JOB_NAME = f"vcast_job_{job_time}_{var_threshold}_{var_radius}"
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
{PYTHONPATH_EXPORT}

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
    # Define parameter lists.
    times = [1]
    var_thresholds = [20]
    var_radii = [1]
    
    # Directory where configuration files will be created.
    config_dir = Path("/scratch2/BMC/fv3lam/Vanderlei.Vargas/verification_AIML/hands-on/NEW_DEV/graphHRRR")
    config_dir.mkdir(parents=True, exist_ok=True)

    # Loop over all combinations and create/submit jobs.
    for t in times:
        for vt in var_thresholds:
            for vr in var_radii:
                # Create a unique filename for each combination.
                config_filename = f"zarr_{t}_{vt}_{vr}.yaml"
                config_file = config_dir / config_filename
                # Create the configuration file.
                create_config_file(config_file, job_time=t, var_threshold=vt, var_radius=vr)
                time.sleep(0.1)  # Brief pause after file creation.
                # Submit a job for this configuration file.
                submit_job(config_file, job_time=t, var_threshold=vt, var_radius=vr)

