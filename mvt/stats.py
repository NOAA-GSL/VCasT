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
    """
    Compute Mean Absolute Error (MAE) between forecast and reference values.

    Parameters:
    - forecast_values (numpy.ndarray): Array of forecasted values.
    - reference_values (numpy.ndarray): Array of observed/reference values.

    Returns:
    - float: The Mean Absolute Error (MAE), which is the average of the absolute differences 
             between forecasted and observed values.
    """

    # Calculate the absolute differences and compute their mean
    return np.mean(np.abs(forecast_values - reference_values))


def compute_scores(fcst_data, ref_data, var_threshold, radius=None):
    """
    Calculate hits, misses, false alarms, and correct rejections based on forecast and reference data.
    Handles both local grid point comparisons and grid radius of influence.

    Parameters:
    fcst_data (np.ndarray): Forecasted values as a 2D grid (n, m).
    ref_data (np.ndarray): Reference values as a 2D grid (n, m).
    var_threshold (float): Threshold above which events are considered significant.
    radius (int, optional): If None, only local grid points are considered. Otherwise, radius is the
                            number of grid points to consider around each grid point of interest.

    Returns:
    tuple: (hits, misses, false_alarms, correct_rejections, total_events)
    """
    # Ensure forecast and reference grids are the same shape
    if fcst_data.shape != ref_data.shape:
        raise ValueError("Forecast and reference grids must have the same shape.")
    
    # Logical masks for significant events
    fcst_mask = fcst_data >= var_threshold
    ref_mask = ref_data >= var_threshold

    if radius == 0:
        # Local grid point calculation
        hits = np.sum(fcst_mask & ref_mask)                   # Both forecast and reference detect an event
        misses = np.sum(~fcst_mask & ref_mask)                # Reference detects an event, forecast does not
        false_alarms = np.sum(fcst_mask & ~ref_mask)          # Forecast detects an event, reference does not
        correct_rejections = np.sum(~fcst_mask & ~ref_mask)   # Neither detect an event
    else:
        # Radius of influence calculation
        n, m = fcst_data.shape
        hits = 0
        misses = 0
        false_alarms = 0
        correct_rejections = 0

        # Iterate through each grid point
        for i in range(n):
            for j in range(m):
                # Define the neighborhood bounds (clipping at grid edges)
                i_min = max(0, i - radius)
                i_max = min(n, i + radius + 1)
                j_min = max(0, j - radius)
                j_max = min(m, j + radius + 1)

                # Extract the neighborhood masks
                fcst_neighborhood = fcst_mask[i_min:i_max, j_min:j_max]
                ref_neighborhood = ref_mask[i_min:i_max, j_min:j_max]

                # Check for hits, misses, false alarms, or correct rejections
                if ref_mask[i, j]:  # Reference event exists at this point
                    if np.any(fcst_neighborhood):  # Any forecast in the neighborhood
                        hits += 1
                    else:
                        misses += 1
                else:  # No reference event at this point
                    if np.any(fcst_neighborhood):  # Forecast in the neighborhood but no reference
                        false_alarms += 1
                    else:
                        correct_rejections += 1

    # Total events
    total_events = hits + misses + false_alarms + correct_rejections

    return hits, misses, false_alarms, correct_rejections, total_events

def compute_gss(hits, misses, false_alarms, total_events):
    """
    Calculate the Gilbert Skill Score (GSS) using the input scores.

    Parameters:
    hits (int): Number of correctly forecast events.
    misses (int): Number of events that occurred but were not forecast.
    false_alarms (int): Number of forecast events that did not occur.
    total_events (int): Total number of events (hits + misses + false alarms + correct rejections).

    Returns:
    float: The Gilbert Skill Score (GSS).
    """
    # Calculate expected hits due to random chance
    expected_hits = ((hits + false_alarms) * (hits + misses)) / total_events

    # Calculate GSS
    if (hits + misses + false_alarms - expected_hits) != 0:
        gss = (hits - expected_hits) / (hits + misses + false_alarms - expected_hits)
    else:
        gss = 0.0  # Avoid division by zero
    
    return gss

def calculate_fbias(hits, false_alarms, misses):
    """
    Calculate the Frequency Bias Index (FBIAS).

    Parameters:
    - hits (int): Number of correctly forecasted events.
    - false_alarms (int): Number of forecasted events that did not occur.
    - misses (int): Number of events that occurred but were not forecasted.

    Returns:
    - float: Frequency Bias Index (FBIAS).

    Raises:
    - ValueError: If there are no observed events (hits + misses = 0).
    """
    # Denominator: Total observed events
    observed_events = hits + misses
    if observed_events == 0:
        return np.nan

    # Numerator: Total forecasted events
    forecasted_events = hits + false_alarms

    # Calculate FBIAS
    fbias = forecasted_events / observed_events

    return fbias

def compute_pod(hits, misses):
    """
    Compute Probability of Detection (POD).

    Parameters:
    - hits (int): Number of correctly forecasted events.
    - misses (int): Number of observed events that were missed.

    Returns:
    - float: Probability of Detection (POD).

    Raises:
    - ValueError: If there are no observed events (hits + misses = 0).
    """
    observed_events = hits + misses
    if observed_events == 0:
        return np.nan

    pod = hits / observed_events
    return pod


def compute_far(hits, false_alarms):
    """
    Compute False Alarm Ratio (FAR).

    Parameters:
    - hits (int): Number of correctly forecasted events.
    - false_alarms (int): Number of forecasted events that did not occur.

    Returns:
    - float: False Alarm Ratio (FAR).

    Raises:
    - ValueError: If there are no forecasted events (hits + false_alarms = 0).
    """
    forecasted_events = hits + false_alarms
    if forecasted_events == 0:
        return np.nan

    far = false_alarms / forecasted_events
    return far

def compute_success_ratio(hits, false_alarms):
    """
    Compute the Success Ratio (SR), also known as Precision.

    Parameters:
    - hits (int): Number of correctly forecasted events.
    - false_alarms (int): Number of forecasted events that did not occur.

    Returns:
    - float: Success Ratio (SR).
    """
    # Compute Success Ratio
    sr = 1 - compute_far(hits, false_alarms)

    return sr

def compute_csi(hits, misses, false_alarms):
    """
    Compute the Critical Success Index (CSI), also known as the Threat Score.

    Parameters:
    - hits (int): Number of correctly forecasted events.
    - misses (int): Number of observed events that were not forecasted.
    - false_alarms (int): Number of forecasted events that did not occur.

    Returns:
    - float: Critical Success Index (CSI).

    Raises:
    - ValueError: If there are no forecasted or observed events (hits + misses + false_alarms = 0).
    """
    total_events = hits + misses + false_alarms
    if total_events == 0:
        return np.nan

    # Compute CSI
    csi = hits / total_events
    return csi

def compute_correlation(forecast_values, reference_values):
    """
    Compute the Pearson correlation coefficient between forecast and reference values.

    Parameters:
    forecast_values (np.ndarray): Forecasted values of shape (n, m) or (n,).
    reference_values (np.ndarray): Reference values of shape (n, m) or (n,).

    Returns:
    float: Pearson correlation coefficient between forecast and reference values.

    Raises:
    ValueError: If the shapes of the inputs do not match.
    """
    # Ensure the inputs are numpy arrays
    forecast_values = np.asarray(forecast_values)
    reference_values = np.asarray(reference_values)

    # Check if the shapes match
    if forecast_values.shape != reference_values.shape:
        raise ValueError("Forecast values and reference values must have the same shape.")

    # Flatten the arrays in case they are 2D
    forecast_values = forecast_values.ravel()
    reference_values = reference_values.ravel()

    # Compute and return the Pearson correlation coefficient
    return np.corrcoef(forecast_values, reference_values)[0, 1]

def compute_stdev(forecast_values, reference_values):
    """
    Compute the standard deviation of forecast values relative to the reference values.

    Parameters:
    forecast_values (np.ndarray): Forecasted values of shape (n, m) or (n,).
    reference_values (np.ndarray): Reference values of shape (n, m) or (n,).

    Returns:
    float: Standard deviation of the forecast values.

    Raises:
    ValueError: If the shapes of the inputs do not match.
    """
    # Ensure the inputs are numpy arrays
    forecast_values = np.asarray(forecast_values)
    reference_values = np.asarray(reference_values)

    # Check if the shapes match
    if forecast_values.shape != reference_values.shape:
        raise ValueError("Forecast values and reference values must have the same shape.")

    # Compute and return the standard deviation of forecast values
    return np.std(forecast_values)
