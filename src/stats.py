import numpy as np

def compute_rmse(forecast_values, reference_values):
    """
    Calculate the Root Mean Square Error (RMSE) between forecast values and reference values.

    Parameters:
    forecast_values (np.ndarray): Forecasted values of shape (n, m).
    reference_values (np.ndarray): Reference values of shape (n, m).

    Returns:
    float: The RMSE value.

    Raises:
    ValueError: If the shapes of the inputs do not match.
    """
    # Check if the shapes match
    if forecast_values.shape != reference_values.shape:
        raise ValueError("Forecast values and reference values must have the same shape.")

    # Calculate RMSE
    differences = forecast_values - reference_values
    squared_differences = np.square(differences)
    mean_squared_error = np.mean(squared_differences)
    rmse = np.sqrt(mean_squared_error)

    return rmse

def compute_bias(forecast_values, reference_values):
    """
    Calculate the bias between forecast values and reference values.

    Parameters:
    forecast_values (np.ndarray): Forecasted values of shape (n, m).
    reference_values (np.ndarray): Reference values of shape (n, m).

    Returns:
    float: The bias value.

    Raises:
    ValueError: If the shapes of the inputs do not match.
    """
    # Check if the shapes match
    if forecast_values.shape != reference_values.shape:
        raise ValueError("Forecast values and reference values must have the same shape.")

    # Calculate bias
    differences = forecast_values - reference_values
    bias = np.mean(differences)

    return bias

