from scipy.interpolate import griddata
import numpy as np

def interpolate_to_target_grid(src_data, src_lats, src_lons, target_lats, target_lons):
    """
    Interpolate data from a source grid (lat/lon) to a target grid (lat/lon).

    Parameters:
    - src_data (numpy.ndarray): Source data array (2D).
    - src_lats (numpy.ndarray): Source latitude array (2D).
    - src_lons (numpy.ndarray): Source longitude array (2D).
    - target_lats (numpy.ndarray): Target latitude array (1D or 2D).
    - target_lons (numpy.ndarray): Target longitude array (1D or 2D).

    Returns:
    - interpolated_data (numpy.ndarray): Interpolated data on the target grid.
    """

    # If target_lats and target_lons are 1D, create a meshgrid
    if target_lats.ndim == 1 and target_lons.ndim == 1:
        target_lon_grid, target_lat_grid = np.meshgrid(target_lons, target_lats)
    else:
        target_lat_grid, target_lon_grid = target_lats, target_lons

    # Flatten the source data
    src_points = np.column_stack((src_lats.ravel(), src_lons.ravel()))
    src_values = src_data.ravel()

    # Flatten the target grid
    target_points = np.column_stack((target_lat_grid.ravel(), target_lon_grid.ravel()))

    # Interpolate using griddata
    interpolated_flat = griddata(
        points=src_points,
        values=src_values,
        xi=target_points,
        method='linear'
    )

    mask_nan = np.isnan(interpolated_flat)
    if np.any(mask_nan):
        nearest_flat = griddata(
            points=src_points,
            values=src_values,
            xi=target_points,
            method='nearest'
        )
        interpolated_flat[mask_nan] = nearest_flat[mask_nan]

    # Reshape to match the target grid
    interpolated_data = interpolated_flat.reshape(target_lat_grid.shape)

    return interpolated_data
