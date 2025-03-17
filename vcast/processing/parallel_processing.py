from multiprocessing import Pool
from functools import partial
from vcast.processing import interpolate_to_target_grid
from vcast.stat import compute_bias, compute_correlation, compute_csi, compute_far,compute_fss, \
                       compute_gss,compute_mae,compute_pod,compute_quantiles,compute_rmse, \
                       compute_scores,compute_stdev,compute_success_ratio, compute_fbias
from vcast.io import Preprocessor
import traceback
from datetime import timedelta

def process_date_multiprocessing(date, fcst_file, ref_file, config):
    """
    Processes a single date entry in parallel using multiprocessing.
    
    Args:
        date (datetime): The date to process.
        fcst_file (str): Path to the forecast file.
        ref_file (str): Path to the reference file.
        config (ConfigLoader): Configuration object.
    
    Returns:
        list: Processed statistics for the given date.
    """
    try:

        fcst_date = date + timedelta(hours=config.shift)
        # Read forecast and reference data
        fcst_data, flats, flons, ftype = Preprocessor.read_input_data(
            fcst_file, config.fcst_var, config.fcst_type_of_level, config.fcst_level, fcst_date
        )
        ref_data, rlats, rlons, rtype = Preprocessor.read_input_data(
            ref_file, config.ref_var, config.ref_type_of_level, config.ref_level, date
        )

        # Adjust longitude ranges if necessary
        if 'grib2' in rtype:
            rlons += 360.
        if 'grib2' in ftype:
            flons += 360.

        # Apply interpolation if enabled
        if config.interpolation:
            fcst_interpolated_data = interpolate_to_target_grid(fcst_data, flats, flons, config.target_grid) 
            ref_interpolated_data = interpolate_to_target_grid(ref_data, rlats, rlons, config.target_grid)
        else:
            fcst_interpolated_data = fcst_data
            ref_interpolated_data = ref_data

        # Compute statistics
        stats = [date]
        ustat_name = [s.lower() for s in config.stat_name]

        if any(stat in ustat_name for stat in ["gss", "fbias", "pod", "far", "csi", "sr"]):
            hits, misses, false_alarms, correct_rejections, total_events = compute_scores(
                fcst_interpolated_data, ref_interpolated_data, config.var_threshold, config.var_radius
            )
        
        if config.threshold == "" or config.threshold is None:
            threshold = None
        else:
            threshold = config.threshold


        # Add computed statistics
        if 'rmse' in ustat_name:
            stats.append(compute_rmse(fcst_interpolated_data, ref_interpolated_data, threshold))
        if 'bias' in ustat_name:
            stats.append(compute_bias(fcst_interpolated_data, ref_interpolated_data, threshold))
        if 'quantiles' in ustat_name:
            stats.extend(compute_quantiles(fcst_interpolated_data, ref_interpolated_data))
        if 'mae' in ustat_name:
            stats.append(compute_mae(fcst_interpolated_data, ref_interpolated_data))
        if 'corr' in ustat_name:
            stats.append(compute_correlation(fcst_interpolated_data, ref_interpolated_data))
        if 'stdev' in ustat_name:
            stats.append(compute_stdev(fcst_interpolated_data, ref_interpolated_data))
        if 'gss' in ustat_name:
            stats.append(compute_gss(hits, misses, false_alarms, total_events))
        if 'fbias' in ustat_name:
            stats.append(compute_fbias(hits, false_alarms, misses))
        if 'pod' in ustat_name:
            stats.append(compute_pod(hits, misses))
        if 'far' in ustat_name:
            stats.append(compute_far(hits, false_alarms))
        if 'csi' in ustat_name:
            stats.append(compute_csi(hits, misses, false_alarms))
        if 'sr' in ustat_name:
            stats.append(compute_success_ratio(hits, false_alarms))
        if 'fss' in ustat_name:
            stats.append(compute_fss(fcst_interpolated_data, ref_interpolated_data, config.var_threshold, config.var_radius))

        return stats

    except Exception as e:
        print(f"Error processing {date}: {traceback.format_exc()}")
        return None  # Return None for failed entries

def process_in_parallel(dates, fcst_files, ref_files, config, output):
    """
    Process all dates in parallel using multiprocessing.
    
    Args:
        dates (list): List of datetime objects.
        fcst_files (list): Forecast file paths.
        ref_files (list): Reference file paths.
        config (ConfigLoader): Configuration object.
        output (OutputFileHandler): Output file handler.
    """
    # Use multiprocessing pool
    with Pool(processes=config.processes) as pool:
        worker_function = partial(process_date_multiprocessing, config=config)
        results = pool.starmap(worker_function, zip(dates, fcst_files, ref_files))

    # Write results to output file
    for row in results:
        if row is not None:
            output.write_to_output_file(row)
