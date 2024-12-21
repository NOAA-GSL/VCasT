# Model Verification Tool (MVT)

A Python-based tool for calculating and visualizing forecast verification statistics such as RMSE, bias, quantiles, and more. This tool is designed for comparing model outputs against observations or references, supporting both GRIB2 and NetCDF file formats.

## Features

- **Supported Metrics**:
  - **RMSE (Root Mean Square Error)**: Quantifies the differences between forecast and observed values.
  - **Bias**: Measures the systematic error between forecast and observed values.
  - **Quantiles**: Computes key quantiles, IQR (Interquartile Range), and outliers.
  - **MAE (Mean Absolute Error)**: Computes the average absolute error between forecast and observed values.
  - **Gilbert Skill Score (GSS)**: Measures the skill of forecasts relative to random chance.
  - **Frequency Bias Index (FBIAS)**: Indicates whether the forecast over- or under-predicts events.
  - **POD (Probability of Detection)**: Measures the proportion of observed events correctly forecasted.
  - **FAR (False Alarm Ratio)**: Measures the proportion of forecasted events that did not occur.
  - **CSI (Critical Success Index)**: Combines hits, misses, and false alarms into a single metric.
  - **Correlation and Standard Deviation**: Useful for Taylor Diagrams.

- **File Handling**:
  - Reads **GRIB2** and **NetCDF** files.
  - Handles both surface fields (no level dimension) and level-specific fields.

- **Visualization**:
  - **Time Series**: Plots a time series for a specified metric.
  - **Performance Diagram**: Visualizes success ratio, POD, and CSI curves.
  - **Taylor Diagram**: Displays standard deviation, and correlation.

- **Parallel Processing**: Supports multiprocessing for handling large datasets.

- **Customizable Configuration**: Configure file paths, variables, metrics, and other settings via a YAML file.

## Installation

### Clone the repository

```bash
git clone https://github.com/VanderleiVargas-NOAA/ModelVerificationTool.git
```

### Install the package

```bash
cd ModelVerificationTool
pip install .
export PYTHONPATH=`pwd`:${PYTHONPATH}
```

This installs the `mvt_stat` and `mvt_plot` packages.

---

## Usage

### Command Line

#### Run Statistics Calculation

```bash
mvt_stat config/config_mvt.yaml
```

This command calculates metrics (e.g., RMSE, Bias, GSS) based on the configuration specified in the YAML file.

#### Generate Plots

```bash
mvt_plot config/config_plot.yaml
```

This command generates visualizations like Taylor and Performance Diagrams.

![Performance Diagram](https://raw.githubusercontent.com/VanderleiVargas-NOAA/ModelVerificationTool/develop/tests/examples/pd_refc.png "Performance Diagram Example")


---

## Configuration

### Example YAML Configuration for Statistics

```yaml
# Date and Time Settings
start_date: "2024-04-01_02:00:00"    # Start processing from this date
end_date: "2024-04-07_17:00:00"      # End processing on this date
interval_hours: "1"                  # Time interval for data processing in hours

# Forecast Configuration
fcst_file_template: "/path/to/forecast/forecast_{year}-{month}-{day}T{hour}:00:00.nc"
fcst_var: "WIND"                     # Variable to process in forecast files
fcst_level: 1000                     # Specific level for the variable (if applicable)
fcst_type_of_level: "level"          # Dimension name associated with levels
shift: -1                            # Apply a time shift to align with observations

# Reference Configuration
ref_file_template: "/path/to/reference/obs_{year}{month}{day}/{cycle}/hrrr.t{hour}z.wrfprsf00.grib2"
ref_var: "10si"                      # Variable to process in reference files
ref_level: 10                        # Level for the reference variable
ref_type_of_level: "heightAboveGround"  # Reference level type

# Output Configuration
output_dir: "/path/to/output_dir"    # Directory for storing output files
output_filename: "output_file.txt"   # Name of the output file

# Statistical Metrics to Compute
stat_name:
  - "rmse"
  - "bias"
  - "quantiles"
  - "mae"
  - "gss"

# Variable Threshold and Radius
var_threshold: 10                    # Threshold value for events
var_radius: 10                       # Grid influence radius (0 for no influence)

# Grid and Interpolation Settings
interpolation: false                 # Whether to interpolate to a target grid
target_grid: "fcst"                  # Target grid (e.g., forecast grid)

# Parallel Processing
processes: 200                       # Number of parallel processes
```

### Example YAML Configuration for Plots

```yaml
# Plot Configuration
plot_type: "taylor_diagram"              # Choose the type of plot (e.g., taylor_diagram, performance_diagram, time_series)
plot_title: "Taylor Diagram Example"     # Title of the plot
input_files:                             # List of files containing data for the plot
  - "output/statistics_1.csv"
  - "output/statistics_2.csv"
labels:                                  # Labels for each dataset in the plot
  - "Model 1"
  - "Model 2"
line_color:                              # Line colors for each dataset
  - "blue"
  - "red"
line_marker:                             # Marker styles for each dataset
  - "o"
  - "x"
output_filename: "taylor_diagram.png"    # File name to save the plot
```

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.
