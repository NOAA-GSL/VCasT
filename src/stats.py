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

def compute_quantiles(forecast_values, reference_values):
    """
    Calculate key quantiles, interquartile range (IQR), and identify outliers in the data.

    Parameters:
    forecast_values (np.ndarray): Forecasted values of shape (n, m).
    reference_values (np.ndarray): Reference values of shape (n, m).

    Returns:
    dict: A dictionary containing Q1 (25th percentile), Q2 (median), Q3 (75th percentile),
          IQR, lower and upper whisker limits, and outliers.
    """
    # Check if the shapes match
    if forecast_values.shape != reference_values.shape:
        raise ValueError("Forecast values and reference values must have the same shape.")
    
    data = forecast_values - reference_values

    # Flatten data in case it's a 2D array
    data = np.ma.masked_invalid(data).compressed()  # Mask NaNs and infinities, then flatten

    # Calculate quantiles
    Q1 = np.percentile(data, 25)  # 25th percentile
    Q2 = np.percentile(data, 50)  # Median (50th percentile)
    Q3 = np.percentile(data, 75)  # 75th percentile

    # Calculate IQR
    IQR = Q3 - Q1

    # Determine whisker limits (1.5 * IQR)
    lower_whisker = Q1 - 1.5 * IQR
    upper_whisker = Q3 + 1.5 * IQR

    # Identify outliers
    outliers = data[(data < lower_whisker) | (data > upper_whisker)]

    # Results in a dictionary
    # quantile_results = {
    #     "Q1 (25th Percentile)": Q1,
    #     "Q2 (Median)": Q2,
    #     "Q3 (75th Percentile)": Q3,
    #     "IQR": IQR,
    #     "Lower Whisker": lower_whisker,
    #     "Upper Whisker": upper_whisker,
    #     "Outliers": outliers
    # }

    quantile_results = [Q1,Q2,Q3,IQR,lower_whisker,upper_whisker]

    return quantile_results

def compute_mae(forecast_values, reference_values):
    return np.mean(np.abs(forecast_values - reference_values))

