from vcast.io import FileChecker
import numpy as np
import xarray as xr
from scipy.interpolate import griddata
import pygrib


def interpolate_to_target_grid(src_data, src_lats, src_lons, target_file):
    """
    Interpolate data from a source grid (lat/lon) to a target grid extracted from a 
    NetCDF file or Zarr dataset, but only perform interpolation if the target grid is 
    different from the source grid.

    Parameters:
    - src_data (numpy.ndarray): Source data array (2D).
    - src_lats (numpy.ndarray): Source latitude array (2D).
    - src_lons (numpy.ndarray): Source longitude array (2D).
    - target_file (str): Path to the file containing the target grid. If the path is a directory,
      it is assumed to be a Zarr dataset; otherwise, it is assumed to be a NetCDF file.
      The dataset is expected to have variables 'latitude' (or 'lat') and 'longitude' (or 'lon').

    Returns:
    - numpy.ndarray: Interpolated data on the target grid, or the original src_data if the 
      target grid matches the source grid.
    """

    fc = FileChecker(target_file)    

    if 'netcdf' in fc.identify_file_type():
        stype = 'netcdf'
    elif 'grib2' in fc.identify_file_type():
        stype = 'grib2'
    elif 'zarr' in fc.identify_file_type():
        stype = 'zarr'            
    else:
        raise Exception("Error: File format unknown.")    

    # Open target dataset using xarray for both NetCDF and Zarr
    if stype == 'zarr':
        ds = xr.open_zarr(target_file,decode_timedelta=True)
    elif stype == 'netcdf':
        ds = xr.open_dataset(target_file,decode_timedelta=True)    
    elif stype == 'grib2':
        ds = pygrib.open(target_file)

    if stype == "zarr" or stype == "netcdf":
        # Extract target latitude array
        if 'latitude' in ds:
            target_lats = ds['latitude'].values
        elif 'lat' in ds:
            target_lats = ds['lat'].values
        else:
            ds.close()
            raise ValueError("Latitude variable not found in target dataset.")
    
        # Extract target longitude array
        if 'longitude' in ds:
            target_lons = ds['longitude'].values
        elif 'lon' in ds:
            target_lons = ds['lon'].values
        else:
            ds.close()
            raise ValueError("Longitude variable not found in target dataset.")
    else:
        msg = ds.message(1)
        _, target_lats, target_lons = msg.data()

    # Close the dataset to free resources
    ds.close()

    # If target_lats and target_lons are 1D, create a meshgrid.
    if target_lats.ndim == 1 and target_lons.ndim == 1:
        target_lon_grid, target_lat_grid = np.meshgrid(target_lons, target_lats)
    else:
        target_lat_grid, target_lon_grid = target_lats, target_lons

    # Check if the target grid is identical to the source grid.
    if (src_lats.shape == target_lat_grid.shape and src_lons.shape == target_lon_grid.shape):
        if np.allclose(src_lats, target_lat_grid) and np.allclose(src_lons, target_lon_grid):
            # No interpolation needed; return the original data.
            return src_data

    # Flatten the source data and its coordinate arrays.
    src_points = np.column_stack((src_lats.ravel(), src_lons.ravel()))
    src_values = src_data.ravel()

    # Flatten the target grid.
    target_points = np.column_stack((target_lat_grid.ravel(), target_lon_grid.ravel()))

    # Perform interpolation using the linear method.
    interpolated_flat = griddata(
        points=src_points,
        values=src_values,
        xi=target_points,
        method='linear'
    )

    # For any points where linear interpolation returns NaN, use nearest-neighbor interpolation.
    mask_nan = np.isnan(interpolated_flat)
    if np.any(mask_nan):
        nearest_flat = griddata(
            points=src_points,
            values=src_values,
            xi=target_points,
            method='nearest'
        )
        interpolated_flat[mask_nan] = nearest_flat[mask_nan]

    # Reshape the interpolated data to match the target grid shape.
    interpolated_data = interpolated_flat.reshape(target_lat_grid.shape)

    return interpolated_data
