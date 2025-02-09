from multiprocessing import Pool
from functools import partial
from datetime import timedelta
from vcast.interpolation import *
from vcast.stats import *
from vcast.ioc import *

def process_date_multiprocessing(date, fcst_file, ref_file, fcst_var, ref_var, interpolation, target_grid, stat_name, 
                                 var_threshold, radius, fcst_type_of_level, fcst_level, ref_type_of_level, ref_level):
    """
    Function to process a single date entry. This will be executed in parallel using multiprocessing.
    """
    try:
        # Read forecast and reference data
        fcst_data, flats, flons, ftype = read_input_data(fcst_file, fcst_var, fcst_type_of_level, fcst_level)
        ref_data, rlats, rlons, rtype = read_input_data(ref_file, ref_var, ref_type_of_level, ref_level)

        # Adjust longitudes if needed
        if 'grib2' in rtype:
            rlons += 360.
        if 'grib2' in ftype:
            flons += 360.

        # Interpolate to target grid
        
        if interpolation:            
            if 'fcst' in target_grid:
                interpolated_data = interpolate_to_target_grid(ref_data, rlats, rlons, flats, flons) 
            else:
                raise Exception("Error: target_grid is unknown.")
        else:
            interpolated_data = ref_data

        # Compute statistics
        stats = [date]
 
        ustat_name = [s.lower() for s in stat_name]

        if "gss" in ustat_name or "fbias" in ustat_name or "pod" in ustat_name or "far" in ustat_name or "csi" in ustat_name or "sr" in ustat_name:
            # Compute scores if any of these metrics are requested
            hits, misses, false_alarms, correct_rejections, total_events = compute_scores(fcst_data, interpolated_data, var_threshold, radius)

        if 'rmse' in ustat_name:
            stats += [compute_rmse(fcst_data, interpolated_data)]
        if 'bias' in ustat_name:
            stats += [compute_bias(fcst_data, interpolated_data)]
        if 'quantiles' in ustat_name:
            stats += compute_quantiles(fcst_data, interpolated_data)
        if "mae" in ustat_name:
            stats += [compute_mae(fcst_data, interpolated_data)]
        if "corr" in ustat_name:
            stats += [compute_correlation(fcst_data, interpolated_data)]
        if "stdev" in ustat_name:
            stats += [compute_stdev(fcst_data, interpolated_data)]
        if "gss" in ustat_name:
            stats += [compute_gss(hits, misses, false_alarms, total_events)]
        if "fbias" in ustat_name:
            stats += [calculate_fbias(hits, false_alarms, misses)]
        if "pod" in ustat_name:
            stats += [compute_pod(hits, misses)]
        if "far" in ustat_name:
            stats += [compute_far(hits, false_alarms)]
        if "csi" in ustat_name:
            stats += [compute_csi(hits, misses, false_alarms)]
        if "sr" in ustat_name:
            stats += [compute_success_ratio(hits, false_alarms)]
        if "fss" in ustat_name:
            stats += [compute_fss(fcst_data, interpolated_data, var_threshold, radius)]
   
        return stats
    
    except Exception as e:
        raise Exception(f"Error processing {date}: {e}")

def process_in_parallel(dates, fcst_files, ref_files, config, output):
    """
    Process all dates in parallel using multiprocessing.
    """
    fcst_var = config.fcst_var
    ref_var = config.ref_var
    interpolation = config.interpolation
    target_grid = config.target_grid
    stat_name = config.stat_name
    var_threshold = config.var_threshold
    radius = config.var_radius
    fcst_type_of_level = config.fcst_type_of_level 
    fcst_level = config.fcst_level 
    ref_type_of_level = config.ref_type_of_level
    ref_level = config.ref_level

    # Use a Pool for parallel processing
    with Pool(processes=config.processes) as pool:  # Adjust number of processes to match your system capacity
        # Use partial to pass constant arguments to the worker function
        worker_function = partial(
            process_date_multiprocessing,
            fcst_var=fcst_var,
            ref_var=ref_var,
            interpolation=interpolation,
            target_grid=target_grid,
            stat_name=stat_name,
            var_threshold = var_threshold,
            radius = radius,
            fcst_type_of_level = fcst_type_of_level, 
            fcst_level = fcst_level, 
            ref_type_of_level = ref_type_of_level, 
            ref_level = ref_level
        )

        # Map input data to the worker function
        results = pool.starmap(worker_function, zip(dates, fcst_files, ref_files))

    for row in results:
        output.write_to_output_file(row)

def dates_to_list(start_date, end_date, interval_hours, date_format="%Y-%m-%d_%H:%M:%S"):
    """
    Converts start_date and end_date strings into datetime objects and generates a list 
    of datetime objects at the specified interval.

    Args:
        start_date (str or datetime): Start date in string or datetime format.
        end_date (str or datetime): End date in string or datetime format.
        interval_hours (int or str): Interval in hours (can be int or string).
        date_format (str): Format of the input date strings (default: "%Y-%m-%d_%H:%M:%S").

    Returns:
        list: List of datetime objects at the specified interval.
    """
    # Convert string dates to datetime objects if necessary
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, date_format)
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, date_format)

    # Convert interval_hours to integer
    try:
        interval_hours = int(interval_hours)
    except ValueError:
        raise ValueError(f"Invalid interval_hours value: {interval_hours}. Must be an integer or string representing an integer.")

    # Generate the list of dates
    dates = []
    current_datetime = start_date
    while current_datetime <= end_date:
        dates.append(current_datetime)
        current_datetime += timedelta(hours=interval_hours)  # Increment by interval_hours

    return dates  # Return the list of dates

def files_to_list(fcst_file_template, ref_file_template, dates, shift):
    ffiles = []
    rfiles = []
    for current_datetime in dates:
        fcst_current_datetime = current_datetime + timedelta(hours=int(shift))
        fcycle = fcst_current_datetime.hour - fcst_current_datetime.hour%6
        fcst_file = format_file_template(fcst_file_template, fcst_current_datetime, fcycle)
        cycle = current_datetime.hour - current_datetime.hour%6
        ref_file = format_file_template(ref_file_template, current_datetime, cycle)

        ffiles.append(fcst_file)
        rfiles.append(ref_file)
    
    return ffiles, rfiles