#!/bin/bash

# Define the base directory
BASE_DIR="/scratch2/BMC/fv3lam/HIWT/expt_dirs"

# Define the experiment prefix
EXPT_PREFIX="RRFS_GDAS_GF.SPP.SPPT_20220501-06"

# Define the range of dates (from 2022050100 to 2022050600)
for DATE in {2022050100..2022050600..100}; do
    # Loop over members mem01 to mem06
    for MEMBER in mem{01..10}; do
        # Define the path to the stats directory
        STAT_DIR="${BASE_DIR}/${EXPT_PREFIX}/${DATE}/${MEMBER}/metprd/grid_stat_cmn"
        
        # Define the output file name
        OUTPUT_FILE="${DATE}_${MEMBER}.stat"
        
        # Check if the directory exists before proceeding
        if [ -d "$STAT_DIR" ]; then
            # Concatenate all stat files into one output file
            cat ${STAT_DIR}/*stat > ${OUTPUT_FILE}
            echo "Created ${OUTPUT_FILE} from ${STAT_DIR}"
        else
            echo "Warning: Directory ${STAT_DIR} does not exist, skipping..."
        fi
    done
done

