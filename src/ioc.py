import pygrib
from netCDF4 import Dataset
import yaml
import numpy as np
import os
from datetime import datetime
import csv 

class PrepIO:
    def __init__(self, config_file):
        """
        Initialize the class with the configuration file.
        """
        self.config = self.read_config_file(config_file)
        self.start_date = datetime.strptime(self.config['start_date'], "%Y-%m-%d_%H:%M:%S")
        self.end_date = datetime.strptime(self.config['end_date'], "%Y-%m-%d_%H:%M:%S")
        self.interval_hours = int(self.config['interval_hours'])
        self.fcst_file_template = self.config['fcst_file_template']
        self.fcst_var = self.config['fcst_var']
        self.ref_file_template = self.config['ref_file_template']
        self.ref_var = self.config['ref_var']
        self.output_dir = self.config['output_dir']
        self.output_filename = self.config['output_filename']
        self.stat_name = self.config.get('stat_name', [])
        self.target_grid = self.config['target_grid']
        self.processes = self.config['processes']
        self.output_file = None        


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
            if "RMSE" in i.upper():
                header += ["RMSE"]
            elif "BIAS" in i.upper():
                header += ["BIAS"]
            elif "QUANTILES" in i.upper():
                header += ["25p","50p","75p","IQR","LW","UW"]
            elif "MAE" in i.upper():
                header += ["MAE"]
          
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

def read_input_data(input_file, var_name):
    
    if 'netcdf' in identify_file_type(input_file):
        data, lats, lons = read_netcdf(input_file,var_name)    
        stype = 'netcdf'
    elif 'grib2' in identify_file_type(input_file):
        data, lats, lons = read_grib2(input_file,var_name)
        stype = 'grib2'
    else:
        raise Exception("Error: File format unknown.")
    
    data = np.squeeze(data)
    return data, lats, lons, stype

def read_grib2(grib2_file, var_name):
    """
    Reads a GRIB2 file and extracts the specified variable data along with latitude and longitude arrays.
    Specifically filters for `TMP` at `surface` level and `anl` type.

    Parameters:
    - grib2_file (str): Path to the GRIB2 file.
    - var_name (str): Name of the variable to extract (e.g., "TMP").

    Returns:
    - data (numpy.ndarray): Variable data array.
    - lats (numpy.ndarray): Latitude array.
    - lons (numpy.ndarray): Longitude array.
    """
    try:
        # Open the GRIB2 file
        grbs = pygrib.open(grib2_file)

        # Filter the GRIB message for the specified variable, level, and type
        grb = None
        if var_name == "t":
            grb = grbs.select(shortName=var_name, level=0)[0]
        else:
            # Default to selecting by shortName only for other variables
            grb = grbs.select(shortName=var_name)[0]

        # Extract the data, latitude, and longitude
        data = grb.values
        lats, lons = grb.latlons()

        grbs.close()
        return data, lats, lons
    except Exception as e:
        print(f"Error reading GRIB2 file with pygrib: {e}")
        return None, None, None

def read_netcdf(netcdf_file, var_name):
    """
    Reads a NetCDF file and extracts the specified variable data along with latitude and longitude arrays.

    Parameters:
    - netcdf_file (str): Path to the NetCDF file.
    - var_name (str): Name of the variable to extract.

    Returns:
    - data (numpy.ndarray): Variable data array.
    - lats (numpy.ndarray): Latitude array.
    - lons (numpy.ndarray): Longitude array.
    """
    try:
        # Open the NetCDF file
        nc = Dataset(netcdf_file, mode='r')
        
        # Extract the variable data
        if var_name not in nc.variables:
            print(f"Variable '{var_name}' not found in NetCDF file.")
            print(f"Available variables: {list(nc.variables.keys())}")
            return None, None, None

        data = nc.variables[var_name][:]  # Extract the variable's data array
        
        # Extract latitude and longitude arrays
        if 'latitude' in nc.variables:
            lats = nc.variables['latitude'][:]
        elif 'lat' in nc.variables:
            lats = nc.variables['lat'][:]
        else:
            print("Latitude variable not found in NetCDF file.")
            return None, None, None
        
        if 'longitude' in nc.variables:
            lons = nc.variables['longitude'][:]
        elif 'lon' in nc.variables:
            lons = nc.variables['lon'][:]
        else:
            print("Longitude variable not found in NetCDF file.")
            return None, None, None
        
        # Close the NetCDF file
        nc.close()
        
        return data, lats, lons

    except Exception as e:
        print(f"Error reading NetCDF file: {e}")
        return None, None, None