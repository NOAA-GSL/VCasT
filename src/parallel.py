from multiprocessing import Pool
from functools import partial
from datetime import timedelta
from src.interpolation import *
from src.stats import *
from src.ioc import *

def process_date_multiprocessing(date, fcst_file, ref_file, fcst_var, ref_var, target_grid, stat_name):
    """
    Function to process a single date entry. This will be executed in parallel using multiprocessing.
    """
    try:
        # Read forecast and reference data
        fcst_data, flats, flons, ftype = read_input_data(fcst_file, fcst_var)
        ref_data, rlats, rlons, rtype = read_input_data(ref_file, ref_var)

        # Adjust longitudes if needed
        if 'grib2' in rtype:
            rlons += 360.
        if 'grib2' in ftype:
            flons += 360.

        # Interpolate to target grid
        if 'fcst' in target_grid:
            interpolated_data = interpolate_to_target_grid(ref_data, rlats, rlons, flats, flons)
        else:
            raise Exception("Error: target_grid is unknown.")

        # Compute statistics
        stats = []
        for stat in [s.upper() for s in stat_name]:
            if 'RMSE' in stat:
                result = compute_rmse(fcst_data, interpolated_data)
            elif 'BIAS' in stat:
                result = compute_bias(fcst_data, interpolated_data)
            else:
                result = "NA"
                print(f"{stat} not found.")
            stats.append(result)

        # Format the result as a string
        row_string = f"{date};" + ";".join([str(f) for f in stats])
        return row_string
    except Exception as e:
        return f"Error processing {date}: {e}"

def process_in_parallel(dates, fcst_files, ref_files, config):
    """
    Process all dates in parallel using multiprocessing.
    """
    fcst_var = config.fcst_var
    ref_var = config.ref_var
    target_grid = config.target_grid
    stat_name = config.stat_name

    # Use a Pool for parallel processing
    with Pool(processes=5) as pool:  # Adjust number of processes to match your system capacity
        # Use partial to pass constant arguments to the worker function
        worker_function = partial(
            process_date_multiprocessing,
            fcst_var=fcst_var,
            ref_var=ref_var,
            target_grid=target_grid,
            stat_name=stat_name
        )

        # Map input data to the worker function
        results = pool.starmap(worker_function, zip(dates, fcst_files, ref_files))

    for row in results:
        config.write_to_output_file(row)

def dates_to_list(start_date_object, end_date_object,interval_hours):
    dates = []
    current_datetime = start_date_object
    while current_datetime <= end_date_object:
        dates.append(current_datetime)
        current_datetime += timedelta(hours=interval_hours)
    
    return dates

def files_to_list(fcst_file_template, ref_file_template, dates):
    ffiles = []
    rfiles = []
    for current_datetime in dates:
        cycle = current_datetime.hour - current_datetime.hour%6
        fcst_file = format_file_template(fcst_file_template, current_datetime, cycle)
        ref_file = format_file_template(ref_file_template, current_datetime, cycle)

        ffiles.append(fcst_file)
        rfiles.append(ref_file)
    
    return ffiles, rfiles