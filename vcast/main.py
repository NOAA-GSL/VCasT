import argparse
import sys
import os
import yaml
from colorama import Fore, Style  

from vcast.stat import ReadStat
from vcast.plot import LinePlot, Reliability, PerformanceDiagram
from vcast.processing import process_in_parallel
from vcast.io import ConfigLoader, OutputFileHandler, FileChecker


def detect_yaml_config(file_path):
    """
    Determines the appropriate module to run based on the YAML configuration content.
    
    Args:
        file_path (str): Path to the YAML file.
    
    Returns:
        str: 'convert' for statistical extraction, 'plot' for plotting, 'stats' for statistical analysis, 
             or None if the YAML format is unrecognized.
    """
    type = None

    try:
        with open(file_path, "r") as file:
            config = yaml.safe_load(file)

        if isinstance(config, dict):
            if all(key in config for key in ["input_stat_folder", "line_type", "date_column", "output_file"]):
                type = "convert"
            
            if all(key in config for key in ["plot_type", "vars", "output_filename"]):
                type = "plot"
            
            if all(key in config for key in ["stat_name", "fcst_file_template", "ref_file_template"]):
                type = "stats"
            
            if all(key in config for key in ["input_file", "group_by", "output_agg_file"]):
                type = "agg"

        return type
    except Exception as e:
        print(Fore.RED + f"Error reading YAML file: {file_path} - {e}" + Style.RESET_ALL)

    return None  # If the file doesn't match any known YAML format


def handle_file_check(file_path):
    """
    Handles file checking for NetCDF and GRIB2 formats.
    
    Args:
        file_path (str): Path to the file to check.
    """
    print(f"Checking file: {file_path}...")
    
    fc = FileChecker(file_path)
    file_type = fc.identify_file_type()

    if file_type == "netcdf":
        print(Fore.GREEN + "File Type: NetCDF" + Style.RESET_ALL)
        fc.check_netcdf()
    elif file_type == "grib2":
        print(Fore.GREEN + "File Type: GRIB2" + Style.RESET_ALL)
        fc.check_grib2()
    else:
        print(Fore.RED + "Unknown file type. Only NetCDF and GRIB2 are supported." + Style.RESET_ALL)
        sys.exit(1)

    print("\n" + "-" * 10)
    print(Fore.GREEN + "File check passed." + Style.RESET_ALL)
    print("-" * 10 + "\n")
    sys.exit(0)


def handle_conversion(config):
    """
    Handles conversion of METplus statistical files.
    
    Args:
        config (ConfigLoader): Configuration object.
    """

    print(f"Processing METplus statistics...")
    
    rs = ReadStat(config)

    rs.run_all()
    
    sys.exit(0)

def handle_plotting(config):
    """
    Handles plotting based on the YAML configuration.
    """

    print(f"Generating plot...")
    
    if config.plot_type == "line":
        plt = LinePlot(config)
    elif config.plot_type == "reliability":
        plt = Reliability(config)
    elif config.plot_type == "performance_diagram":
        plt = PerformanceDiagram(config)
    else:
        raise Exception(Fore.RED + f"ERROR: Plot type {config.plot_type} is not supported." + Style.RESET_ALL)

    plt.plot()

    sys.exit(0)

def handle_statistical_analysis(config, test):
    """
    Handles statistical analysis using multiprocessing.

    Args:
        config (ConfigLoader): Configuration object.
    """

    print(f"Running statistical analysis...")

    output = OutputFileHandler(config)
            
    process_in_parallel(output.config, output, test)

    output.close_output_file()

    sys.exit(0)

def handle_aggregation(config):

    print(f"Running aggregation...")

    rs = ReadStat(config)

    rs.run_aggregation(config.input_file)

    sys.exit(0)


def main():
    """Central command-line interface for VCasT."""
    parser = argparse.ArgumentParser(
        description="VCasT: Verification and Forecast Evaluation Tool"
    )
    
    parser.add_argument(
        "file_path",
        help=(
            "Specify the input file (YAML, NetCDF, GRIB2) for processing. "
            "The tool will automatically determine the required action."
        )
    )

    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Run the VCasT in test mode."
    )

    args = parser.parse_args()

    if not os.path.exists(args.file_path):
        raise FileNotFoundError(f"File not found: {args.file_path}")

    # **Step 1: Try detecting YAML configuration**
    action = detect_yaml_config(args.file_path)
    if action in ["convert", "plot", "stats", "agg"]:
        config = ConfigLoader(args.file_path)
        if action == "convert":        
            handle_conversion(config)
        elif action == "plot":
            handle_plotting(config)
        elif action == "stats":
            handle_statistical_analysis(config, args.test_mode)
        elif action == "agg":
            handle_aggregation(config)

    # **Step 2: If not YAML, try checking if it's NetCDF or GRIB2**
    print(f"Attempting to detect file format for: {args.file_path} ...")
    
    fc = FileChecker(args.file_path)
    file_type = fc.identify_file_type()

    if file_type == "netcdf" or file_type == "grib2":
        handle_file_check(args.file_path)

    # **Step 3: If it doesn't match anything, raise an error**
    raise Exception(f"Unrecognized file type or unsupported format: {args.file_path}")

if __name__ == "__main__":
    main()
