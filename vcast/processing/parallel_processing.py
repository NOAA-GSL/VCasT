from multiprocessing import Pool
from functools import partial
from vcast.processing import interpolate_to_target_grid
from vcast.stat import compute_bias, compute_correlation, compute_csi, compute_far,compute_fss, \
                       compute_gss,compute_mae,compute_pod,compute_quantiles,compute_rmse, \
                       compute_scores,compute_stdev,compute_success_ratio, compute_fbias
from vcast.stat import compute_fss_ensemble, compute_reliability
from vcast.io import Preprocessor
from datetime import timedelta
import numpy as np
import logging
import math

def truncate_to_10_decimals(value):
    """
    Truncate a number or a list of numbers to 10 decimal places without rounding.
    If the value is NaN, returns NaN.
    
    Args:
        value (int, float, np.floating, or list): A numeric value or a list of numeric values.
        
    Returns:
        A number truncated to 10 decimal places, or a list of such numbers.
    
    Raises:
        TypeError: If value is not a number or a list of numbers.
    """
    def _truncate(num):
        # Convert num to a regular Python float.
        num_f = float(num)
        if math.isnan(num_f):
            return num_f  # Return nan as is
        return math.trunc(num_f * 1e10) / 1e10

    if isinstance(value, list):
        return [truncate_to_10_decimals(item) for item in value]
    elif isinstance(value, (int, float, np.floating)):
        return _truncate(value)
    else:
        raise TypeError("Input must be a number or a list of numbers.")


logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


def process_deterministic_multiprocessing(date, lead_time, member, test, config):
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
        
        fcst_file = Preprocessor.format_file_template(config.fcst_file_template, date, member, lead_time)
        ref_file = Preprocessor.format_file_template(config.ref_file_template, date, member, lead_time)
        
        fcst_date = date + timedelta(hours=config.shift)

        logging.info(f"Processing {fcst_date} with lead time {lead_time} for member {member}")

        # Read forecast and reference data
        fcst_data, flats, flons, ftype = Preprocessor.read_input_data(
            fcst_file, config.fcst_var, config.fcst_type_of_level, config.fcst_level, fcst_date
        )
        ref_data, rlats, rlons, rtype = Preprocessor.read_input_data(
            ref_file, config.ref_var, config.ref_type_of_level, config.ref_level, date
        )

        if fcst_data.ndim == 3:
            fcst_data = fcst_data[lead_time]
            ref_data = ref_data[lead_time]

        # Apply interpolation if enabled
        if config.interpolation:
            fcst_interpolated_data = interpolate_to_target_grid(fcst_data, flats, flons, config.target_grid) 
            ref_interpolated_data = interpolate_to_target_grid(ref_data, rlats, rlons, config.target_grid)
        else:
            fcst_interpolated_data = fcst_data
            ref_interpolated_data = ref_data

        # Compute statistics
        stats = [date, lead_time]
        if config.cmem:
            stats += [Preprocessor.extract_members(fcst_file, config.fcst_file_template)]
        
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
        for var in config.stat_name:
            if var == 'rmse':
                tstat = compute_rmse(fcst_interpolated_data, ref_interpolated_data, threshold)
            elif var == 'bias':
                tstat = compute_bias(fcst_interpolated_data, ref_interpolated_data, threshold)
            elif var == 'quantiles':
                tstat = compute_quantiles(fcst_interpolated_data, ref_interpolated_data)
            elif var == 'mae':
                tstat = compute_mae(fcst_interpolated_data, ref_interpolated_data)
            elif var == 'corr':
                tstat = compute_correlation(fcst_interpolated_data, ref_interpolated_data)
            elif var == 'stdev':
                tstat = compute_stdev(fcst_interpolated_data, ref_interpolated_data)
            elif var == 'gss':
                tstat = compute_gss(hits, misses, false_alarms, total_events)
            elif var == 'fbias':
                tstat = compute_fbias(hits, false_alarms, misses)
            elif var == 'pod':
                tstat = compute_pod(hits, misses)
            elif var == 'far':
                tstat = compute_far(hits, false_alarms)
            elif var == 'csi':
                tstat = compute_csi(hits, misses, false_alarms)
            elif var == 'sr':
                tstat = compute_success_ratio(hits, false_alarms)
            elif var == 'fss':
                tstat = compute_fss(fcst_interpolated_data, ref_interpolated_data, config.var_threshold, config.var_radius)

            if test:
                tstat = truncate_to_10_decimals(tstat)
    
            if isinstance(tstat, list):
                stats.extend(tstat)
            else:
                stats.append(tstat)
            
        logging.info(f"Completed processing for {fcst_date} with lead time {lead_time} for member {member}")

        return stats

    except Exception as e:
        logging.exception(f"Error processing {date}")
        return None  # Return None for failed entries

def process_ensemble_multiprocessing(date,lead_time,config):

            ensembles = []

            ustat_name = [s.lower() for s in config.stat_name]
            stats = [date, lead_time]

            ref_file = Preprocessor.format_file_template(config.ref_file_template, date, 0, lead_time)

            ref_data, rlats, rlons, rtype = Preprocessor.read_input_data(
                ref_file, config.ref_var, config.ref_type_of_level, config.ref_level, date
            )
            
            if config.interpolation:
                ref_interpolated_data = interpolate_to_target_grid(ref_data, rlats, rlons, config.target_grid)
            else:
                ref_interpolated_data = ref_data

            for member in config.members:

                fcst_date = date + timedelta(hours=config.shift)
                
                fcst_file = Preprocessor.format_file_template(config.fcst_file_template, date, member, lead_time)

                # Read forecast and reference data
                fcst_data, flats, flons, _ = Preprocessor.read_input_data(
                    fcst_file, config.fcst_var, config.fcst_type_of_level, config.fcst_level, fcst_date
                )

                # Apply interpolation if enabled
                if config.interpolation:
                    fcst_interpolated_data = interpolate_to_target_grid(fcst_data, flats, flons, config.target_grid) 
                else:
                    fcst_interpolated_data = fcst_data
                
                ensembles.append(fcst_interpolated_data)

            ensembles_arr = np.array(ensembles)
            
            if 'fss' in ustat_name:
                tstat = compute_fss_ensemble(ensembles_arr, ref_interpolated_data, config.var_threshold, config.var_radius)
        
            if "reliability" in ustat_name:
                tstat = compute_reliability(ensembles_arr, ref_interpolated_data, config.var_threshold)

            return stats

def process_in_parallel(config, output, test):
    """
    Process all dates in parallel using multiprocessing.
    
    Args:
        dates (list): List of datetime objects.
        fcst_files (list): Forecast file paths.
        ref_files (list): Reference file paths.
        config (ConfigLoader): Configuration object.
        output (OutputFileHandler): Output file handler.
    """

    tasks = []

    dates = Preprocessor.dates_to_list(config.start_date, config.end_date, config.interval_hours)

    if config.stat_type == "det":
        worker_function = partial(process_deterministic_multiprocessing, config=config)
        for date in dates:
            for lead_time in config.lead_times:
                for member in config.members:    
                    task = (date,lead_time,member,test)
                    tasks.append(task)

    elif config.stat_type == "ens":
        worker_function = partial(process_ensemble_multiprocessing, config=config)
        for date in dates:
            for lead_time in config.lead_times:
                task = (date,lead_time)
                tasks.append(task)
    
    else:
        raise Exception("Process execution failed.")

    with Pool(processes=config.processes) as pool:
        results = pool.starmap(worker_function, tasks)
        for row in results:
            if row is not None:
                output.write_to_output_file(row)

