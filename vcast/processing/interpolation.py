from scipy.interpolate import griddata
import numpy as np
from netCDF4 import Dataset

def interpolate_to_target_grid(src_data, src_lats, src_lons, target_nc_file):
    """
    Interpolate data from a source grid (lat/lon) to a target grid extracted from a NetCDF file,
    but only perform interpolation if the target grid is different from the source grid.

    Parameters:
    - src_data (numpy.ndarray): Source data array (2D).
    - src_lats (numpy.ndarray): Source latitude array (2D).
    - src_lons (numpy.ndarray): Source longitude array (2D).
    - target_nc_file (str): Path to the NetCDF file containing the target grid. Assumes the file 
      has variables 'lat' and 'lon'.

    Returns:
    - numpy.ndarray: Interpolated data on the target grid, or the original src_data if the target 
      grid matches the source grid.
    """

    # Open the NetCDF file and extract target latitude and longitude arrays.
    with Dataset(target_nc_file, mode='r') as ds:
        target_lats = ds.variables['latitude'][:]
        target_lons = ds.variables['longitude'][:]

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

    # Interpolate using linear method.
    interpolated_flat = griddata(
        points=src_points,
        values=src_values,
        xi=target_points,
        method='linear'
    )

    # For any points where linear interpolation fails (NaN), use nearest-neighbor.
    mask_nan = np.isnan(interpolated_flat)
    if np.any(mask_nan):
        nearest_flat = griddata(
            points=src_points,
            values=src_values,
            xi=target_points,
            method='nearest'
        )
        interpolated_flat[mask_nan] = nearest_flat[mask_nan]

    # Reshape to the shape of the target grid.
    interpolated_data = interpolated_flat.reshape(target_lat_grid.shape)

    return interpolated_data
