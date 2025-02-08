import argparse
import sys
import os
import yaml
from vcast.stat_handler import *
from vcast.file_handler import *
from colorama import Fore, Style  
from vcast.plot_class import *
from vcast.ioc import *
from vcast.parallel import *
import time

def detect_yaml_config(file_path):
    """
    Determines the appropriate module to run based on the YAML configuration.
    
    Parameters:
        file_path (str): Path to the YAML file.
    
    Returns:
        str: 'convert' for main_conv, 'plot' for main_plot, 'stats' for main_stat, otherwise None.
    """
    try:
        with open(file_path, "r") as file:
            config = yaml.safe_load(file)

        # If it contains statistical processing elements, assume it's for conversion
        required_keys_for_conversion = ["input_stat_folder", "line_type", "date_column", "output_file"]
        if all(key in config for key in required_keys_for_conversion):
            return "convert"

        # If it contains plotting parameters, assume it's for plotting
        required_keys_for_plot = ["plot_type", "vars", "output_filename"]
        if all(key in config for key in required_keys_for_plot):
            return "plot"

        # If it contains statistical metric calculations, assume it's for main_stat
        required_keys_for_stats = ["stat_name", "fcst_file_template", "ref_file_template"]
        if all(key in config for key in required_keys_for_stats):
            return "stats"

    except:
        return None

def main():
    """Central command-line interface for VCasT."""
    parser = argparse.ArgumentParser(
        description="VCasT: Verification and Forecast Evaluation Tool"
    )
    
    parser.add_argument(
        "command_or_file",
        help=(
            "Specify the operation (plot, convert, stats, check) or provide a file "
            "(NetCDF, GRIB2, YAML) for automatic detection."
        )
    )

    parser.add_argument(
        "config",
        type=str,
        nargs="?",  # Make this optional in case of direct file input
        help="Path to the YAML configuration file (not needed for direct file check)."
    )

    args = parser.parse_args()

    # Check if the argument is a file
    if os.path.isfile(args.command_or_file):
        file_extension = os.path.splitext(args.command_or_file)[1].lower()

        # If it's a NetCDF or GRIB2 file → Run `main_check.py`
        if file_extension in [".nc", ".grib2"]:
            print(f"Detected file '{args.command_or_file}' - Running check...")
            file_type = identify_file_type(args.command_or_file)
    
            print()
            if file_type == "netcdf":
                print("File type: NetCDF")
                check_netcdf(args.command_or_file)
            elif file_type == "grib2":
                print("File type: GRIB2")
                check_grib2(args.command_or_file)
            else:
                print(Fore.RED + "Unknown file type. Only NetCDF and GRIB2 are supported." + Style.RESET_ALL)
            
            print()
            print("-"*10)
            print(Fore.GREEN + "File passed check." + Style.RESET_ALL)
            print("-"*10)
        
            print()
            sys.exit(0)

        # If it's a YAML file → Check for conversion, plotting, or statistics
        elif file_extension in [".yaml", ".yml"]:
            action = detect_yaml_config(args.command_or_file)
            if action == "convert":
                print(f"Detected YAML configuration for METplus stat file - Extracting statistics...")
                ReadStat(args.command_or_file)
                sys.exit(0)
            elif action == "plot":
                print(f"Detected YAML configuration for plotting - Plotting...")
                plot = Plot(args.command_or_file)
                plot.plot()
                sys.exit(0)
            elif action == "stats":
                print(f"Detected YAML configuration for statistical analysis - Running statistical analysis...")
                start_time = time.time()
  
                print_intro()
            
                config = PrepIO(args.command_or_file)
            
                dates = dates_to_list(config.start_date, config.end_date,config.interval_hours)
                fcst_files, ref_files = files_to_list(config.fcst_file_template, config.ref_file_template, dates, config.shift)
                
                config.open_output_file()
            
                process_in_parallel(dates, fcst_files, ref_files, config)
            
                config.close_output_file()
            
                print_conclusion(start_time)
                sys.exit(0)

        else:
            raise Exception(f"Unrecognized file type or unsupported YAML format: {args.command_or_file}")

    else:
        raise Exception(f"File not found: {args.command_or_file}")


if __name__ == "__main__":
    main()
