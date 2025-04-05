from multiprocessing import Pool
from functools import partial
from vcast.processing import interpolate_to_target_grid
from vcast.stat import compute_bias, compute_correlation, compute_csi, compute_far,compute_fss, \
                       compute_gss,compute_mae,compute_pod,compute_quantiles,compute_rmse, \
                       compute_scores,compute_stdev,compute_success_ratio, compute_fbias
from vcast.stat import compute_fss_ensemble, compute_reliability
from vcast.io import Preprocessor
import traceback
from datetime import timedelta
import numpy as np

def process_deterministic_multiprocessing(date, lead_time, member, config):
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

        print(fcst_date, lead_time,flush=True)

        # Read forecast and reference data
        fcst_data, flats, flons, ftype = Preprocessor.read_input_data(
            fcst_file, config.fcst_var, config.fcst_type_of_level, config.fcst_level, fcst_date
        )
        ref_data, rlats, rlons, rtype = Preprocessor.read_input_data(
            ref_file, config.ref_var, config.ref_type_of_level, config.ref_level, date
        )

        if fcst_data.ndim == 3:
            if not hasattr(config, 'time') or config.time is None:
                raise ValueError("For 3D forecast data, config.time must be provided.")
            fcst_data = fcst_data[config.time]
            ref_data = ref_data[config.time]
        
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
                stats.append(compute_rmse(fcst_interpolated_data, ref_interpolated_data, threshold))
            elif var == 'bias':
                stats.append(compute_bias(fcst_interpolated_data, ref_interpolated_data, threshold))
            elif var == 'quantiles':
                stats.extend(compute_quantiles(fcst_interpolated_data, ref_interpolated_data))
            elif var == 'mae':
                stats.append(compute_mae(fcst_interpolated_data, ref_interpolated_data))
            elif var == 'corr':
                stats.append(compute_correlation(fcst_interpolated_data, ref_interpolated_data))
            elif var == 'stdev':
                stats.append(compute_stdev(fcst_interpolated_data, ref_interpolated_data))
            elif var == 'gss':
                stats.append(compute_gss(hits, misses, false_alarms, total_events))
            elif var == 'fbias':
                stats.append(compute_fbias(hits, false_alarms, misses))
            elif var == 'pod':
                stats.append(compute_pod(hits, misses))
            elif var == 'far':
                stats.append(compute_far(hits, false_alarms))
            elif var == 'csi':
                stats.append(compute_csi(hits, misses, false_alarms))
            elif var == 'sr':
                stats.append(compute_success_ratio(hits, false_alarms))
            elif var == 'fss':
                stats.append(compute_fss(fcst_interpolated_data, ref_interpolated_data, config.var_threshold, config.var_radius))

        print(f"{fcst_date} Done",flush=True)

        return stats

    except Exception as e:
        print(f"Error processing {date}: {traceback.format_exc()}")
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
                stats.append(compute_fss_ensemble(ensembles_arr, ref_interpolated_data, config.var_threshold, config.var_radius))
        
            if "reliability" in ustat_name:
                stats.append(compute_reliability(ensembles_arr, ref_interpolated_data, config.var_threshold))

            return stats

def process_in_parallel(config, output):
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
                    task = (date,lead_time,member)
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

