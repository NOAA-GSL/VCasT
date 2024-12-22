from multiprocessing import Pool
from functools import partial
from datetime import timedelta
from mvt.interpolation import *
from mvt.stats import *
from mvt.ioc import *

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
 
        ustat_name = [s.upper() for s in stat_name]

        if "GSS" in ustat_name or "FBIAS" in ustat_name or "POD" in ustat_name or "FAR" in ustat_name or "CSI" in ustat_name or "SR" in ustat_name:
            # Compute scores if any of these metrics are requested
            hits, misses, false_alarms, correct_rejections, total_events = compute_scores(fcst_data, interpolated_data, var_threshold, radius)

        if 'RMSE' in ustat_name:
            stats += [compute_rmse(fcst_data, interpolated_data)]
        if 'BIAS' in ustat_name:
            stats += [compute_bias(fcst_data, interpolated_data)]
        if 'QUANTILES' in ustat_name:
            stats += compute_quantiles(fcst_data, interpolated_data)
        if "MAE" in ustat_name:
            stats += [compute_mae(fcst_data, interpolated_data)]
        if "CORR" in ustat_name:
            stats += [compute_correlation(fcst_data, interpolated_data)]
        if "STDEV" in ustat_name:
            stats += [compute_stdev(fcst_data, interpolated_data)]
        if "GSS" in ustat_name:
            stats += [compute_gss(hits, misses, false_alarms, total_events)]
        if "FBIAS" in ustat_name:
            stats += [calculate_fbias(hits, false_alarms, misses)]
        if "POD" in ustat_name:
            stats += [compute_pod(hits, misses)]
        if "FAR" in ustat_name:
            stats += [compute_far(hits, false_alarms)]
        if "CSI" in ustat_name:
            stats += [compute_csi(hits, misses, false_alarms)]
        if "SR" in ustat_name:
            stats += [compute_success_ratio(hits, false_alarms)]
        if "FSS" in ustat_name:
            stats += [compute_fss(fcst_data, interpolated_data, var_threshold, radius)]
   
        return stats
    
    except Exception as e:
        raise Exception(f"Error processing {date}: {e}")

def process_in_parallel(dates, fcst_files, ref_files, config):
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
        config.write_to_output_file(row)

def dates_to_list(start_date_object, end_date_object,interval_hours):
    dates = []
    current_datetime = start_date_object
    while current_datetime <= end_date_object:
        dates.append(current_datetime)
        current_datetime += timedelta(hours=interval_hours)
    
    return dates

def files_to_list(fcst_file_template, ref_file_template, dates, shift):
    ffiles = []
    rfiles = []
    for current_datetime in dates:
        fcst_current_datetime = current_datetime + timedelta(hours=shift)
        fcycle = fcst_current_datetime.hour - fcst_current_datetime.hour%6
        fcst_file = format_file_template(fcst_file_template, fcst_current_datetime, fcycle)
        cycle = current_datetime.hour - current_datetime.hour%6
        ref_file = format_file_template(ref_file_template, current_datetime, cycle)

        ffiles.append(fcst_file)
        rfiles.append(ref_file)
    
    return ffiles, rfiles