import pygrib
from netCDF4 import Dataset
import yaml
import numpy as np
import os
from datetime import datetime
import csv 
import time

def print_intro():
    """
    Print an introduction to the Model Verification Tool (MVT).
    """
    print()
    print("=" * 60)
    print("Model Verification Tool (MVT)")
    print()
    print("Starting the Model Verification Tool (MVT)...")
    print("=" * 60)
    print()

def print_conclusion(start_time):
    """
    Print a conclusion message and show the time spent.

    Parameters:
    - start_time (float): The starting time of the script (use `time.time()`).
    """
    # Calculate the elapsed time
    elapsed_time = time.time() - start_time
    minutes, seconds = divmod(elapsed_time, 60)
    
    print()
    print("=" * 60)
    print("Execution Complete: Model Verification Tool (MVT)")
    print()
    print(f"Total Time Spent: {int(minutes)} minutes and {seconds:.2f} seconds.")
    print("=" * 60)


class PrepIO:
    def __init__(self, config_file):
        """
        Initialize the class with the configuration file.
        """
        self.available_vars = ["RMSE","BIAS","QUANTILES","MAE","GSS","FBIAS","POD","FAR","SR","CSI","STDEV","CORR","FSS"]

        self.config = self.read_config_file(config_file)
        self.start_date = datetime.strptime(self.config['start_date'], "%Y-%m-%d_%H:%M:%S")
        self.end_date = datetime.strptime(self.config['end_date'], "%Y-%m-%d_%H:%M:%S")
        self.interval_hours = int(self.config['interval_hours'])
        self.fcst_file_template = self.config['fcst_file_template']
        self.fcst_var = self.config['fcst_var']
        self.shift = self.config['shift']
        self.ref_file_template = self.config['ref_file_template']
        self.ref_var = self.config['ref_var']
        self.output_dir = self.config['output_dir']
        self.output_filename = self.config['output_filename']
        self.stat_name = self.config.get('stat_name', [])
        self.interpolation = self.config['interpolation']
        self.target_grid = self.config['target_grid']
        self.processes = self.config['processes']
        self.var_threshold = self.config['var_threshold']
        self.var_radius = self.config['var_radius']
        self.output_file = None      
        self.fcst_type_of_level = self.config["fcst_type_of_level"]
        self.fcst_level = self.config["fcst_level"]
        self.ref_type_of_level = self.config["ref_type_of_level"]
        self.ref_level = self.config["ref_level"]

        self.print_options()  
    
    def print_options(self):
        """
        Print the configuration options in a nicely formatted way.
        """
        print("Configuration Options:")
        print(f"  Start Date: {self.start_date}")
        print(f"  End Date: {self.end_date}")
        print(f"  Interval Hours: {self.interval_hours}")
        print(f"  Forecast File Template: {self.fcst_file_template}")
        print(f"  Forecast Variable: {self.fcst_var}")
        print(f"  Shift: {self.shift}")
        print(f"  Reference File Template: {self.ref_file_template}")
        print(f"  Reference Variable: {self.ref_var}")
        print(f"  Output Directory: {self.output_dir}")
        print(f"  Output Filename: {self.output_filename}")
        print(f"  Statistical Metrics: {', '.join(self.stat_name)}")
        print(f"  Interpolation: {self.interpolation}")
        print(f"  Target Grid: {self.target_grid}")
        print(f"  Processes: {self.processes}")
        print(f"  Variable Threshold: {self.var_threshold}")
        print(f"  Variable Radius: {self.var_radius}")

    @staticmethod
    def read_config_file(config_file):
        """
        Read the configuration file and return the parsed config as a dictionary.
        """
        with open(config_file, 'r') as file:
            return yaml.safe_load(file)

    def open_output_file(self):
        """
        Open the output file for writing.
        """
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, self.output_filename)
        self.output_file = open(output_path, 'w')
        self.writer = csv.writer(self.output_file)

        header = ["DATE"] 

        for i in self.stat_name:
            if i.upper() in self.available_vars:
                if i.upper() in "QUANTILES":
                    header += ["25p","50p","75p","IQR","LW","UW"]
                else:
                    header += [i.upper()]

        self.write_to_output_file(header)

    def write_to_output_file(self, row):
        """
        Write a row string to the output file.
        """
        if self.output_file is None:
            raise ValueError("Output file is not open. Call open_output_file() first.")
        self.writer.writerow(row)

    def close_output_file(self):
        """
        Close the output file.
        """
        if self.output_file:
            self.output_file.close()
            self.output_file = None        

def format_file_template(template, current_datetime, cycle = 0):
    """
    Replace placeholders in a file template with corresponding datetime values.

    Parameters:
    template (str): Template string with placeholders for year, month, day, hour, and minute.
    current_datetime (datetime): The datetime object to extract values from.

    Returns:
    str: Formatted file path.
    """

    replacements = {
        "year": current_datetime.year,
        "month": f"{current_datetime.month:02}",
        "day": f"{current_datetime.day:02}",
        "cycle": f"{cycle:02}",
        "hour": f"{current_datetime.hour:02}",
        "minute": f"{current_datetime.minute:02}"
    }
    return template.format(**replacements)

def identify_file_type(file_path):
    """
    Identifies whether a file is a NetCDF or GRIB2 file.

    Parameters:
    - file_path (str): Path to the file to identify.

    Returns:
    - file_type (str): 'netcdf' if the file is a NetCDF file, 'grib2' if it is a GRIB2 file, or 'unknown' otherwise.
    """
    if not os.path.exists(file_path):
        raise Exception(f"File {file_path} does not exist.")

    try:
        # Check for NetCDF format
        with Dataset(file_path, 'r') as _:
            return 'netcdf'
    except Exception:
        pass

    try:
        # Check for GRIB2 format
        with pygrib.open(file_path) as _:
            return 'grib2'
    except Exception:
        pass

    return 'unknown'

def read_input_data(input_file, var_name, type_of_level, level):
    
    if 'netcdf' in identify_file_type(input_file):
        data, lats, lons = read_netcdf(input_file, var_name, type_of_level, level)   
        stype = 'netcdf'
    elif 'grib2' in identify_file_type(input_file):
        data, lats, lons = read_grib2(input_file,var_name, type_of_level, level)
        stype = 'grib2'
    else:
        raise Exception("Error: File format unknown.")
    
    data = np.squeeze(data)
    return data, lats, lons, stype


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

def read_netcdf(netcdf_file, var_name, type_of_level, level):
    """
    Reads a NetCDF file and extracts the specified variable data along with latitude and longitude arrays.
    Handles cases where the type_of_level dimension is absent for surface fields.

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
    """
    try:
        # Open the NetCDF file
        nc = Dataset(netcdf_file, mode='r')

        # Check if the variable exists
        if var_name not in nc.variables:
            raise ValueError(f"Variable '{var_name}' not found in NetCDF file. Available variables: {list(nc.variables.keys())}")

        # Extract latitude and longitude arrays
        if 'latitude' in nc.variables:
            lats = nc.variables['latitude'][:]
        elif 'lat' in nc.variables:
            lats = nc.variables['lat'][:]
        else:
            raise ValueError("Latitude variable not found in NetCDF file.")

        if 'longitude' in nc.variables:
            lons = nc.variables['longitude'][:]
        elif 'lon' in nc.variables:
            lons = nc.variables['lon'][:]
        else:
            raise ValueError("Longitude variable not found in NetCDF file.")

        # Get the dimensions of the variable
        variable_dimensions = nc.variables[var_name].dimensions

        has_dimension = type_of_level in variable_dimensions

        if has_dimension:
            # Check if type_of_level is specified and exists in the NetCDF file
            if type_of_level and type_of_level in nc.variables:
                level_array = nc.variables[type_of_level][:]
                if level is not None:
                    # Find the index of the specified level
                    level_index = np.where(level_array == level)[0]
                    if level_index.size == 0:
                        raise ValueError(f"Level '{level}' not found in dimension '{type_of_level}'. Available levels: {level_array}")
    
                    # Extract data at the specified level
                    data = nc.variables[var_name][level_index[0], ...]
                else:
                    raise ValueError("Level must be specified for non-surface fields.")
        else:
            # Assume surface field (no level dimension)
            data = nc.variables[var_name][...]

        # Close the NetCDF file
        nc.close()

        return data, lats, lons

    except Exception as e:
        raise RuntimeError(f"Error reading NetCDF file '{netcdf_file}': {e}") from e
