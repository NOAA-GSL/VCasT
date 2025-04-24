from datetime import datetime, timedelta
import numpy as np
import pygrib
import xarray as xr
import re
import os
from pathlib import Path
import pandas as pd
from vcast.stat import AVAILABLE_VARS 

class Preprocessor:
    """Handles input/output file preparation and date formatting."""

    _TABLE_PATH = Path(__file__).resolve().parents[2] / 'util' / 'lookup_table.txt'

    @staticmethod
    def read_input_data(input_file, var_name, type_of_level, level, date):
        from vcast.io import FileChecker
        """
        Reads forecast or observation data from a given input file.

        Args:
            input_file (str): Path to the input file (NetCDF or GRIB2).
            var_name (str): Name of the variable to extract (e.g., "TMP").
            type_of_level (str): Type of level for filtering (e.g., "heightAboveGround").
            level (int): Specific level value to extract (e.g., 2 for 2m temperature).

        Returns:
            tuple: 
                - data (numpy.ndarray): Extracted variable data.
                - lats (numpy.ndarray): Latitude values.
                - lons (numpy.ndarray): Longitude values.
                - stype (str): File format type ('netcdf' or 'grib2').

        Raises:
            Exception: If the file format is unknown or unsupported.
        """
        stime = date.strftime("%Y-%m-%dT%H:%M:%S")
        fc = FileChecker(input_file)        
        file_type = fc.identify_file_type()

        if 'netcdf' in file_type:
            data, lats, lons = Preprocessor.read_netcdf(input_file, var_name, type_of_level, level)   
            stype = 'netcdf'
        elif 'grib2' in file_type:
            data, lats, lons = Preprocessor.read_grib2(input_file, var_name, type_of_level, level)
            stype = 'grib2'
        elif 'zarr' in file_type:
            data, lats, lons = Preprocessor.read_zarr(input_file, var_name, type_of_level, level, stime)
            stype = 'zarr'            
        else:
            raise Exception("Error: File format unknown.")
        
        if lats.ndim == 1 and lons.ndim == 1:
            lon_grid, lat_grid = np.meshgrid(lons, lats)
        else:
            lat_grid, lon_grid = lats, lons
        
        data = np.squeeze(data)
        return data, lat_grid, lon_grid, stype

    @classmethod
    def get_lookup_table_path(cls, check: bool = True) -> Path:
        """
        Return the path to the lookup table file, optionally verifying its existence.

        Args:
            check: If True, ensure the file exists and is a regular file.

        Raises:
            LookupTableNotFound: if file is missing when check is True.
        """
        path = cls._TABLE_PATH
        if check and not path.is_file():
            raise Exception(f"Lookup table not found at {path}")
        return path

    @staticmethod
    def get_meta_data(
        df: pd.DataFrame,
        variable: str,        
        model: str,
        level: str = None
    ) -> tuple[str, str, str]:
        """
        Extract `model_variable`, `level`, and `level_name` for a given forecast or reference.

        Args:
            df: DataFrame loaded from the lookup table.
            variable: the `variable` column value.
            model: the `model` column value.
            level: the level to match.


        Returns:
            Tuple of (model_variable, level, level_name).

        Raises:
            LookupTableDataError: if no match or ambiguous matches remain.
        """
        subset = df.loc[
            (df['variable'] == variable) &
            (df['model'] == model)
        ]

        if subset.empty:
            raise Exception(
                f"No metadata for variable={variable}, model={model}!"
            )
        
        if len(subset) > 1:
            raise Exception(
                f"Ambiguous metadata for variable={variable}, model={model}, level={level}!"
            )

        row = subset.iloc[0]

        if str(row['multi_level']).lower() == 't':
            if level is None:
                raise Exception(
                    f"Level specification required for variable={variable}, model={model}"
                )

        return subset['model_variable'].iat[0], subset['level'].iat[0], subset['level_name'].iat[0], subset['units'].iat[0]

    @classmethod
    def process_variables(
        cls,
        config
    ) -> dict[str, tuple[str, int, str]]:
        """
        For both forecast (`fcst`) and reference (`ref`), lookup metadata.

        Expects `config` to provide attributes:
          - `fcst_var`, `fcst_level`, `fcst_model`
          - `ref_var`,  `ref_level`,  `ref_model`

        Returns:
            A dict with keys 'fcst' and 'ref', each mapping to the
            (model_variable, level, level_name) tuple.
        """
        path = cls.get_lookup_table_path()
        df = pd.read_csv(path, sep='\t', index_col=False)

        result = {}
        for tag in ('fcst', 'ref'):
            mdl = getattr(config,f"{tag}_model")
            if hasattr(config,"level"):
                result[tag] = cls.get_meta_data(df, config.var, mdl, config.level)
            else:
                result[tag] = cls.get_meta_data(df, config.var, mdl)
   
        fcst_units = result['fcst'][3]
        ref_units = result['ref'][3]
   
        if fcst_units != ref_units:
            raise Exception(f"Unit conversion not implemented: fcst units '{fcst_units}' vs ref units '{ref_units}'")

        return result

    @staticmethod
    def validate_config(config, config_type):
        """
        Validate configuration parameters based on config_type.
        
        If config_type is "stat", the function checks that:
          - All required configuration attributes exist.
          - start_date and end_date follow the expected date format ("%Y-%m-%d_%H:%M:%S"),
            and end_date is later than start_date.
          - interpolation is a boolean and, if True, target_grid exists.
          - output_dir exists as a directory.
          - stat_type is either "deterministic" or "ensemble".
          - stat_name is a list whose (lowercase) values are in AVAILABLE_VARS.
          - processes is an integer > 0.
          - interval_hours is an integer.
          
        Additionally, if any of the optional lead time attributes exist (start_lead_time, end_lead_time, interval_lead_time):
          - All must exist.
          - start_lead_time and end_lead_time must be integers, and end_lead_time must be equal or greater than start_lead_time.
          - interval_lead_time must be an integer.
          - Then, config.lead_times is computed using Preprocessor.lead_times_to_list.
          
        Also, if the optional attribute members exists, it must be a list.
        
        Finally, if the optional attribute time exists, it must be an integer.
                
        Parameters:
            config: Configuration object (e.g., from ConfigLoader) with attributes.
            config_type (str): A string indicating the configuration type.
            
        Returns:
            config if validations pass for the given config_type.
            
        Raises:
            ValueError: If any of the validations for config_type "stat" fail.
        """
    
        if config_type == "stat":
            required_attributes = [
                "start_date", "end_date", "interval_hours",  # "time" is now optional
                "fcst_file_template", "var","fcst_model",
                "ref_file_template", "ref_model",
                "output_dir", "output_filename",
                "stat_type", "stat_name",
                "interpolation", "target_grid",
                "processes"
            ]
           
            # Check that all required attributes exist
            missing = [attr for attr in required_attributes if not hasattr(config, attr)]
            if missing:
                raise ValueError("Missing required configuration attributes: " + ", ".join(missing))

            res = Preprocessor.process_variables(config)

            config.fcst_var = res['fcst'][0]
            config.fcst_level = res['fcst'][1]
            config.fcst_type_of_level = res['fcst'][2]

            config.ref_var = res['ref'][0]
            config.ref_level = res['ref'][1]
            config.ref_type_of_level = res['ref'][2]

            # Define the expected date format for main dates
            date_format = "%Y-%m-%d_%H:%M:%S"
            
            # Validate start_date and end_date
            try:
                start_date_obj = datetime.strptime(config.start_date, date_format)
            except Exception:
                raise ValueError(
                    f"start_date must be a valid date in format {date_format}. Got: '{config.start_date}'"
                )
            
            try:
                end_date_obj = datetime.strptime(config.end_date, date_format)
            except Exception:
                raise ValueError(
                    f"end_date must be a valid date in format {date_format}. Got: '{config.end_date}'"
                )
            
            # Ensure that end_date comes after start_date
            if end_date_obj < start_date_obj:
                raise ValueError("end_date must be later than start_date.")
            
            # Check that interpolation is a boolean
            if not isinstance(config.interpolation, bool):
                raise ValueError("interpolation must be a boolean (True or False)")
            
            # If interpolation is True, verify that target_grid exists
            if config.interpolation:
                if not os.path.exists(config.target_grid):
                    raise ValueError(f"target_grid specified does not exist: {config.target_grid}")
            
            # Check that output_dir exists as a directory
            if not os.path.isdir(config.output_dir):
                raise ValueError(f"output_dir does not exist or is not a directory: {config.output_dir}")
            
            # Validate stat_type: must be either "deterministic" or "ensemble"
            allowed_stat_types = {"det", "ens"}
            if config.stat_type not in allowed_stat_types:
                raise ValueError(f"stat_type must be either 'det' or 'ens'. Got: '{config.stat_type}'")
            
            # Validate stat_name: must be a list and all entries (lowercase) must be in AVAILABLE_VARS
            if not isinstance(config.stat_name, list):
                raise ValueError("stat_name must be a list.")
            for stat in config.stat_name:
                stat, _, _, _ = Preprocessor.parse_metric_string(stat)
                if stat.lower() not in AVAILABLE_VARS:
                    allowed = ", ".join(sorted(AVAILABLE_VARS))
                    raise ValueError(f"Invalid stat in stat_name: '{stat}'. Allowed values: {allowed}")
            
            # Check processes: must be an integer > 0
            if not isinstance(config.processes, int) or config.processes <= 0:
                raise ValueError(f"processes must be an integer greater than 0. Got: {config.processes}")
            
            # Check interval_hours: must be an integer
            if not isinstance(config.interval_hours, int):
                try:
                    config.interval_hours = int(config.interval_hours)
                except Exception:
                    raise ValueError(f"interval_hours must be an integer. Got: {config.interval_hours}")
            
            # Optional: Validate lead time attributes.
            # If any one exists, then all must exist.
            config.lead_times = range(0,1)
            if (hasattr(config, 'start_lead_time') or 
                hasattr(config, 'end_lead_time') or 
                hasattr(config, 'interval_lead_time')):
                
                missing_lead = [key for key in ['start_lead_time', 'end_lead_time', 'interval_lead_time']
                                if not hasattr(config, key)]
                if missing_lead:
                    raise ValueError("Optional lead time attributes incomplete. Missing: " + ", ".join(missing_lead))
                
                # Convert start_lead_time and end_lead_time to integers
                try:
                    config.start_lead_time = int(config.start_lead_time)
                except Exception:
                    raise ValueError(f"start_lead_time must be an integer. Got: {config.start_lead_time}")
                try:
                    config.end_lead_time = int(config.end_lead_time)
                except Exception:
                    raise ValueError(f"end_lead_time must be an integer. Got: {config.end_lead_time}")
                
                # Ensure that end_lead_time is equal or greater than start_lead_time
                if config.end_lead_time < config.start_lead_time:
                    raise ValueError("end_lead_time must be equal or greater than start_lead_time.")
                
                # Check interval_lead_time: must be an integer
                if not isinstance(config.interval_lead_time, int):
                    try:
                        config.interval_lead_time = int(config.interval_lead_time)
                    except Exception:
                        raise ValueError(f"interval_lead_time must be an integer. Got: {config.interval_lead_time}")
                
                # Compute the lead_times list using the Preprocessor
                config.lead_times = Preprocessor.lead_times_to_list(
                    config.start_lead_time, config.end_lead_time, config.interval_lead_time
                )
            
            # Optional: Validate members attribute if it exists
            if hasattr(config, 'members'):
                if not isinstance(config.members, list):
                    raise ValueError(f"members must be a list. Got: {config.members} (type: {type(config.members)})")
                config.cmem = True
            else:
                config.members = [0]
                config.cmem = False
            
            # Optional: Validate time attribute if it exists; it must be an integer.
            if hasattr(config, 'time'):
                if not isinstance(config.time, int):
                    try:
                        config.time = int(config.time)
                    except Exception:
                        raise ValueError(f"time must be an integer. Got: {config.time}")
            
            return config
        
        else:
            # For other config_types, add alternative validation logic as needed.
            return config

    @staticmethod
    def parse_metric_string(var_string):
        """
        Parse a metric specifier of the form:
            "metric"             → returns (metric, None, None)
            "metric:thresh"      → returns (metric, float(thresh), None)
            "metric:thresh:rad"  → returns (metric, float(thresh), int(rad))
    
        Raises ValueError if the format isn't recognized.
        """
        parts = var_string.split(":")
        metric = parts[0]
    
        # no extra args
        if len(parts) == 1:
            return metric, None, None, None
    
        # one extra arg  → threshold
        if len(parts) == 2:
            return metric, float(parts[1]), None, None
    
        # two extra args → threshold and radius
        if len(parts) == 3:
            return metric, float(parts[1]), float(parts[2]), None
        
        if len(parts) == 4:
            return metric, float(parts[1]), float(parts[2]), float(parts[3])
    
        raise ValueError(f"Invalid metric specifier: '{var_string}'")

    @staticmethod
    def read_grib2(grib2_file, var_name, type_of_level, level):
        """
        Reads a GRIB2 file and extracts the specified variable data along with latitude and longitude arrays.
        Requires filtering by type of level and level.
    
        Parameters:
        - grib2_file (str): Path to the GRIB2 file.
        - var_name (str): Name of the variable to extract (e.g., "TMP").
        - type_of_level (str): Type of level to filter (e.g., "surface", "isobaricInhPa").
        - level (int): Specific level to filter (e.g., 10 for 10 m above ground).
    
        Returns:
        - data (numpy.ndarray): Variable data array.
        - lats (numpy.ndarray): Latitude array.
        - lons (numpy.ndarray): Longitude array.
    
        Raises:
        - ValueError: If the specified variable or level is not found.
        """
        try:
            # Open the GRIB2 file
            grbs = pygrib.open(grib2_file)
            grb = grbs.select(shortName=var_name, typeOfLevel=type_of_level, level=int(level))[0]
    
            # Extract the data, latitude, and longitude
            data = grb.values
            lats, lons = grb.latlons()
    
            grbs.close()
            return data, lats, lons
    
        except (IndexError, ValueError) as e:
            raise ValueError(f"Variable '{var_name}' with type_of_level '{type_of_level}' and level {level} not found in the file.") from e
        except Exception as e:
            raise RuntimeError(f"Error reading GRIB2 file '{grib2_file}': {e}") from e

    @staticmethod
    def read_input(input, var_name, type_of_level=None, level=None, time=None):
        """
        Reads a Zarr dataset using xarray and extracts the specified variable data 
        along with latitude and longitude arrays. Handles cases where the type_of_level 
        dimension is absent for surface fields. Optionally selects a specific time 
        if multiple time steps are available.
    
        Parameters:
        - zarr_folder (str): Path to the Zarr folder.
        - var_name (str): Name of the variable to extract.
        - type_of_level (str, optional): Name of the dimension (e.g., 'level').
        - level (int or float, optional): Specific level value to extract (if applicable).
        - time (str or np.datetime64, optional): Specific time to select. If provided and the dataset
          contains a time coordinate, the data is selected at the nearest time step.
    
        Returns:
        - data (numpy.ndarray): Variable data array.
        - lats (numpy.ndarray): Latitude array.
        - lons (numpy.ndarray): Longitude array.
    
        Raises:
        - ValueError: If the variable or necessary coordinates (or time coordinate when required) are not found.
        - RuntimeError: If an error occurs while reading the Zarr dataset.
        """

        def try_open_with_engines(path):
            open_attempts = [
                ("zarr", lambda p: xr.open_zarr(p, decode_timedelta=True)),
                ("netcdf", lambda p: xr.open_dataset(p, decode_timedelta=True)),
                ("grib2", lambda p: xr.open_dataset(p, engine="cfgrib")),
            ]
            errors = {}
            for label, opener in open_attempts:
                try:
                    ds = opener(path)
                    print(f"Successfully opened with {label}")
                    return ds
                except Exception as e:
                    errors[label] = str(e)
            raise RuntimeError(f"Failed to open dataset at '{path}' using any known format.\nErrors:\n" +
                               "\n".join(f"- {k}: {v}" for k, v in errors.items()))

        ds = try_open_with_engines(input)
        
        try:
            
            # If time selection is requested and the dataset has a time coordinate, subset it first.
            if time is not None:
                if 'time' in ds:
                    ds = ds.sel(time=time)
                else:
                    raise ValueError("Time coordinate not found in Zarr dataset.")
    
            # Ensure the variable exists
            if var_name not in ds:
                raise ValueError(f"Variable '{var_name}' not found in Zarr dataset. Available variables: {list(ds.data_vars.keys())}")
    
            # Extract latitude and longitude arrays
            if 'latitude' in ds:
                lats = ds['latitude'].values
            elif 'lat' in ds:
                lats = ds['lat'].values
            else:
                raise ValueError("Latitude variable not found in Zarr dataset.")
    
            if 'longitude' in ds:
                lons = ds['longitude'].values
            elif 'lon' in ds:
                lons = ds['lon'].values
            else:
                raise ValueError("Longitude variable not found in Zarr dataset.")
    
            # Extract variable data
            var_data = ds[var_name]
    
            # Check if the level dimension exists in the dataset
            if type_of_level and type_of_level in var_data.dims:
                if level is not None:
                    if type_of_level in ds:
                        level_values = ds[type_of_level].values
                        if level not in level_values:
                            raise ValueError(f"Level '{level}' not found in dimension '{type_of_level}'. Available levels: {level_values}")
                        
                        # Select the specified level
                        data = var_data.sel({type_of_level: level}).values
                    else:
                        raise ValueError(f"Level dimension '{type_of_level}' not found in dataset.")
                else:
                    raise ValueError("Level must be specified for non-surface fields.")
            else:
                # Assume surface field (no level dimension)
                data = var_data.values
    
            return data, lats, lons
    
        except Exception as e:
            raise RuntimeError(f"Error reading Zarr dataset at '{zarr_folder}': {e}") from e

    @staticmethod
    def read_zarr(zarr_folder, var_name, type_of_level=None, level=None, time=None):
        """
        Reads a Zarr dataset using xarray and extracts the specified variable data 
        along with latitude and longitude arrays. Handles cases where the type_of_level 
        dimension is absent for surface fields. Optionally selects a specific time 
        if multiple time steps are available.
    
        Parameters:
        - zarr_folder (str): Path to the Zarr folder.
        - var_name (str): Name of the variable to extract.
        - type_of_level (str, optional): Name of the dimension (e.g., 'level').
        - level (int or float, optional): Specific level value to extract (if applicable).
        - time (str or np.datetime64, optional): Specific time to select. If provided and the dataset
          contains a time coordinate, the data is selected at the nearest time step.
    
        Returns:
        - data (numpy.ndarray): Variable data array.
        - lats (numpy.ndarray): Latitude array.
        - lons (numpy.ndarray): Longitude array.
    
        Raises:
        - ValueError: If the variable or necessary coordinates (or time coordinate when required) are not found.
        - RuntimeError: If an error occurs while reading the Zarr dataset.
        """
        try:
            # Open the Zarr dataset using xarray
            ds = xr.open_zarr(zarr_folder,decode_timedelta=True)
            
            # If time selection is requested and the dataset has a time coordinate, subset it first.
            if time is not None:
                if 'time' in ds:
                    ds = ds.sel(time=time)
                else:
                    raise ValueError("Time coordinate not found in Zarr dataset.")
    
            # Ensure the variable exists
            if var_name not in ds:
                raise ValueError(f"Variable '{var_name}' not found in Zarr dataset. Available variables: {list(ds.data_vars.keys())}")
    
            # Extract latitude and longitude arrays
            if 'latitude' in ds:
                lats = ds['latitude'].values
            elif 'lat' in ds:
                lats = ds['lat'].values
            else:
                raise ValueError("Latitude variable not found in Zarr dataset.")
    
            if 'longitude' in ds:
                lons = ds['longitude'].values
            elif 'lon' in ds:
                lons = ds['lon'].values
            else:
                raise ValueError("Longitude variable not found in Zarr dataset.")
    
            # Extract variable data
            var_data = ds[var_name]
    
            # Check if the level dimension exists in the dataset
            if type_of_level and type_of_level in var_data.dims:
                if level is not None:
                    if type_of_level in ds:
                        level_values = ds[type_of_level].values
                        if level not in level_values:
                            raise ValueError(f"Level '{level}' not found in dimension '{type_of_level}'. Available levels: {level_values}")
                        
                        # Select the specified level
                        data = var_data.sel({type_of_level: level}).values
                    else:
                        raise ValueError(f"Level dimension '{type_of_level}' not found in dataset.")
                else:
                    raise ValueError("Level must be specified for non-surface fields.")
            else:
                # Assume surface field (no level dimension)
                data = var_data.values
    
            return data, lats, lons
    
        except Exception as e:
            raise RuntimeError(f"Error reading Zarr dataset at '{zarr_folder}': {e}") from e


    @staticmethod
    def read_netcdf(netcdf_file, var_name, type_of_level=None, level=None):
        """
        Reads a NetCDF file using xarray and extracts the specified variable data 
        along with latitude and longitude arrays. Handles cases where the type_of_level 
        dimension is absent for surface fields.
    
        Parameters:
        - netcdf_file (str): Path to the NetCDF file.
        - var_name (str): Name of the variable to extract.
        - type_of_level (str, optional): Name of the dimension (e.g., 'level').
        - level (int or float, optional): Specific level value to extract (if applicable).
    
        Returns:
        - data (numpy.ndarray): Variable data array.
        - lats (numpy.ndarray): Latitude array.
        - lons (numpy.ndarray): Longitude array.
    
        Raises:
        - ValueError: If the variable or necessary coordinates are not found.
        - RuntimeError: If an error occurs while reading the NetCDF file.
        """
        try:
            # Open the NetCDF file using xarray
            ds = xr.open_dataset(netcdf_file)
    
            # Ensure the variable exists
            if var_name not in ds:
                raise ValueError(f"Variable '{var_name}' not found in NetCDF file. Available variables: {list(ds.data_vars.keys())}")
    
            # Extract latitude and longitude arrays
            if 'latitude' in ds:
                lats = ds['latitude'].values
            elif 'lat' in ds:
                lats = ds['lat'].values
            else:
                raise ValueError("Latitude variable not found in NetCDF file.")
    
            if 'longitude' in ds:
                lons = ds['longitude'].values
            elif 'lon' in ds:
                lons = ds['lon'].values
            else:
                raise ValueError("Longitude variable not found in NetCDF file.")
    
            # Extract variable data
            var_data = ds[var_name]
    
            # Check if the level dimension exists in the dataset
            if type_of_level and type_of_level in var_data.dims:
                if level is not None:
                    # Ensure the level exists
                    if type_of_level in ds:
                        level_values = ds[type_of_level].values
                        if level not in level_values:
                            raise ValueError(f"Level '{level}' not found in dimension '{type_of_level}'. Available levels: {level_values}")
                        
                        # Select the specified level
                        data = var_data.sel({type_of_level: level}).values
                    else:
                        raise ValueError(f"Level dimension '{type_of_level}' not found in dataset.")
                else:
                    raise ValueError("Level must be specified for non-surface fields.")
            else:
                # Assume surface field (no level dimension)
                data = var_data.values
    
            # Close the dataset
            ds.close()

            return data, lats, lons
    
        except Exception as e:
            raise RuntimeError(f"Error reading NetCDF file '{netcdf_file}': {e}") from e

    @staticmethod
    def calculate_valid_time(date_obj, lead_time):
        return date_obj + timedelta(hours=lead_time)

    @staticmethod
    def format_file_template(template, date_obj, member = None, lead_time = 0):
        """
        Replaces placeholders in a file template with corresponding datetime values.

        Args:
            template (str): Template string with placeholders for year, month, day, hour, minute, and cycle.
            date_obj (datetime): Datetime object to extract values from.
            cycle (int): Cycle value to replace in the template.

        Returns:
            str: Formatted file path.
        """

        valid_date_obj = Preprocessor.calculate_valid_time(date_obj, lead_time)

        

        formatted_file_path = template.format(
            year=date_obj.year,
            month=f"{date_obj.month:02}",
            day=f"{date_obj.day:02}",
            hour=f"{date_obj.hour:02}",
            minute=f"{date_obj.minute:02}",
            members=member,
            lead_time=f"{lead_time:02}",
            valid_year=valid_date_obj.year,
            valid_month=f"{valid_date_obj.month:02}",
            valid_day=f"{valid_date_obj.day:02}",
            valid_hour=f"{valid_date_obj.hour:02}"
        )

        return formatted_file_path

    @staticmethod
    def lead_times_to_list(start_lead_time, end_lead_time, interval_lead_time):
        return range(start_lead_time,end_lead_time + 1,interval_lead_time)

    @staticmethod
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
        start_date = datetime.strptime(start_date, date_format)
        end_date = datetime.strptime(end_date, date_format)

        interval_hours = int(interval_hours)

        # Generate the list of dates
        dates = []
        current_datetime = start_date
        while current_datetime <= end_date:
            dates.append(current_datetime)
            current_datetime += timedelta(hours=interval_hours)  # Increment by interval_hours

        return dates  # Return the list of dates

    @staticmethod
    def files_to_list(fcst_file_template, ref_file_template, dates, lead_times, members = None):
        """
        Generates forecast and reference file paths based on templates and datetime ranges.

        Args:
            fcst_file_template (str): Template for forecast file paths.
            ref_file_template (str): Template for reference file paths.
            dates (list): List of datetime objects to generate files for.

        Returns:
            tuple: Two lists containing forecast and reference file paths.
        """
        ffiles = []
        rfiles = []
        
        for current_datetime in np.unique(dates):
            for lead_time in lead_times:                       
                for member in members:
                    fcst_current_datetime = current_datetime
        
                    # Calculate forecast and reference cycles
                    fcycle = fcst_current_datetime.hour - (fcst_current_datetime.hour % 6)
                    cycle = current_datetime.hour - (current_datetime.hour % 6)

                    
                    # Format the file paths
                    fcst_file = Preprocessor.format_file_template(fcst_file_template, fcst_current_datetime, fcycle, member, lead_time)
                    ref_file = Preprocessor.format_file_template(ref_file_template, current_datetime, cycle, member, lead_time)
        
                    ffiles.append(fcst_file)
                    rfiles.append(ref_file)

        return ffiles, rfiles

    @staticmethod
    def extract_members(path, template):
        """
        Extracts members from a file path based on a given template.
    
        Args:
            path (str): The actual path to be matched.
            template (str): The template string containing placeholders.
    
        Returns:
            str: Extracted member name.
        
        Raises:
            ValueError: If the path doesn't match the template.
        """
        # Convert template placeholders to regex capture groups
        pattern = template
        pattern = pattern.replace("{year}", r"(?P<year>\d{4})")
        pattern = pattern.replace("{month}", r"(?P<month>\d{2})")
        pattern = pattern.replace("{day}", r"(?P<day>\d{2})")
        pattern = pattern.replace("{lead_time}", r"(?P<lead_time>\d+)")
        pattern = pattern.replace("{members}", r"(?P<members>[^/]+)")  # Capture any member name
        
        # Compile the pattern to regex
        regex_pattern = re.compile(pattern)
        
        # Search for a match
        match = regex_pattern.match(path)
        
        if match:
            # Extract 'members' from the match
            return match.group("members")
        else:
            raise ValueError(f"Path '{path}' does not match the template '{template}'.")

