# VCasT: Verification and Forecast Evaluation Tool

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

VCasT (Verification and Forecast Evaluation Tool) is a library designed for weather model verification, providing tools for:

- **Statistical processing**: Compute RMSE, MAE, correlation coefficients, and more.
- **Data handling and preprocessing**: Read, process, and format data efficiently.
- **Parallel computation**: Speed up analysis with multiprocessing capabilities.
- **Plot generation for visualization**: Create performance and Taylor diagrams.

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
  - **Correlation (CORR) and Standard Deviation (STDEV)**: Useful for Taylor Diagrams.
  - **Fractions Skill Score (FSS)**: Evaluates spatial forecasts by comparing fractions of grid points exceeding a threshold within a specified neighborhood.

- **File Handling**:
  - Reads **GRIB2** and **NetCDF** files.
  - Handles both surface fields (no level dimension) and level-specific fields.

- **Visualization**:
  - **Time Series**: Plots a time series for a specified metric.
  - **Performance Diagram**: Visualizes success ratio, POD, and CSI curves.
  - **Taylor Diagram**: Displays standard deviation, and correlation.

## Modules

- `io`: Handles input/output operations, config loading, and file checks.
- `plot`: Implements plotting functions including performance and Taylor diagrams.
- `processing`: Contains interpolation and parallel data processing.
- `stat`: Provides statistical calculations and data aggregation.

## Installation

To install VCasT, use:

```bash
git clone git@github.com:VanderleiVargas-NOAA/VCasT.git
cd VCasT
pip install .
export ${PYTHONPATH}:`pwd`
```

## Usage

VCasT determines the required action based on the structure of the provided configuration file. The main actions include:

- **File Checking**: Detects file type (NetCDF or GRIB2) and verifies compatibility.
- **Statistical Extraction**: Extracts and processes statistical data from METplus stat files.
- **Plotting**: Generates visualizations such as line plots based on configuration.
- **Statistical Analysis**: Performs parallelized statistical computations on forecast data.

VCasT operates via command-line interface:

```bash
vcast config_file
```
The action taken depends on the structure of the specified configuration file.

## Project Structure

```
VCasT/
│── config/          # Configuration files
│── tests/           # Unit tests
│── util/            # Utility functions
│── vcast/           # Core library files
│── .gitignore       # Git ignore rules
│── LICENSE          # License information
│── README.md        # Project documentation
│── requirements.txt # Dependencies
│── setup.py         # Package installation script
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a new branch (`git checkout -b feature-branch`)
3. Commit your changes (`git commit -m "Add feature"`)
4. Push to the branch (`git push origin feature-branch`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

