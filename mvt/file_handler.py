import pygrib
from netCDF4 import Dataset
import os
import warnings
from colorama import Fore, Style

def check_grib2(file_path):
    """
    Performs checks and extracts details for a GRIB2 file.
    """
    with pygrib.open(file_path) as grib_file:
        print("GRIB2 Messages:")
        time_dim_checked = False

        for grib_msg in grib_file:
            # Extract metadata
            name = grib_msg.name
            short_name = grib_msg.shortName
            dimensions = grib_msg.values.shape  # Dimensions as a tuple (e.g., (lat, lon))
            num_dims = len(dimensions)
            level_type = grib_msg.typeOfLevel if hasattr(grib_msg, 'typeOfLevel') else "Unknown"

            # Validate time dimension (if not checked already)
            if not time_dim_checked:
                time_dim_checked = True
                time_dim = getattr(grib_msg, 'dataDate', None)
                if time_dim is not None and isinstance(time_dim, list) and len(time_dim) > 1:
                    print(Fore.RED + "Warning: GRIB2 file contains multiple time steps. Expected one." + Style.RESET_ALL)

            # Print the variable information
            if num_dims <= 4:
                print(Fore.GREEN + f"  {name} ({short_name}): {dimensions}, Level: {level_type}" + Style.RESET_ALL)
            else:
                print(Fore.RED + f"  {name} ({short_name}): {dimensions}, Level: {level_type} - Too many dimensions!" + Style.RESET_ALL)


def check_netcdf(file_path):
    """
    Performs checks and extracts details for a NetCDF file.
    """
    with Dataset(file_path, "r") as nc_file:
        dimensions = nc_file.dimensions
        variables = nc_file.variables

        # Check for latitude and longitude dimensions
        lat_keys = [dim for dim in dimensions if dim.lower() in ['lat', 'latitude']]
        lon_keys = [dim for dim in dimensions if dim.lower() in ['lon', 'longitude']]
        level_keys = [dim for dim in dimensions if 'level' in dim.lower()]
        time_keys = [dim for dim in dimensions if dim.lower() == 'time']

        if not lat_keys or not lon_keys:
            raise ValueError("The file does not contain required latitude and longitude dimensions.")

        if not level_keys:
            warnings.warn("The file does not contain a level dimension. It might contain surface fields.")

        # Ensure the time dimension (if present) has size one
        if time_keys:
            time_dim = dimensions[time_keys[0]]
            if len(time_dim) != 1:
                raise ValueError(f"The time dimension '{time_keys[0]}' must have size 1, but it has size {len(time_dim)}.")

        # Print dimensions and sizes
        print("Dimensions:")
        for dim_name, dim in dimensions.items():
            print(f"  {dim_name}: {len(dim)}")

        # Print variables
        print("\nVariables:")
        for var_name, var in variables.items():
            num_dims = len(var.dimensions)
            if num_dims <= 4:
                print(Fore.GREEN + f"  {var_name}: {var.dimensions} ({var.dtype})" + Style.RESET_ALL)
            else:
                print(Fore.RED + f"  {var_name}: {var.dimensions} ({var.dtype}) - Too many dimensions!" + Style.RESET_ALL)



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