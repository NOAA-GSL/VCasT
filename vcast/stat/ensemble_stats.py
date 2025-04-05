import numpy as np
from scipy.signal import convolve2d

def compute_reliability(ensemble, obs, threshold, n_bins=10):
    """
    Compute reliability curve for ensemble reflectivity forecasts.

    Parameters:
        ensemble (ndarray): shape (n_members, H, W), raw reflectivity values.
        obs (ndarray): shape (H, W), observed reflectivity.
        threshold (float): Threshold for defining an event (e.g., 40 dBZ).
        n_bins (int): Number of probability bins for the reliability curve.

    Returns:
        bin_centers, observed_frequencies, counts
    """
    # Step 1: Convert ensemble to binary (event occurrence)
    binary_ensemble = (ensemble >= threshold).astype(int)  # shape: (10, H, W)

    # Step 2: Compute ensemble probability forecast at each grid point
    forecast_prob = np.mean(binary_ensemble, axis=0)  # shape: (H, W)

    # Step 3: Convert observed reflectivity to binary
    obs_binary = (obs >= threshold).astype(int)  # shape: (H, W)

    # Step 4: Flatten for binning
    probs_flat = forecast_prob.ravel()
    obs_flat = obs_binary.ravel()

    # Step 5: Bin forecast probabilities
    bins = np.linspace(0, 1, n_bins + 1)
    bin_centers = (bins[:-1] + bins[1:]) / 2
    observed_freqs = np.zeros(n_bins)
    counts = np.zeros(n_bins)

    for i in range(n_bins):
        mask = (probs_flat >= bins[i]) & (probs_flat < bins[i + 1])
        counts[i] = np.sum(mask)
        if counts[i] > 0:
            observed_freqs[i] = np.mean(obs_flat[mask])
        else:
            observed_freqs[i] = np.nan  # or 0

    return bin_centers, observed_freqs, counts

def compute_fss_ensemble(forecast_values, reference_values, threshold, window_size):
    """
    Compute the Fractions Skill Score (FSS) for spatial forecasts.
    This version is adapted to handle both deterministic forecasts (2D array)
    and ensemble forecasts (3D array: n_members x n x m).
    
    For ensemble forecasts, the ensemble probability field is computed as the 
    fraction of ensemble members that exceed the threshold.
    
    Parameters:
        forecast_values (np.ndarray): 
            Deterministic: Forecast values of shape (n, m).
            Ensemble: Forecast values of shape (n_members, n, m).
        reference_values (np.ndarray): Observed values of shape (n, m).
        threshold (float): The threshold above which an event is defined (e.g., 40 dBZ).
        window_size (int): Size of the window for fraction computation (e.g., 5 for a 5x5 grid box).
    
    Returns:
        float: The computed FSS value.
    
    Raises:
        ValueError: If the shapes of the inputs do not match (after ensemble reduction) 
                    or if the window size is invalid.
    """

    # Check for ensemble input: if forecast_values is 3D, compute ensemble probability.
    if forecast_values.ndim == 3:
        # Compute the ensemble probability field: average over the ensemble members.
        fcst_binary = (forecast_values >= threshold).astype(float)
        forecast_prob = np.mean(fcst_binary, axis=0)
    elif forecast_values.ndim == 2:
        forecast_prob = (forecast_values >= threshold).astype(float)
    else:
        raise ValueError("Forecast values must be a 2D (deterministic) or 3D (ensemble) array.")
    

    # Ensure reference field is binary.
    if reference_values.shape != forecast_prob.shape:
        raise ValueError("Reference values and forecast values (after ensemble reduction) must have the same shape.")
    ref_binary = (reference_values >= threshold).astype(float)
    
    # If neither field contains events, FSS cannot be computed.
    if not (np.any(forecast_prob) or np.any(ref_binary)):
        return np.nan
    
    if window_size <= 0:
        raise ValueError("Window size must be greater than zero.")
    
    # Define the kernel for neighborhood averaging.
    kernel = np.ones((window_size, window_size), dtype=float)
    
    # Compute the fraction of event occurrence in the neighborhood using 2D convolution.
    fcst_fractions = convolve2d(forecast_prob, kernel, mode='same', boundary='fill', fillvalue=0)
    ref_fractions = convolve2d(ref_binary, kernel, mode='same', boundary='fill', fillvalue=0)
    
    # Normalize the fractions by the area of the kernel.
    kernel_area = window_size ** 2
    fcst_fractions /= kernel_area
    ref_fractions /= kernel_area
    
    # Calculate the mean square error (MSE) between the forecast and reference fractions.
    mse_fractions = np.mean((fcst_fractions - ref_fractions) ** 2)
    
    # Compute the reference MSE (the worst-case scenario).
    ref_mse = np.mean(fcst_fractions ** 2) + np.mean(ref_fractions ** 2)
    if ref_mse == 0:
        return np.nan
    
    # Compute FSS: 1 indicates perfect skill, 0 indicates no skill.
    fss = 1 - mse_fractions / ref_mse
    return fss