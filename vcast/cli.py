import argparse
import sys
import os
import yaml
from colorama import Fore, Style  

from vcast.metstat import ReadStat
from vcast.agg import Aggregation
from vcast.plot import LinePlot, Reliability, PerformanceDiagram, Roc
from vcast.io import ConfigLoader

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

            if all(key in config for key in ["input_model_A", "input_model_B", "output_file"]):
                type = "sig"

        return type
    except Exception as e:
        print(Fore.RED + f"Error reading YAML file: {file_path} - {e}" + Style.RESET_ALL)

    return None  # If the file doesn't match any known YAML format

def handle_conversion(config):
    """
    Handles conversion of METplus statistical files.
    
    Args:
        config (ConfigLoader): Configuration object.
    """

    print(f"Processing METplus statistics...")
    
    rs = ReadStat(config)

    df, add_columns, svars = rs.run_all()

    if hasattr(config,'aggregate'):
        if config.aggregate:
            
            if config.line_type.lower() == "ecnt" and "ratio" in add_columns:
                    df['ratio'] = df['spread_plus_oerr'] / df['rmse']
                    print("Calculated 'ratio' as spread_plus_oerr / rmse.")

            agg = Aggregation(config, df, svars)
            df = agg.run()
            print(f"DataFrame shape after aggregation: {df.shape}")
            print(f"Saving aggregated file to {config.output_agg_file}.")
            rs.save_dataframe(df, config.output_agg_file)

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
    elif config.plot_type == "roc":
        plt = Roc(config)
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

    from vcast.processing import process_in_parallel
    from vcast.preprocess import Preprocessor
    from vcast.io import OutputFileHandler

    if Preprocessor is None or process_in_parallel is None:
        print(Fore.RED + "Statistical analysis requires the 'processing' extras. Use: pip install vcast[all]" + Style.RESET_ALL)
        sys.exit(1)

    print(f"Running statistical analysis...")

    config = Preprocessor.validate_config(config,"stat")

    output = OutputFileHandler(config)
            
    process_in_parallel(output.config, output, test)

    output.close_output_file()

    sys.exit(0)

def handle_aggregation(config):

    print(f"Running aggregation...")

    agg = Aggregation(config)

    agg.run()

    agg.save_output()    

    sys.exit(0)

def handle_statistical_significance(config):
    
    from vcast.processing import StatiscalSignificance

    if StatiscalSignificance is None:
        print(Fore.RED + "Statistical significance requires the 'processing' extras. Use: pip install vcast[all]" + Style.RESET_ALL)
        sys.exit(1)

    print(f"Running statistical significance...")

    StatiscalSignificance(config)

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
    if action in ["convert", "plot", "stats", "agg", "sig"]:
        config = ConfigLoader(args.file_path)

        if action == "convert":        
            handle_conversion(config)
        elif action == "plot":
            handle_plotting(config)
        elif action == "stats":
            handle_statistical_analysis(config, args.test_mode)
        elif action == "agg":
            handle_aggregation(config)
        elif action == "sig":
            handle_statistical_significance(config)
        else:
            print(Fore.RED + f"Unsupported action type: {action}" + Style.RESET_ALL)
            sys.exit(1)

if __name__ == "__main__":
    main()
