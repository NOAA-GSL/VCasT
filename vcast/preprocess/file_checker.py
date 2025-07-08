import os
import warnings
import pygrib
from netCDF4 import Dataset
from colorama import Fore, Style
import xarray as xr

class FileChecker:
    """
    Handles detection and validation of NetCDF and GRIB2 files.
    """

    def __init__(self, file_path):
        """
        Initialize with file path and determine the file type.
        """
        self.file_path = file_path
        self.file_type = self.identify_file_type()

    def identify_file_type(self):
        """
        Determines whether the file is NetCDF, GRIB2, or Zarr.
    
        Returns:
            str: 'netcdf', 'grib2', 'zarr', or 'unknown'
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File {self.file_path} does not exist.")
    
        # If the path is a directory, attempt to open it as a Zarr dataset.

        if os.path.isdir(self.file_path):
            try:
                ds = xr.open_zarr(self.file_path,decode_timedelta=True)
                ds.close()
                return 'zarr'
            except Exception:
                # If opening as Zarr fails, continue checking other formats.
                pass
    
        # Try opening as NetCDF
        try:
            with Dataset(self.file_path, 'r'):
                return 'netcdf'
        except Exception:
            pass
    
        # Try opening as GRIB2
        try:
            with pygrib.open(self.file_path):
                return 'grib2'
        except Exception:
            pass

        return 'unknown'

    def check_file(self):
        """
        Runs appropriate validation based on file type.
        """
        if self.file_type == "netcdf":
            self.check_netcdf()
        elif self.file_type == "grib2":
            self.check_grib2()
        else:
            print(Fore.RED + "Unsupported file type. Cannot check." + Style.RESET_ALL)

    def check_netcdf(self):
        """
        Performs checks and extracts details for a NetCDF file.
        """
        print(Fore.BLUE + f"Checking NetCDF file: {self.file_path}" + Style.RESET_ALL)
        with Dataset(self.file_path, "r") as nc_file:
            dimensions = nc_file.dimensions
            variables = nc_file.variables

            lat_keys = [dim for dim in dimensions if dim.lower() in ['lat', 'latitude']]
            lon_keys = [dim for dim in dimensions if dim.lower() in ['lon', 'longitude']]
            level_keys = [dim for dim in dimensions if 'level' in dim.lower()]
            time_keys = [dim for dim in dimensions if dim.lower() == 'time']

            if not lat_keys or not lon_keys:
                raise ValueError("Missing latitude or longitude dimensions.")

            if not level_keys:
                warnings.warn("Missing level dimension. Only surface fields may be available.")

            if time_keys:
                time_dim = dimensions[time_keys[0]]
                if len(time_dim) != 1:
                    raise ValueError(f"Time dimension '{time_keys[0]}' must have size 1, found {len(time_dim)}.")

            print(Fore.YELLOW + "Dimensions:" + Style.RESET_ALL)
            for dim_name, dim in dimensions.items():
                print(f"  {dim_name}: {len(dim)}")

            print(Fore.GREEN + "\nVariables:" + Style.RESET_ALL)
            for var_name, var in variables.items():
                num_dims = len(var.dimensions)
                color = Fore.GREEN if num_dims <= 4 else Fore.RED
                print(color + f"  {var_name}: {var.dimensions} ({var.dtype})" + Style.RESET_ALL)

    def check_grib2(self):
        """
        Performs checks and extracts details for a GRIB2 file.
        """
        print(Fore.BLUE + f"Checking GRIB2 file: {self.file_path}" + Style.RESET_ALL)
        with pygrib.open(self.file_path) as grib_file:
            seen_variables = set()
            time_dim_checked = False

            for grib_msg in grib_file:
                name = grib_msg.name
                short_name = grib_msg.shortName
                level_type = getattr(grib_msg, 'typeOfLevel', "Unknown")
                dimensions = grib_msg.values.shape

                variable_key = (short_name, level_type)
                if variable_key in seen_variables:
                    continue
                seen_variables.add(variable_key)

                if not time_dim_checked:
                    time_dim_checked = True
                    time_dim = getattr(grib_msg, 'dataDate', None)
                    if isinstance(time_dim, list) and len(time_dim) > 1:
                        print(Fore.RED + "Warning: Multiple time steps detected!" + Style.RESET_ALL)

                color = Fore.GREEN if len(dimensions) <= 4 else Fore.RED
                print(color + f"  {name} ({short_name}): {dimensions}, Level: {level_type}" + Style.RESET_ALL)
