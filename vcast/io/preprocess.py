from vcast.io import FileChecker
from datetime import datetime, timedelta
import numpy as np
import pygrib
import xarray as xr

class Preprocessor:
    """Handles input/output file preparation and date formatting."""

    @staticmethod
    def read_input_data(input_file, var_name, type_of_level, level, date):
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
        if 'netcdf' in fc.identify_file_type():
            data, lats, lons = Preprocessor.read_netcdf(input_file, var_name, type_of_level, level)   
            stype = 'netcdf'
        elif 'grib2' in fc.identify_file_type():
            data, lats, lons = Preprocessor.read_grib2(input_file, var_name, type_of_level, level)
            stype = 'grib2'
        elif 'zarr' in fc.identify_file_type():
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
    
            # Filter the GRIB message based on var_name, type_of_level, and level
            grb = grbs.select(shortName=var_name, typeOfLevel=type_of_level, level=level)[0]
    
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
                    ds = ds.sel(time=time, method="nearest")
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
    def format_file_template(template, date_obj, cycle=0):
        """
        Replaces placeholders in a file template with corresponding datetime values.

        Args:
            template (str): Template string with placeholders for year, month, day, hour, minute, and cycle.
            date_obj (datetime): Datetime object to extract values from.
            cycle (int): Cycle value to replace in the template.

        Returns:
            str: Formatted file path.
        """
        formatted_file_path = template.format(
            year=date_obj.year,
            month=f"{date_obj.month:02}",
            day=f"{date_obj.day:02}",
            cycle=f"{cycle:02}",
            hour=f"{date_obj.hour:02}",
            minute=f"{date_obj.minute:02}",
        )
        
        return formatted_file_path

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
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, date_format)
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, date_format)

        # Convert interval_hours to integer
        try:
            interval_hours = int(interval_hours)
        except ValueError:
            raise ValueError(
                f"Invalid interval_hours value: {interval_hours}. Must be an integer or string representing an integer."
            )

        # Generate the list of dates
        dates = []
        current_datetime = start_date
        while current_datetime <= end_date:
            dates.append(current_datetime)
            current_datetime += timedelta(hours=interval_hours)  # Increment by interval_hours

        return dates  # Return the list of dates

    @staticmethod
    def files_to_list(fcst_file_template, ref_file_template, dates, shift):
        """
        Generates forecast and reference file paths based on templates and datetime ranges.

        Args:
            fcst_file_template (str): Template for forecast file paths.
            ref_file_template (str): Template for reference file paths.
            dates (list): List of datetime objects to generate files for.
            shift (int or str): Shift (in hours) to apply to forecast times.

        Returns:
            tuple: Two lists containing forecast and reference file paths.
        """
        try:
            # Convert shift to integer
            shift = int(shift)
        except ValueError:
            raise ValueError(f"Invalid shift value: {shift}. Must be an integer or string representing an integer.")

        ffiles = []
        rfiles = []

        for current_datetime in dates:
            # Apply the shift for forecast datetime
            fcst_current_datetime = current_datetime + timedelta(hours=shift)

            # Calculate forecast and reference cycles
            fcycle = fcst_current_datetime.hour - (fcst_current_datetime.hour % 6)
            cycle = current_datetime.hour - (current_datetime.hour % 6)

            # Format the file paths
            fcst_file = Preprocessor.format_file_template(fcst_file_template, fcst_current_datetime, fcycle)
            ref_file = Preprocessor.format_file_template(ref_file_template, current_datetime, cycle)

            ffiles.append(fcst_file)
            rfiles.append(ref_file)

        return ffiles, rfiles
